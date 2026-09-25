import json
from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from src.prompts.report_templates import AUDIT_REPORT_SYSTEM_PROMPT


class RedactorAgent:
    def __init__(self, model_name: str = "models/gemini-3.5-flash-lite", temperature: float = 0.2):
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature
        )

    def generate_report(self, audit_results: Dict[str, Any]) -> str:
        json_data = json.dumps(audit_results, indent=2, ensure_ascii=False)

        prompt = f"""
            {AUDIT_REPORT_SYSTEM_PROMPT}

            ### DADOS BRUTOS DA AUDITORIA:
            ```json
            {json_data}
            ```
        """
        response = self.llm.invoke(prompt)

        # 1. Extração do conteúdo bruto
        if isinstance(response.content, str):
            raw_text = response.content
        elif isinstance(response.content, list):
            raw_text = "".join([str(part) for part in response.content])
        else:
            raw_text = str(response.content)

        clean_text = raw_text.replace("\\n", "\n").replace("\\t", "\t")

        return clean_text
