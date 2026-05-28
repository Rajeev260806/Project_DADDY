from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage,AIMessage,SystemMessage
from loguru import logger
from config import OLLAMA_MODEL,OLLAMA_BASE_URL,ASSISTANT_NAME

SYSTEM_PROMPT = """You are {name}, a smart and helpful personal AI assistant
running locally on the user's Windows 11 laptop. You help with everyday tasks like
managing files, editing documents, writing code, and answering questions.

Rules:
- Be concise and clear. Don't over-explain unless asked.
- If you don't know something, say so honestly.
- If you have doubt on something, ask an appropriate question.
- You are running 100% locally — no internet, full privacy.
- When the user asks you to do something on their computer, confirm before doing it.
- Use the memory context below to personalise your responses.
- If the user has a preferred name, use it.
- If the user prefers concise replies, keep answers short.
- If there are pending tasks, mention them only when relevant.

{memory_context}
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
    
    def chat(self,user_input,history,memory_context):
        try:
            new_sys_prompt = SYSTEM_PROMPT.format(
                name=ASSISTANT_NAME,
                memory_context=memory_context if memory_context
                               else "No previous memory available."
            )
            messages = [SystemMessage(content=new_sys_prompt)]
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
