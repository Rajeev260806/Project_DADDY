from dotenv import load_env
import os

load_env()
OLLAMA_MODEL=os.getenv("OLLAMA_MODEL","llama3.2")
OLLAMA_BASE_URL=os.getenv("OLLAMA_BASE_URL","http://localhost:11434")
ASSISTANT_NAME=os.getenv("ASSISTANT_NAME","Daddy")

MAX_HISTORY = 10