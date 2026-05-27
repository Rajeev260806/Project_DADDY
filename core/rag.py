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
            extracted = text.extract_text()
            if extracted:
                cont+=extracted + "\n"
        return cont
    
    def read_docx(self, path: Path) -> str:
        doc  = Document(str(path))
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    
    def read_document(self, path: Path) -> str:
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
        
    def chunk_text(self,text:str,source:str)->list[dict]:
        start = 0
        chunks = []
        while start<len(text):
            end = start + CHUNK_SIZE
            chunk = text[start:end]

            if chunk:
                chunks.append({"text":chunk,"source":source})
            start+=CHUNK_SIZE-CHUNK_OVERLAY
        return chunks
    
    def make_id(self, source: str, chunk_index: int) -> str:
        raw = f"{source}_{chunk_index}"
        return hashlib.md5(raw.encode()).hexdigest()
    
    def index_document(self, path:Path)->int:
        if not RAW_DIR_LOC.exists():
            return "Knowledge folder not found. Please create knowledge/raw_docs/ and add files."
        text = self.read_document(path)
        if not text.strip():
            return 0
        chunks = self.chunk_text(text,path.name)
        ids        = []
        texts      = []
        embeddings = []
        metadatas  = []

        for i, chunk in enumerate(chunks):
            chunk_id = self.make_id(path.name, i)
            check_exist = self.collection.get(ids=[chunk_id])
            if check_exist["ids"]:
                continue

            embedding = self.embedder.encode(chunk["text"]).tolist()
            ids.append(chunk_id)
            texts.append(chunk["text"])
            embeddings.append(embedding)
            metadatas.append({"source": chunk["source"], "chunk_index": i})

        if ids:
            self.collection.add(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas
            )
            logger.success(f"  Added {len(ids)} new chunk(s) from {path.name}")
        else:
            logger.info(f"  {path.name} already fully indexed — skipped.")
        return len(ids)
    
    def index_all(self) -> str:
        supported = [".txt", ".md", ".pdf", ".docx"]
        files     = [
            f for f in RAW_DIR_LOC.iterdir()
            if f.is_file() and f.suffix.lower() in supported
        ]

        if not files:
            return "No documents found in knowledge/raw_docs/. Add .txt, .pdf or .docx files."

        total_chunks = 0
        indexed_files = []
        for file in files:
            count = self.index_document(file)
            total_chunks  += count
            indexed_files.append(file.name)

        return (
            f"Indexed {len(indexed_files)} document(s): "
            f"{', '.join(indexed_files)}. "
            f"Total chunks stored: {self.collection.count()}."
        )
    
    def retrieve(self,question: str,top_k: int = TOP_K)->list[dict]:
        if self.collection.count() == 0:
            return []
        question_embedding = self.embedder.encode(question).tolist()
        results = self.collection.query(
            query_embeddings=[question_embedding],
            n_results=min(top_k, self.collection.count()),
            include=["documents", "metadatas", "distances"]
        )

        chunks = []
        for text, meta, distance in zip(results["documents"][0],results["metadatas"][0],results["distances"][0]):
            if distance<0.8:
                chunks.append({"text": text,"source": meta["source"],"distance": round(distance, 3)})
        return chunks
    
    def get_status(self) -> str:
        count = self.collection.count()
        if count == 0:
            return "Knowledge base is empty. Add documents to knowledge/raw_docs/ and say 'index my documents'."

        all_data = self.collection.get(include=["metadatas"])
        sources  = list(set([m["source"] for m in all_data["metadatas"]]))

        return (
            f"Knowledge base has {count} chunk(s) from "
            f"{len(sources)} document(s): {', '.join(sources)}"
        )

    def clear(self) -> str:
        self.client.delete_collection(COLLECTION_NAME)
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
        logger.success("Knowledge base cleared.")
        return "Knowledge base cleared. All indexed documents removed."
        