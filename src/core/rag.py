import chromadb
from sentence_transformers import SentenceTransformer
import os

class RAGEngine:
    def __init__(self, db_path=None):
        if db_path is None:
            # Default to the data/vector_db folder relative to project root
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            db_path = os.path.join(base_dir, "data", "vector_db")
        
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection("project_context")

    def chunk_text(self, text, chunk_size=1000, overlap=100):
        chunks = []
        for i in range(0, len(text), chunk_size - overlap):
            chunks.append(text[i:i + chunk_size])
        return chunks

    def index_document(self, text, doc_id, metadata=None):
        chunks = self.chunk_text(text)
        embeddings = self.model.encode(chunks).tolist()
        
        ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [metadata or {"source": doc_id}] * len(chunks)
        
        self.collection.add(
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )

    def query(self, query, n_results=5):
        query_embedding = self.model.encode([query]).tolist()
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=n_results
        )
        return "\n---\n".join(results["documents"][0]) if results["documents"] and results["documents"][0] else ""
