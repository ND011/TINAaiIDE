import os
import sys
import hashlib

# Add project root to path so we can import src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.rag import RAGEngine

def get_file_hash(path):
    hasher = hashlib.md5()
    with open(path, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def run_indexer(directory):
    engine = RAGEngine()
    # CRITICAL: Professional filter for IDE
    excluded = {
        ".git", "__pycache__", "data", "node_modules", "src", 
        "venv", ".vscode", "vector_db", "dist", "build", ".idea"
    }
    extensions = {".py", ".md", ".txt", ".js", ".html", ".css", ".json", ".bat", ".ps1"}

    print(f"🚀 Tina AI: Optimizing Index for {directory}")
    
    # --- PHASE 1: COUNT TOTAL FILES ---
    all_files = []
    for root, dirs, files in os.walk(directory):
        # Prune excluded directories
        dirs[:] = [d for d in dirs if d not in excluded]
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                all_files.append(os.path.join(root, file))

    total_files = len(all_files)
    indexed_count = 0
    
    # --- PHASE 2: INDEX EACH FILE ---
    for path in all_files:
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                if content.strip():
                    indexed_count += 1
                    # Progress reporting for UI capture
                    progress_pct = int((indexed_count / total_files) * 100)
                    print(f"[{indexed_count}/{total_files}] ({progress_pct}%) INDEXING: {os.path.relpath(path, directory)}")
                    
                    # Pass file path to engine for metadata extraction (like extension)
                    engine.index_document(content, path, {"path": path, "filename": os.path.basename(path)})
        except Exception as e:
            print(f" [!] ERROR: {path} - {e}")

    print(f"\n✅ Indexing Complete. Total files: {indexed_count}")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    run_indexer(current_dir)
