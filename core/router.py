from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger
from config import OLLAMA_MODEL, OLLAMA_BASE_URL

ROUTER_PROMPT = """You are a command router for a personal AI assistant.
Read the user's command and decide which agent should handle it.

Reply with ONLY one of these exact words — nothing else:

filesystem  → user wants to create, delete, move, rename, list, find, read or write files/folders
general     → everything else (questions, conversation, calculations, definitions, etc.)

Examples:
"create a folder called Projects on Desktop"  → filesystem
"move report.pdf from Downloads to Documents" → filesystem
"find all PDF files in Downloads"             → filesystem
"what is machine learning"                    → general
"tell me a joke"                              → general
"what is 25 times 48"                         → general
"read the notes.txt file on my Desktop"       → filesystem
"rename my resume to resume_final"            → filesystem
"""

class Router:
    def __init__(self):
        self.llm = ChatOllama(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=0,     
        )
        logger.info("Router initialised.")

    def route(self,command:str)->str:
        messages = [
            SystemMessage(content=ROUTER_PROMPT),
            HumanMessage(content=command)
        ]
        response = self.llm.invoke(messages)
        decision = response.content.strip().lower()

        if decision not in ["filesystem","general"]:
            logger.warning(f"Router got unexpected decision: '{decision}' — defaulting to general")
            decision = "general"

        logger.info(f"Router decision for '{command[:50]}': {decision}")
        return decision