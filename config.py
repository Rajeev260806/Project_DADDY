from dotenv import load_dotenv
import os

load_dotenv()
OLLAMA_MODEL=os.getenv("OLLAMA_MODEL","llama3.2")
OLLAMA_BASE_URL=os.getenv("OLLAMA_BASE_URL","http://localhost:11434")
ASSISTANT_NAME=os.getenv("ASSISTANT_NAME","DADDY")

MAX_HISTORY = 10