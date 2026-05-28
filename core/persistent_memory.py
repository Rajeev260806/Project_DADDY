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
        self.data["conversations"].append({
            "role": role, 'content': content, 'timestamp' : datetime.now().isoformat()
        })
        if len(self.data["conversations"])>SUMMARY_THRESHOLD:
            self.summarizeConversation()
        self.save()

    def summarizeConversation(self):
        old_turns = self.data["conversations"][:-MAX_RECENT_TURNS]
        recent_turns = self.data["conversations"][-MAX_RECENT_TURNS:]

        old_text = "\n".join([
            f"{t['role'].upper()}: {t['content']}"
            for t in old_turns
        ])
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

    def getRecentConversations(self, n: int = MAX_RECENT_TURNS) -> list[dict]:
        return self.data["conversations"][-n:]
    
    def addPreference(self,key:str,value:str):
        for pref in self.data["preferences"]:
            if pref["key"].lower()==key.lower():
                pref["value"] = value
                pref["timestamp"] = datetime.now().isoformat()
                self.save()
                logger.info(f"Updated preference: {key} = {value}")
                return

        self.data["preferences"].append({
            "key":key,"value":value,"timestamp": datetime.now().isoformat()
        })
        self.save()
        logger.info(f"Saved preference: {key} = {value}")

    def getEveryPreferences(self):
        return self.data["preferences"]
    
    def getPreference(self,key:str):
        for pref in self.data["preferences"]:
            if pref["key"].lower()==key.lower():
                return pref["value"]
        return ""
    
    def addTask(self,task:str):
        self.data["tasks"].append({
            "task":      task,
            "status":    "pending",
            "timestamp": datetime.now().isoformat()
        })
        self.save()
        logger.info(f"Task Added: {task}")

    def completeTask(self,task_keyword:str)->str:
        for task in self.data["tasks"]:
            if task_keyword.lower() in task["task"].lower() and task["status"] == "pending":
                task["status"] = "completed"
                self.save()
                return f"Task marked as completed: '{task['task']}'"
        return f"No pending task found matching '{task_keyword}'."
    
    def getPendingTasks(self) -> list[dict]:
        return [t for t in self.data["tasks"] if t["status"] == "pending"]

    def getAllTasks(self) -> list[dict]:
        return self.data["tasks"]
    
    def getSummary(self) -> str:
        return self.data["summary"]

    def buildContextBlock(self) -> str:
        parts = []
        if self.data["summary"]:
            parts.append(
                f"SUMMARY OF PAST CONVERSATIONS:\n{self.data['summary']}"
            )
        recent = self.getRecentConversations(n=10)
        if recent:
            conv_text = "\n".join([
                f"{t['role'].upper()}: {t['content'][:200]}"
                for t in recent
            ])
            parts.append(f"RECENT CONVERSATION HISTORY:\n{conv_text}")

        prefs = self.data["preferences"]
        if prefs:
            pref_text = "\n".join([
                f"- {p['key']}: {p['value']}"
                for p in prefs
            ])
            parts.append(f"USER PREFERENCES:\n{pref_text}")

        pending = self.getPendingTasks()
        if pending:
            task_text = "\n".join([
                f"- {t['task']} (since {t['timestamp'][:10]})"
                for t in pending
            ])
            parts.append(f"PENDING TASKS:\n{task_text}")

        if not parts:
            return ""

        return "\n\n".join(parts)

    def clearConversations(self) -> str:
        self.data["conversations"] = []
        self.data["summary"]       = ""
        self.save()
        return "Conversation history cleared. Preferences and tasks kept."

    def clearAll(self) -> str:
        self.data = self.default_data()
        self.save()
        return "All memory cleared — conversations, preferences and tasks."    
    
    def getStatus(self) -> str:
        conv_count  = len(self.data["conversations"])
        pref_count  = len(self.data["preferences"])
        task_count  = len(self.data["tasks"])
        pending     = len(self.getPendingTasks())
        has_summary = "Yes" if self.data["summary"] else "No"

        return (
            f"Memory status:\n"
            f"  Conversations  : {conv_count} recent turn(s)\n"
            f"  Old summary    : {has_summary}\n"
            f"  Preferences    : {pref_count}\n"
            f"  Tasks (total)  : {task_count} "
            f"({pending} pending)"
        )

    def extract_and_save_preference(self, user_text: str):
        text  = user_text.lower()
        prefs = []
        if "speak slower" in text or "too fast" in text:
            prefs.append(("speech_speed", "slow"))
        elif "speak faster" in text or "too slow" in text:
            prefs.append(("speech_speed", "fast"))

        if "be more detailed" in text or "explain more" in text:
            prefs.append(("response_style", "detailed"))
        elif "keep it short" in text or "be brief" in text or "be concise" in text:
            prefs.append(("response_style", "concise"))

        if "call me " in text:
            name = text.split("call me ")[-1].strip().split()[0]
            prefs.append(("user_name", name))

        if "reply in malayalam" in text or "speak in malayalam" in text:
            prefs.append(("language", "malayalam"))
        elif "reply in english" in text or "speak in english" in text:
            prefs.append(("language", "english"))

        for key, value in prefs:
            self.addPreference(key, value)

    def extract_and_save_task(self, user_text: str):
        text = user_text.lower().strip()
        task_triggers = [
            "remind me to",
            "don't forget to",
            "remember to",
            "make sure to",
            "i need to",
            "track this:",
            "add to my tasks:",
            "note this:",
        ]
        for trigger in task_triggers:
            if text.startswith(trigger):
                task = user_text[len(trigger):].strip()
                if task:
                    self.addTask(task)
                return