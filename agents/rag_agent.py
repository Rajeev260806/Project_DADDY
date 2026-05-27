import json
from loguru import logger
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from agents.base_agent import BaseAgent
from core.rag import RAGEngine
from config import OLLAMA_MODEL, OLLAMA_BASE_URL

RAG_AGENT_PROMPT = """You are a knowledge base command parser.
The user will give a plain English command about their personal knowledge base.
Respond ONLY with a JSON object — no explanation, no markdown, no extra text.

Supported actions:

1. Answer a question from documents:
{"action":"answer","question":"what is the main topic of my notes"}

2. Index all documents in knowledge folder:
{"action":"index"}

3. Summarize a specific document by name:
{"action":"summarize_doc","filename":"my_notes.txt"}

4. Search for a specific topic across all documents:
{"action":"search","query":"machine learning"}

5. Check knowledge base status:
{"action":"status"}

6. Clear the entire knowledge base:
{"action":"clear"}

Question patterns that map to answer:
- "what does my document say about X"    → answer
- "according to my notes, what is X"     → answer
- "find information about X in my files" → answer
- "what did I write about X"             → answer
- "tell me about X from my documents"    → answer

Rules:
- Respond ONLY with JSON. Nothing else.
- question and query fields should be the core topic — clean and concise
"""

ANSWER_PROMPT = """You are Nova, a helpful personal AI assistant.
Answer the user's question using ONLY the context provided below from their personal documents.

Rules:
- Answer only from the provided context — do not use outside knowledge
- If the context doesn't contain enough information, say so honestly
- Always mention which document the information came from
- Be concise and clear
- If multiple documents have relevant info, combine them naturally

Context from documents:
{context}

User question: {question}
"""

class RAGAgent(BaseAgent):
    def __init__(self, rag_engine:RAGEngine):
        super().__init__("RAGAgent")
        self.rag = rag_engine
        self.llm = ChatOllama(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=0.3
        )

    def parse_command(self, command: str) -> dict:
        messages = [
            SystemMessage(content=RAG_AGENT_PROMPT),
            HumanMessage(content=command)
        ]
        response = self.llm.invoke(messages)
        raw = response.content.strip()
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1])
        return json.loads(raw)
    
    def build_context(self, chunks: list[dict]) -> str:
        if not chunks:
            return "No relevant content found in your documents."
        parts = []
        for i, chunk in enumerate(chunks, 1):
            parts.append(
                f"[Source: {chunk['source']} | Chunk {i}]\n{chunk['text']}"
            )
        return "\n\n---\n\n".join(parts)
    
    def answer(self, data: dict) -> str:
        question = data.get("question", "")
        if not question:
            return "Please provide a question to answer."

        chunks = self.rag.retrieve(question)

        if not chunks:
            return (
                "I couldn't find relevant information in your documents. "
                "Make sure your documents are indexed — say 'index my documents' first."
            )

        context = self.build_context(chunks)
        prompt  = ANSWER_PROMPT.format(context=context, question=question)

        response = self.llm.invoke([HumanMessage(content=prompt)])
        return response.content
    
    def index(self, data: dict) -> str:
        logger.info("Indexing all documents...")
        result = self.rag.index_all()
        return result
    
    def summarize_doc(self, data: dict) -> str:
        filename = data.get("filename", "")
        if not filename:
            return "Please specify which document to summarize."

        all_data = self.rag.collection.get(include=["documents", "metadatas"])

        doc_chunks = [
            doc for doc, meta in zip(
                all_data["documents"], all_data["metadatas"]
            )
            if meta["source"].lower() == filename.lower()
        ]

        if not doc_chunks:
            return (
                f"'{filename}' not found in knowledge base. "
                f"Make sure it's in knowledge/raw_docs/ and indexed."
            )

        full_text = "\n\n".join(doc_chunks)
        prompt    = (
            f"Summarize this document clearly and concisely in 5 to 7 sentences. "
            f"Capture the key points:\n\n{full_text[:5000]}"
        )
        response = self.llm.invoke([HumanMessage(content=prompt)])
        return f"Summary of '{filename}':\n{response.content}"