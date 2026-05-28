import json
from datetime import datetime
from pathlib import Path
from loguru import logger
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from config import OLLAMA_MODEL, OLLAMA_BASE_URL

MEMORY_FILE = Path("memory/persistent_memory.json")
MAX_RECENT_TURNS = 20
SUMMARY_THRESHOLD = 30

class PersistentMemory:
    def __init__(self):    
        MEMORY_FILE.parent.mkdir(parents=True,exist_ok=True)
        self.llm = ChatOllama(
                model=OLLAMA_MODEL,
                base_url=OLLAMA_BASE_URL,
                temperature=0.3,
        )
        self.data = self.load()
        logger.success(
            f"Persistent memory loaded — "
            f"{len(self.data['conversations'])} conversation(s), "
            f"{len(self.data['tasks'])} task(s), "
            f"{len(self.data['preferences'])} preference(s)."
        )

    def default_data(self) -> dict:
        return {
            "conversations": [],   
            "summary":       "",   
            "preferences":   [],   
            "tasks":         [],   
        }
