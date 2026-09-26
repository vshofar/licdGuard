# 🛡️ Licit-Guard

**Licit-Guard** é um pipeline automatizado de detecção de fraudes e conluios em licitações públicas brasileiras. A solução utiliza um **Knowledge Graph (Neo4j)** para identificar relacionamentos ocultos entre licitantes (sócios em comum, endereços compartilhados e propostas de cobertura) e alavanca **LLMs (Google Gemini via LangChain)** para gerar pareceres técnicos forenses em linguagem natural.

> ⚠️ **Atenção:** Este é um projeto de estudos em processo de validação. Não deve ser utilizado em ambiente de produção ou para tomada de decisões reais em processos licitatórios.

---

## 🏗️ Arquitetura do Sistema

O projeto é estruturado em agentes modulares que se comunicam via contratos de dados estritos (`Pydantic`):

### 📦 Estrutura de Diretórios

```
licdGuard/
├── config.py                 # Centralização de variáveis de ambiente
├── src/
│   ├── agents/
│   │   ├── ingestor_agent.py # Ingestão de dados no Knowledge Graph
│   │   ├── auditor_agent.py  # Análise de fraude e cálculo de risco
│   │   └── redactor_agent.py # Geração de relatórios com Gemini
│   ├── database/
│   │   └── neo4j_client.py   # Cliente Neo4j
│   ├── models/
│   │   └── ingestor_schemas.py # Schemas Pydantic para validação
│   ├── prompts/
│   │   └── report_templates.py # Prompts para LLM
│   ├── services/
│   │   ├── brasil_api_service.py # Integração com BrasilAPI (dados de CNPJ)
│   │   └── pncp_api_service.py   # Integração com PNCP API (licitações)
│   └── main.py               # Pipeline principal
├── tests/
│   ├── pipeline_test.py      # Testes end-to-end
│   ├── agents/               # Testes unitários dos agentes
│   └── services/             # Testes unitários dos serviços de API
└── requirements.txt
```

### 🤖 Agentes

- **IngestorAgent**: Responsável por persistir empresas, sócios e licitações no Neo4j
- **AuditorAgent**: Executa queries Cypher para detectar padrões suspeitos:
  - Sócios em comum entre licitantes
  - Endereços compartilhados
  - Propostas de cobertura (valores acima de 20% do estimado)
- **RedactorAgent**: Utiliza Google Gemini para gerar relatórios forenses em português

### 🔌 Serviços de Integração

- **BrasilAPIService**: Integração com BrasilAPI para consulta de dados cadastrais de CNPJ
  - Busca razão social, endereço e quadro de sócios (QSA)
  - Retorna dados estruturados via Pydantic schemas
- **PNCPApiService**: Integração com PNCP API para consulta de licitações públicas
  - Busca dados de licitações por órgão, ano e sequencial
  - Recupera propostas de fornecedores associadas

---

## 🛠️ Tech Stack

* **Linguagem:** Python 3.11+
* **Graph Database:** Neo4j (Cypher Query Language)
* **LLM Orchestration:** LangChain & `langchain-google-genai` (Google Gemini)
* **LLM Provider:** GROQ & Google Gemini
* **HTTP Client:** httpx
* **Data Validation:** Pydantic v2
* **Testing Infrastructure:** Pytest, Testcontainers (Neo4j Docker Container efêmero) & pytest-httpx
* **Environment Management:** python-dotenv

---

## 🚀 Como Executar o Projeto

### 1. Pré-requisitos
* Python 3.11+ instalado
* Docker Desktop rodando (necessário para o Neo4j via Testcontainers)
* Chaves de API:
  - `GROQ_API_KEY`
  - `GEMINI_API_KEY`

### 2. Configuração do Ambiente

Clone o repositório e instale as dependências:

```bash
python -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto baseado no `.env.example`:

```bash
cp .env.example .env
```

Edite o arquivo `.env` com suas credenciais:

```env
GROQ_API_KEY=seu_groq_api_key_aqui
GEMINI_API_KEY=seu_gemini_api_key_aqui
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=sua_senha_neo4j_aqui
```

### 4. Execução do Pipeline

Execute o pipeline principal:

```bash
python src/main.py
```

Para auditar uma licitação específica:

```bash
python src/main.py PNCP-FRAUDE-01
```

### 5. Execução dos Testes

Os testes utilizam Testcontainers para criar uma instância Neo4j efêmera:

```bash
pytest
```

Para executar com verbose:

```bash
pytest -v
```

---

## 📊 Cálculo de Score de Risco

O sistema calcula um score de risco (0-100) baseado em:

| Alerta | Peso |
|--------|------|
| Sócios em comum | +40 pontos |
| Endereços compartilhados | +30 pontos |
| Propostas de cobertura | +20 pontos |

---

## 🧪 Testes

O projeto inclui testes automatizados que:
- Inicializam um container Neo4j temporário via Testcontainers
- Populam dados de teste
- Executam o pipeline completo
- Validam os resultados da auditoria
- Testam integrações com APIs externas (BrasilAPI e PNCP) usando pytest-httpx para mocking de requisições HTTP