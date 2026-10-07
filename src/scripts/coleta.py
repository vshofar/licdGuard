import requests
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# URL do endpoint oficial
API_URL = "https://dadosabertos.compras.gov.br/modulo-contratacoes/3_consultarResultadoItensContratacoes_PNCP_14133"

# Arquivos de saída
ARQUIVO_RAW = "ids_coletados_raw.txt"
ARQUIVO_FINAL = "ids_unicos_consolidados.txt"

# Mecanismos de sincronização entre Threads
file_lock = Lock()
counter_lock = Lock()
total_ids_coletados = 0


def extrair_ids_de_payload(payload: dict) -> list:
    """Extrai a lista de idCompra contida no objeto 'resultado' da API."""
    itens = payload.get("resultado", [])
    ids_pagina = []

    for item in itens:
        id_compra = (
                item.get("idCompra") or
                item.get("idContratacao") or
                item.get("numeroControlePNCP") or
                item.get("id")
        )
        if id_compra:
            ids_pagina.append(str(id_compra).strip())

    return ids_pagina


def salvar_ids_em_arquivo(ids: list):
    """Escreve os IDs coletados diretamente no arquivo bruto de forma Thread-safe."""
    global total_ids_coletados
    if not ids:
        return

    # Trava para escrita concorrente no arquivo
    with file_lock:
        with open(ARQUIVO_RAW, "a", encoding="utf-8") as f:
            for id_c in ids:
                f.write(f"{id_c}\n")

    # Trava para atualização atômica do contador
    with counter_lock:
        total_ids_coletados += len(ids)


def consultar_pagina_worker(pagina: int, params_base: dict, max_retries: int = 5):
    """
    Worker executado por cada thread para consultar uma página específica.
    Implementa retentativa (retry) em caso de HTTP 409 ou 429.
    """
    params = params_base.copy()
    params["pagina"] = pagina
    headers = {"accept": "application/json"}

    tentativa = 1
    sucesso = False

    while tentativa <= max_retries and not sucesso:
        try:
            response = requests.get(API_URL, params=params, headers=headers, timeout=20)

            if response.status_code == 200:
                payload = response.json()
                ids = extrair_ids_de_payload(payload)
                salvar_ids_em_arquivo(ids)

                with counter_lock:
                    coletados = total_ids_coletados

                print(f"✅ [Pág {pagina}] Sucesso | +{len(ids)} IDs | 📈 Acumulado Bruto: {coletados} IDs")
                sucesso = True

            elif response.status_code in (409, 429):
                # Tratamento para conflito (409) ou estouro de limite de taxa (429)
                print(
                    f"⚠️ [Pág {pagina}] Recebeu HTTP {response.status_code} (Tentativa {tentativa}/{max_retries}). Aguardando 2s antes de tentar novamente...")
                time.sleep(2)
                tentativa += 1

            elif response.status_code == 204:
                print(f"ℹ️ [Pág {pagina}] HTTP 204 (Sem Conteúdo).")
                sucesso = True

            else:
                print(f"❌ [Pág {pagina}] Falha HTTP {response.status_code}. Prosseguindo sem tentar novamente...")
                break

        except Exception as e:
            print(f"❌ [Pág {pagina}] Exceção na requisição ({e}). Tentativa {tentativa}/{max_retries}...")
            time.sleep(2)
            tentativa += 1

    if not sucesso and tentativa > max_retries:
        print(f"🛑 [Pág {pagina}] Excedeu o limite máximo de {max_retries} tentativas. Página ignorada.")


def executar_coleta_paralela(params_config: dict, max_workers: int = 10):
    """Gerencia a coleta paralela em 3 fases: Inicial, Concorrente e Consolidação."""
    global total_ids_coletados
    total_ids_coletados = 0

    # Limpa o arquivo temporário anterior, se existir
    if os.path.exists(ARQUIVO_RAW):
        os.remove(ARQUIVO_RAW)

    # -------------------------------------------------------------
    # 1. FASE INICIAL: Consulta a Página 1 e exibe o resumo
    # -------------------------------------------------------------
    print("🚀 [Fase 1] Mapeando total de páginas e registros na página 1...")

    headers = {"accept": "application/json"}
    params_p1 = params_config.copy()
    params_p1["pagina"] = 1

    try:
        resp = requests.get(API_URL, params=params_p1, headers=headers, timeout=30)
        if resp.status_code != 200:
            print(f"❌ Falha ao realizar chamada inicial. Status HTTP: {resp.status_code}")
            return

        payload_p1 = resp.json()
        total_paginas = payload_p1.get("totalPaginas", 1)
        total_registros = payload_p1.get("totalRegistros", 0)

        # Processa os registros da página 1
        ids_p1 = extrair_ids_de_payload(payload_p1)
        salvar_ids_em_arquivo(ids_p1)

        paginas_restantes = max(0, total_paginas - 1)

        print("\n" + "=" * 60)
        print("📊 RESUMO DA PRIMEIRA CONSULTA")
        print("=" * 60)
        print(f"• Total de registros estimados: {total_registros}")
        print(f"• Total de páginas identificadas: {total_paginas}")
        print(f"• Registros coletados na Pág 1: {len(ids_p1)}")
        print(f"• Páginas que serão coletadas na Fase 2: {paginas_restantes} (Páginas 2 a {total_paginas})")
        print("=" * 60 + "\n")

        # Pausa e aguarda a confirmação do usuário
        input("Press [ENTER] para iniciar a coleta paralela das páginas restantes...")
        print("\n")

    except Exception as e:
        print(f"❌ Erro na chamada inicial: {e}")
        return

    # -------------------------------------------------------------
    # 2. FASE PARALELA: Distribui as páginas 2..N entre as Threads
    # -------------------------------------------------------------
    if total_paginas > 1:
        paginas_para_coletar = list(range(2, total_paginas + 1))
        print(f"⚙️ [Fase 2] Executando {max_workers} Threads para processar {len(paginas_para_coletar)} páginas...\n")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(consultar_pagina_worker, pag, params_config)
                for pag in paginas_para_coletar
            ]

            # Aguarda a conclusão de todas as threads
            for _ in as_completed(futures):
                pass
    else:
        print("ℹ️ Não há mais páginas pendentes para coleta.")

    # -------------------------------------------------------------
    # 3. FASE DE CONSOLIDAÇÃO: Deduplicação e Arquivo Final
    # -------------------------------------------------------------
    print("\n🧹 [Fase 3] Removendo duplicidades e gerando arquivo consolidado...")

    ids_unicos = set()
    total_linhas_raw = 0

    if os.path.exists(ARQUIVO_RAW):
        with open(ARQUIVO_RAW, "r", encoding="utf-8") as f:
            for linha in f:
                linha_limpa = linha.strip()
                if linha_limpa:
                    total_linhas_raw += 1
                    ids_unicos.add(linha_limpa)

        lista_ordenada = sorted(list(ids_unicos))
        with open(ARQUIVO_FINAL, "w", encoding="utf-8") as f:
            for id_c in lista_ordenada:
                f.write(f"{id_c}\n")

        print("\n" + "=" * 60)
        print("📊 RESUMO FINAL DA COLETA")
        print("=" * 60)
        print(f"• Registros coletados (bruto com duplicatas): {total_linhas_raw}")
        print(f"• IDs de compra ÚNICOS identificados: {len(ids_unicos)}")
        print(f"• Arquivo bruto: {ARQUIVO_RAW}")
        print(f"• Arquivo final consolidado: {ARQUIVO_FINAL}")
        print("=" * 60)


if __name__ == "__main__":
    PARAMETROS_INICIAIS = {
        "tamanhoPagina": 100,
        "dataResultadoPncpInicial": "2024-11-01",
        "dataResultadoPncpFinal": "2024-11-30"
    }

    executar_coleta_paralela(PARAMETROS_INICIAIS, max_workers=10)
