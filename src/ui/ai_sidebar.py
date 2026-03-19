import customtkinter as ctk
import threading
import os
import re
import psutil
from src.core.ollama_client import OllamaClient
from src.core.agent_orchestrator import AgentOrchestrator
from src.core.rag import RAGEngine

class AISidebar(ctk.CTkFrame):
    def __init__(self, master, ide_ref=None, **kwargs):
        super().__init__(master, **kwargs)
        self.ide = ide_ref
        self.ollama = OllamaClient()
        self.orchestrator = AgentOrchestrator(self.ollama, ide_ref=self.ide)
        self.rag = RAGEngine()
        
        self.last_query = ""
        self.is_generating = False
        self.selected_context_files = set()

        # Header
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", pady=(20, 10), padx=20)
        self.header_label = ctk.CTkLabel(self.header_frame, text="AI ASSISTANT", font=ctk.CTkFont(size=14, weight="bold"), text_color="#bbbbbb")
        self.header_label.pack(side="left")

        # Resource Monitor
        self.monitor_frame = ctk.CTkFrame(self, height=30, fg_color="#1e1e1e", corner_radius=4)
        self.monitor_frame.pack(fill="x", padx=15, pady=5)
        self.cpu_label = ctk.CTkLabel(self.monitor_frame, text="CPU: --%", font=ctk.CTkFont(size=10, family="Consolas"), text_color="#858585")
        self.cpu_label.pack(side="left", padx=10)
        self.ai_load_indicator = ctk.CTkLabel(self.monitor_frame, text="● IDLE", font=ctk.CTkFont(size=10, weight="bold"), text_color="#4CAF50")
        self.ai_load_indicator.pack(side="right", padx=10)
        self.update_resource_usage()

        # --- CONTEXT SELECTOR ---
        self.context_frame = ctk.CTkFrame(self, fg_color="#252526", border_width=1, border_color="#333333")
        self.context_frame.pack(fill="x", padx=15, pady=5)
        
        self.context_header = ctk.CTkLabel(self.context_frame, text="📁 CONTEXT FILES (0)", font=ctk.CTkFont(size=11, weight="bold"), text_color="#858585")
        self.context_header.pack(fill="x", padx=10, pady=5)
        
        self.context_scroll = ctk.CTkScrollableFrame(self.context_frame, height=100, fg_color="transparent")
        self.context_scroll.pack(fill="x", padx=5, pady=5)
        
        self.refresh_context_btn = ctk.CTkButton(self.context_frame, text="Sync Open Tabs", height=22, font=ctk.CTkFont(size=10), fg_color="#3a3d3e", command=self.sync_context_with_tabs)
        self.refresh_context_btn.pack(fill="x", padx=10, pady=(0, 10))

        # Model Selector
        self.model_selector = ctk.CTkOptionMenu(self, values=["Searching..."], command=self.on_model_change, height=28, font=ctk.CTkFont(size=12))
        self.model_selector.pack(fill="x", padx=15, pady=5)
        self.after(500, self.refresh_models)

        # Chat Display
        self.chat_display = ctk.CTkTextbox(self, font=ctk.CTkFont(size=14), wrap="word", fg_color="#1e1e1e", border_width=1, border_color="#333333", corner_radius=0)
        self.chat_display.pack(fill="both", expand=True, padx=15, pady=10)
        self.chat_display.configure(state="disabled")

        # Control Bar
        self.control_bar = ctk.CTkFrame(self, height=30, fg_color="transparent")
        self.control_bar.pack(fill="x", padx=10)
        self.status_label = ctk.CTkLabel(self.control_bar, text="", font=ctk.CTkFont(size=12, slant="italic"))
        self.status_label.pack(side="left")
        self.stop_btn = ctk.CTkButton(self.control_bar, text="STOP", width=60, height=22, fg_color="#cc0000", command=self.stop_generation)
        
        # Input Area
        self.entry_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.entry_frame.pack(fill="x", padx=15, pady=(0, 15))
        self.entry = ctk.CTkEntry(self.entry_frame, placeholder_text="Ask Tina...", height=35, font=ctk.CTkFont(size=14))
        self.entry.pack(fill="x", side="left", expand=True, padx=(0, 5))
        self.entry.bind("<Return>", lambda e: self.send_query())
        self.send_btn = ctk.CTkButton(self.entry_frame, text="Send", width=60, height=35, fg_color="#007acc", command=self.send_query)
        self.send_btn.pack(side="right")

    def sync_context_with_tabs(self):
        """Automatically adds all currently open editor tabs to context."""
        if not self.ide: return
        for path in self.ide.editor_tabs.keys():
            self.add_file_to_context(path)
        self.refresh_context_ui()

    def add_file_to_context(self, path):
        self.selected_context_files.add(path)
        self.refresh_context_ui()

    def refresh_context_ui(self):
        for widget in self.context_scroll.winfo_children(): widget.destroy()
        
        for path in list(self.selected_context_files):
            name = os.path.basename(path)
            f_frame = ctk.CTkFrame(self.context_scroll, fg_color="transparent")
            f_frame.pack(fill="x", pady=1)
            
            lbl = ctk.CTkLabel(f_frame, text=f"📄 {name}", font=ctk.CTkFont(size=11), anchor="w")
            lbl.pack(side="left", fill="x", expand=True, padx=5)
            
            del_btn = ctk.CTkButton(f_frame, text="×", width=20, height=20, fg_color="transparent", hover_color="#cc0000", command=lambda p=path: self.remove_context_file(p))
            del_btn.pack(side="right")
            
        self.context_header.configure(text=f"📁 CONTEXT FILES ({len(self.selected_context_files)})")

    def remove_context_file(self, path):
        if path in self.selected_context_files:
            self.selected_context_files.remove(path)
            self.refresh_context_ui()

    def update_resource_usage(self):
        cpu = psutil.cpu_percent()
        self.cpu_label.configure(text=f"CPU: {cpu}%")
        self.after(2000, self.update_resource_usage)

    def refresh_models(self):
        def run():
            if self.ollama.check_connection():
                models = self.ollama.get_available_models()
                if models: self.after(0, lambda: self._update_selector_ui(models))
        threading.Thread(target=run, daemon=True).start()

    def _update_selector_ui(self, models):
        self.model_selector.configure(values=models)
        best = self.ollama.chat_model
        if best not in models:
            for m in models:
                if "3b" in m or "3.2" in m: best = m; break
        self.model_selector.set(best)
        self.ollama.chat_model = best

    def on_model_change(self, model_name): self.ollama.chat_model = model_name

    def set_busy(self, busy, status="Thinking..."):
        self.is_generating = busy
        if busy:
            self.status_label.configure(text=status)
            self.stop_btn.pack(side="right")
            self.ai_load_indicator.configure(text="● ACTIVE", text_color="#FF9800")
        else:
            self.status_label.configure(text="")
            self.stop_btn.pack_forget()
            self.ai_load_indicator.configure(text="● IDLE", text_color="#4CAF50")

    def send_query(self):
        query = self.entry.get().strip()
        if not query or self.is_generating: return
        self.last_query = query
        self.entry.delete(0, "end")
        
        self.set_busy(True)
        self.append_text(f"YOU: {query}\n", "user")

        def process_logic():
            try:
                # --- BUILD EXPLICIT CONTEXT ---
                context = ""
                for path in self.selected_context_files:
                    if os.path.exists(path):
                        try:
                            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                                context += f"\n--- FILE: {os.path.basename(path)} ---\n{f.read()}\n"
                        except: pass

                auto_keywords = ["create", "make", "delete", "folder", "directory", "file", "build", "run", "execute"]
                is_auto = any(kw in query.lower() for kw in auto_keywords)
                
                if not is_auto:
                    intent_res = self.ollama.run(self.ollama.fast_model, "Respond ONLY with 'AUTO' if user wants an action, else 'CHAT'.", f"Query: {query}")
                    if "AUTO" in intent_res.upper(): is_auto = True

                if is_auto:
                    self.after(0, lambda: self.append_text("🧠 [AUTONOMOUS AGENT ACTIVATED]\n", "sys"))
                    self.orchestrator.run_autonomous_loop(query, context, self.handle_auto_callback)
                else:
                    self.after(0, lambda: self.append_text("TINA: ", "bot"))
                    self.ollama.stream_run(self.ollama.chat_model, f"Context:\n{context}\nYou are Tina AI.", query, self.handle_stream_token)
            except Exception as e:
                self.after(0, lambda: self.append_text(f"Error: {str(e)}\n", "sys"))
                self.after(0, lambda: self.set_busy(False))

        threading.Thread(target=process_logic, daemon=True).start()

    def handle_stream_token(self, token):
        if token is None: self.after(0, lambda: self.set_busy(False))
        else: self.after(0, lambda: self.append_text(token, "bot"))

    def handle_auto_callback(self, text, status):
        if status == "done":
            self.after(0, lambda: self.set_busy(False))
            if self.ide: self.ide.explorer.refresh()
        else: self.after(0, lambda: self.append_text(text, status))

    def append_text(self, text, tag):
        self.chat_display.configure(state="normal")
        tag_colors = {"user": "#ffffff", "bot": "#cccccc", "sys": "#007acc", "done": "#00ff00"}
        self.chat_display.tag_config(tag, foreground=tag_colors.get(tag, "#cccccc"))
        self.chat_display.insert("end", text, tag)
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def stop_generation(self):
        self.ollama.stop()
        self.orchestrator.stop()
        self.set_busy(False)

    def set_zoom(self, level): pass
