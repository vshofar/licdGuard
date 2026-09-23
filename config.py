import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY não definida no arquivo .env")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY não definida no arquivo .env")
