from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage,AIMessage,SystemMessage
from loguru import logger
from config import OLLAMA_MODEL,OLLAMA_BASE_URL,ASSISTANT_NAME

SYSTEM_PROMPT = f"""You are {ASSISTANT_NAME}, a smart and helpful personal AI assistant 
running locally on the user's Windows 11 laptop. You help with everyday tasks like 
managing files, editing documents, writing code, and answering questions.

Rules:
- Be concise and clear. Don't over-explain unless asked.
- If you don't know something, say so honestly.
- If you have doubt on something, ask appropriate question and clear the doubt.
- You are running 100% locally — no internet, full privacy.
- When the user asks you to do something on their computer, confirm what you will do 
  before doing it.
"""

class LLMCore:

    def __init__(self):
        logger.info(f"Connecting to OLLAMA Model {OLLAMA_MODEL}")
        try:
            self.llm = ChatOllama(model=OLLAMA_MODEL,base_url=OLLAMA_BASE_URL,temperature=0.7)
            logger.success(f"Successfully connected to OLLAMA Model {OLLAMA_MODEL}")
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            raise
    
    def chat(self,user_input,history):
        try:
            messages = [SystemMessage(content=SYSTEM_PROMPT)]
            for msg in history:
                if msg["role"]=="user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"]=="agent":
                    messages.append(AIMessage(content=msg["content"]))
            messages.append(HumanMessage(content=user_input))

            logger.debug(f"Sending to Llama: {user_input}")
            response = self.llm.invoke(messages)
            reply = response.content

            logger.debug(f"Llama replied: {reply[:80]}...")
            return reply
        except Exception as e:
            logger.error(f"LLM error: {e}")
            return f"Sorry, I ran into an error: {e}"
