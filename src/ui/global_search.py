import customtkinter as ctk
import os
import re

class GlobalSearch(ctk.CTkFrame):
    def __init__(self, master, ide_ref, **kwargs):
        super().__init__(master, **kwargs)
        self.ide = ide_ref
        
        # Header
        self.header_label = ctk.CTkLabel(self, text="SEARCH", font=ctk.CTkFont(size=13, weight="bold"), text_color="#bbbbbb")
        self.header_label.pack(pady=(10, 5), padx=20, anchor="w")
        
        # Search Box
        self.search_entry = ctk.CTkEntry(self, placeholder_text="Search text...", height=30)
        self.search_entry.pack(fill="x", padx=10, pady=2)
        self.search_entry.bind("<Return>", lambda e: self.perform_search())
        
        # Replace Box (Optional)
        self.replace_entry = ctk.CTkEntry(self, placeholder_text="Replace with...", height=30)
        self.replace_entry.pack(fill="x", padx=10, pady=2)
        
        # Search Options
        self.options_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.options_frame.pack(fill="x", padx=10, pady=2)
        
        self.match_case = ctk.CTkCheckBox(self.options_frame, text="Match Case", font=ctk.CTkFont(size=11), width=80)
        self.match_case.pack(side="left")
        
        self.whole_word = ctk.CTkCheckBox(self.options_frame, text="Whole Word", font=ctk.CTkFont(size=11), width=80)
        self.whole_word.pack(side="left", padx=5)

        self.search_btn = ctk.CTkButton(self, text="Search All Files", height=28, command=self.perform_search)
        self.search_btn.pack(fill="x", padx=10, pady=10)

        # Results Area (Scrollable)
        self.results_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.results_frame.pack(fill="both", expand=True, padx=5, pady=5)

    def perform_search(self):
        """Searches all project files for the query string."""
        query = self.search_entry.get()
        if not query: return
        
        for widget in self.results_frame.winfo_children():
            widget.destroy()
            
        case_sensitive = self.match_case.get()
        whole_word = self.whole_word.get()
        
        pattern = re.escape(query)
        if whole_word:
            pattern = rf"\b{pattern}\b"
        flags = 0 if case_sensitive else re.IGNORECASE
        
        results_count = 0
        project_root = os.getcwd()
        excluded = {".git", "__pycache__", "node_modules", "data", "venv", ".vscode", "vector_db", "dist", "build"}
        extensions = {".py", ".md", ".txt", ".js", ".html", ".css", ".json", ".bat", ".ps1", ".java", ".c", ".cpp"}

        for root, dirs, files in os.walk(project_root):
            dirs[:] = [d for d in dirs if d not in excluded]
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    path = os.path.join(root, file)
                    try:
                        with open(path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.readlines()
                            file_matches = []
                            for i, line in enumerate(content):
                                if re.search(pattern, line, flags):
                                    file_matches.append((i + 1, line.strip()))
                            
                            if file_matches:
                                results_count += len(file_matches)
                                self.add_file_result(path, file_matches)
                    except: pass
        
        self.header_label.configure(text=f"SEARCH: {results_count} results")

    def add_file_result(self, path, matches):
        """Adds a file and its matches to the results view."""
        rel_path = os.path.relpath(path, os.getcwd())
        
        file_btn = ctk.CTkButton(self.results_frame, text=f"📄 {rel_path} ({len(matches)})", 
                                 anchor="w", fg_color="#333333", hover_color="#404040", 
                                 height=26, font=ctk.CTkFont(size=12, weight="bold"))
        file_btn.pack(fill="x", pady=(5, 2))
        
        for line_num, text in matches[:20]: # Limit matches per file
            match_btn = ctk.CTkButton(self.results_frame, text=f"  {line_num}: {text[:50]}...", 
                                      anchor="w", fg_color="transparent", hover_color="#2a2d2e",
                                      height=22, font=ctk.CTkFont(size=11),
                                      command=lambda p=path, l=line_num: self.ide.open_file_at_line(p, l))
            match_btn.pack(fill="x")
