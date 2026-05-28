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
    
    def load(self)->dict:
        if MEMORY_FILE.exists():
            try:
                with open(MEMORY_FILE,"r",encoding="utf-8") as f:
                    data = json.load(f)
                    logger.success("Json file loaded successfully!")
                    return data
            except Exception as e:
                logger.error(f"Json file failed to load: {e}")
        return self.default_data()
    
    def save(self):
        try:
            with open(MEMORY_FILE,"w",encoding="utf-8") as f:
                json.dump(self.data,f,indent=2,ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")

    def addConversation(self,role:str,content:str):
        self.data["conversation"].append({
            "role": role, 'content': content, 'timestamp' : datetime.now().isoformat()
        })
        if len(self.data["conversation"])>SUMMARY_THRESHOLD:
            self.summarizeConversation()
        self.save()

    def summarizeConversation(self):
        old_turns = self.data["conversations"][:-MAX_RECENT_TURNS]
        recent_turns = self.data["conversations"][-MAX_RECENT_TURNS:]

        old_text = "\n".join([f"{t["role"].upper()} : {t["content"]}"
            for t in old_turns])
        existing_summary = self.data["summary"]
        if existing_summary:
            prompt = (
                f"You have this existing summary of past conversations:\n"
                f"{existing_summary}\n\n"
                f"Now summarize and merge these additional conversations "
                f"into the existing summary. Keep it concise — max 10 sentences. "
                f"Preserve important facts, preferences, and tasks mentioned:\n\n"
                f"{old_text}"
            )
        else:
            prompt = (
                f"Summarize these conversations concisely in max 10 sentences. "
                f"Preserve important facts, preferences, tasks and context:\n\n"
                f"{old_text}"
            )
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            self.data["summary"]       = response.content.strip()
            self.data["conversations"] = recent_turns
            logger.success("Old conversations summarized and compressed.")
        except Exception as e:
            logger.error(f"Failed to summarize old conversations: {e}")
            