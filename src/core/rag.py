import chromadb
from sentence_transformers import SentenceTransformer
import os
import re

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
        """Standard character-based chunking."""
        chunks = []
        for i in range(0, len(text), chunk_size - overlap):
            chunks.append(text[i:i + chunk_size])
        return chunks

    def chunk_code(self, text, filename, chunk_size=1000):
        """Intelligent structural chunking for code files."""
        ext = os.path.splitext(filename)[1].lower()
        
        if ext == ".py":
            # Split by class and function definitions
            # We use positive lookahead to keep the 'class ' or 'def ' in the chunk
            pattern = r'(?m)^(?=class |def )'
            parts = re.split(pattern, text)
            
            # Combine small parts into bigger chunks
            chunks = []
            current_chunk = ""
            for part in parts:
                if len(current_chunk) + len(part) < chunk_size:
                    current_chunk += part
                else:
                    if current_chunk: chunks.append(current_chunk)
                    current_chunk = part
            if current_chunk: chunks.append(current_chunk)
            return chunks
        
        elif ext in [".js", ".ts", ".java", ".cpp", ".c", ".cs"]:
            # Split by common structural markers like top-level blocks or functions
            pattern = r'(?m)^(?=function |export |class |public |private |static |const )'
            parts = re.split(pattern, text)
            chunks = []
            current_chunk = ""
            for part in parts:
                if len(current_chunk) + len(part) < chunk_size:
                    current_chunk += part
                else:
                    if current_chunk: chunks.append(current_chunk)
                    current_chunk = part
            if current_chunk: chunks.append(current_chunk)
            return chunks
            
        # Fallback to character-based for other types (markdown, txt, etc.)
        return self.chunk_text(text)

    def index_document(self, text, doc_id, metadata=None):
        """Indexes a document using the best available chunking strategy."""
        filename = metadata.get("filename", doc_id) if metadata else doc_id
        
        # Use structural chunking if possible
        chunks = self.chunk_code(text, filename)
        
        if not chunks: return # Empty or failed

        embeddings = self.model.encode(chunks).tolist()
        
        ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [metadata or {"source": doc_id}] * len(chunks)
        
        # Add to collection
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
