import os
import hashlib
from pathlib import Path
from loguru import logger
from pypdf import PdfReader
from docx import Document
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

RAW_DIR_LOC = Path("knowledge/raw_docs")
VECTOR_LOC = Path("knowledge/vector_store")
EMBED_MODEL = "all-MiniLM-L6-v2"
CHUNK_SIZE = 500
CHUNK_OVERLAY = 50
TOP_K = 5
COLLECTION_NAME = "Daddy_knowledge"

class RAGEngine:

    def __init__(self):
        logger.info("Initialsing RAG")
        self.embedder = SentenceTransformer(EMBED_MODEL)
        logger.success("RAG model loaded successfully")
        VECTOR_LOC.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=str(VECTOR_LOC),
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}   # cosine similarity for text
        )

    def read_text(self,path:Path)->str:
        return path.read_text(encoding="utf-8",errors="ignore")
    
    def read_pdf(self,path:Path)->str:
        file = PdfReader(str(path))
        cont = ""
        for text in file.pages:
            cont+=text + "\n"
        return cont
    
    def read_docx(self, path: Path) -> str:
        doc  = Document(str(path))
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    
    def _read_document(self, path: Path) -> str:
        ext = path.suffix.lower()
        if ext == ".txt" or ext == ".md":
            return self.read_text(path)
        elif ext == ".pdf":
            return self.read_pdf(path)
        elif ext == ".docx":
            return self.read_docx(path)
        else:
            logger.warning(f"Unsupported file type: {path.name} — skipping.")
            return ""