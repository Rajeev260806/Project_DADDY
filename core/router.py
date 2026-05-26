from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger
from config import OLLAMA_MODEL, OLLAMA_BASE_URL

ROUTER_PROMPT = """You are a command router for a personal AI assistant.
Read the user's command and decide which agent should handle it.

Reply with ONLY one of these exact words — nothing else:

filesystem  → create, delete, move, rename, list, find files or folders (NOT Word files)
word        → anything about a .docx or Word document
general     → everything else (questions, conversation, calculations, definitions etc.)

Examples:
"create a folder called Projects on Desktop"          → filesystem
"delete all PDFs in Downloads"                        → filesystem
"find files starting with report in Documents"        → filesystem
"create a new Word document called report"            → word
"summarize my essay.docx on Desktop"                  → word
"add a paragraph to report.docx"                      → word
"count words in my document"                          → word
"replace old with new in report.docx"                 → word
"add a heading called Introduction to my document"    → word
"delete paragraphs containing llama in report.docx"   → word
"what is machine learning"                            → general
"tell me a joke"                                      → general
"what is 25 times 48"                                 → general
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

        if decision not in ["filesystem","general","word"]:
            logger.warning(f"Router got unexpected decision: '{decision}' — defaulting to general")
            decision = "general"

        logger.info(f"Router decision for '{command[:50]}': {decision}")
        return decision