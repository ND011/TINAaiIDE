import customtkinter as ctk
import os
import subprocess

class GitSidebar(ctk.CTkFrame):
    def __init__(self, master, ide_ref, **kwargs):
        super().__init__(master, **kwargs)
        self.ide = ide_ref
        
        # Header
        self.header_label = ctk.CTkLabel(self, text="SOURCE CONTROL", font=ctk.CTkFont(size=13, weight="bold"), text_color="#bbbbbb")
        self.header_label.pack(pady=(10, 5), padx=20, anchor="w")
        
        # Commit Area
        self.commit_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.commit_frame.pack(fill="x", padx=10, pady=10)
        
        self.commit_entry = ctk.CTkEntry(self.commit_frame, placeholder_text="Message (Ctrl+Enter to commit)", height=30)
        self.commit_entry.pack(fill="x", pady=2)
        self.commit_entry.bind("<Control-Return>", lambda e: self.perform_commit())
        
        self.commit_btn = ctk.CTkButton(self.commit_frame, text="Commit", height=28, fg_color="#007acc", command=self.perform_commit)
        self.commit_btn.pack(fill="x", pady=5)

        # Changes Label
        self.changes_label = ctk.CTkLabel(self, text="CHANGES", font=ctk.CTkFont(size=11, weight="bold"), text_color="#858585")
        self.changes_label.pack(anchor="w", padx=10, pady=(10, 0))

        # Results Area (Scrollable)
        self.results_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.results_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.refresh()

    def refresh(self):
        """Checks git status and updates the list."""
        for widget in self.results_frame.winfo_children(): widget.destroy()
        
        if not os.path.exists(os.path.join(os.getcwd(), ".git")):
            lbl = ctk.CTkLabel(self.results_frame, text="Not a git repository", font=ctk.CTkFont(size=12))
            lbl.pack(pady=20)
            return

        try:
            # Get status
            output = subprocess.check_output(["git", "status", "--short"], text=True)
            lines = output.splitlines()
            
            if not lines:
                lbl = ctk.CTkLabel(self.results_frame, text="No changes detected", font=ctk.CTkFont(size=12))
                lbl.pack(pady=20)
                return

            for line in lines:
                if len(line) < 4: continue
                status = line[:2].strip()
                path = line[3:].strip()
                
                color = "#4CAF50" if "A" in status or "?" in status else "#E5C07B" if "M" in status else "#F44336"
                
                f_frame = ctk.CTkFrame(self.results_frame, fg_color="transparent")
                f_frame.pack(fill="x", pady=1)
                
                status_lbl = ctk.CTkLabel(f_frame, text=status, width=20, text_color=color, font=ctk.CTkFont(size=11, weight="bold"))
                status_lbl.pack(side="left", padx=5)
                
                btn = ctk.CTkButton(f_frame, text=path, anchor="w", fg_color="transparent", hover_color="#2a2d2e", height=24, font=ctk.CTkFont(size=12),
                                    command=lambda p=os.path.abspath(path): self.ide.open_file(p))
                btn.pack(side="left", fill="x", expand=True)
                
        except Exception as e:
            lbl = ctk.CTkLabel(self.results_frame, text=f"Git Error: {str(e)}", font=ctk.CTkFont(size=11), text_color="red")
            lbl.pack(pady=20)

    def perform_commit(self):
        msg = self.commit_entry.get().strip()
        if not msg: return
        
        try:
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", msg], check=True)
            self.commit_entry.delete(0, "end")
            self.refresh()
            if self.ide: self.ide.status_left.configure(text=" Git: Committed successfully")
        except Exception as e:
            if self.ide: self.ide.status_left.configure(text=f" Git Error: {str(e)}")
