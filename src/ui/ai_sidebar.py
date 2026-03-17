import customtkinter as ctk
import threading
import os
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
        self.last_ai_code = ""
        
        self.current_model = self.ollama.chat_model
        self.is_generating = False
        self.mode_var = ctk.StringVar(value="CHAT")

        # Header
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", pady=(20, 10), padx=20)
        
        self.header_label = ctk.CTkLabel(self.header_frame, text="AI ASSISTANT", font=ctk.CTkFont(size=14, weight="bold"), text_color="#bbbbbb")
        self.header_label.pack(side="left")
        
        self.sync_btn = ctk.CTkButton(self.header_frame, text="Sync Discovery", width=100, height=24, 
                                      fg_color="#3a3d3e", hover_color="#007acc", 
                                      command=self.trigger_sync, corner_radius=2,
                                      font=ctk.CTkFont(size=11))
        self.sync_btn.pack(side="right")

        # 2. Controls Row
        self.control_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.control_frame.pack(fill="x", padx=15, pady=5)
        
        self.regen_btn = ctk.CTkButton(self.control_frame, text="Regenerate", width=100, height=26, fg_color="#3a3d3e", hover_color="#45494a", command=self.regenerate, corner_radius=2)
        self.regen_btn.pack(side="left", padx=2)
        
        self.apply_btn = ctk.CTkButton(self.control_frame, text="Apply Code", width=100, height=26, fg_color="#007acc", hover_color="#0062a3", command=self.apply_to_file, corner_radius=2)
        self.apply_btn.pack(side="left", padx=2)

        # 3. Metrics HUD
        self.metrics_frame = ctk.CTkFrame(self, fg_color="#252526", border_width=1, border_color="#404040")
        self.metrics_frame.pack(fill="x", padx=20, pady=10)
        
        self.latency_label = ctk.CTkLabel(self.metrics_frame, text="LATENCY: 0.0s", font=ctk.CTkFont(size=12, family="Consolas"), text_color="#858585")
        self.latency_label.pack(side="left", padx=10, pady=5)
        
        self.context_label = ctk.CTkLabel(self.metrics_frame, text="CONTEXT: 0 FILES", font=ctk.CTkFont(size=12, family="Consolas"), text_color="#858585")
        self.context_label.pack(side="right", padx=10, pady=5)

        # RAG Switch
        self.rag_switch = ctk.CTkSwitch(self, text="Use Project RAG", font=ctk.CTkFont(size=14), progress_color="#007acc")
        self.rag_switch.pack(pady=5, padx=22, anchor="w")
        self.rag_switch.select()

        # Chat Display
        self.chat_display = ctk.CTkTextbox(self, font=ctk.CTkFont(size=14), wrap="word", fg_color="#1e1e1e", border_width=1, border_color="#333333", corner_radius=0)
        self.chat_display.pack(fill="both", expand=True, padx=15, pady=10)
        self.chat_display.configure(state="disabled")

        # RAG Sources Panel (Collapsible-style)
        self.sources_frame = ctk.CTkFrame(self, height=0, fg_color="gray15")
        self.sources_frame.pack(fill="x", padx=10, pady=(0, 10))
        self.sources_label = ctk.CTkLabel(self.sources_frame, text="📚 SOURCE REFERENCES", font=ctk.CTkFont(size=12, weight="bold"), text_color="gray50")
        self.sources_label.pack(pady=2, padx=5, anchor="w")
        self.sources_list = ctk.CTkLabel(self.sources_frame, text="", font=ctk.CTkFont(size=11), justify="left", wraplength=300)
        self.sources_list.pack(pady=2, padx=10, anchor="w")

        # Control Bar (Thinking / Stop)
        self.control_bar = ctk.CTkFrame(self, height=30, fg_color="transparent")
        self.control_bar.pack(fill="x", padx=10)
        
        self.status_label = ctk.CTkLabel(self.control_bar, text="", font=ctk.CTkFont(size=13, slant="italic"))
        self.status_label.pack(side="left")
        
        self.stop_btn = ctk.CTkButton(self.control_bar, text="STOP", width=60, height=22, fg_color="#cc0000", hover_color="#ff0000", command=self.stop_generation)
        # Hidden by default
        
        # Input Area
        self.entry_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.entry_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        self.entry = ctk.CTkEntry(self.entry_frame, placeholder_text="Ask Tina...", height=35, fg_color="#3c3c3c", border_width=0, corner_radius=2, font=ctk.CTkFont(size=14))
        self.entry.pack(fill="x", side="left", expand=True, padx=(0, 5))
        self.entry.bind("<Return>", lambda e: self.send_query())

        self.send_btn = ctk.CTkButton(self.entry_frame, text="Send", width=60, height=35, fg_color="#007acc", hover_color="#0062a3", command=self.send_query, corner_radius=2)
        self.send_btn.pack(side="right")

    def set_busy(self, busy, status="Tina is thinking..."):
        self.is_generating = busy
        if busy:
            self.status_label.configure(text=status)
            self.stop_btn.pack(side="right")
        else:
            self.status_label.configure(text="")
            self.stop_btn.pack_forget()

    def send_query(self):
        query = self.entry.get().strip()
        if not query or self.is_generating: return
        self.last_query = query
        self.entry.delete(0, "end")
        
        self.set_busy(True)
        self.append_text(f"YOU: {query}\n", "user")

        def process_logic():
            try:
                context = ""
                if self.rag_switch.get():
                    context = self.rag.query(query)
                    self.after(0, lambda: self.context_label.configure(text=f"Context: {len(context.split('---'))} files"))

                # --- TURBO-MODE: REGEX BYPASS (Instant Navigation) ---
                import re
                turbo_match = None
                
                # Patterns: "open folder X", "expand X", "close X", "focus X"
                # 1. Bulk Open: "open all files in shree", "open shree folder and files"
                if re.search(r"\ball\s+files\b", query.lower()) or re.search(r"\bfiles\b", query.lower()):
                    # Extract the path by removing boilerplate words carefully
                    clean_path = query.lower()
                    for word in ["open", "show", "focus", "all", "files", "file", "in", "of", "and", "folder", "dir", "directory"]:
                        clean_path = re.sub(rf"\b{word}\b", "", clean_path)
                    turbo_match = ("OPEN_FOLDER_FILES", clean_path.strip())
                
                # 2. Open Single File: "open index.py", "open main"
                elif re.search(r"^(open|focus|show)\s+(file\s+)?(.*)", query.lower()) and ("." in query or any(kw in query.lower() for kw in ["main", "index", "init"])):
                    file_name = re.search(r"^(open|focus|show)\s+(file\s+)?(.*)", query.lower()).group(3).strip()
                    file_name = re.sub(r"\bfile\b", "", file_name).strip()
                    turbo_match = ("OPEN_FILE", file_name)

                # 3. Operations on Folders
                elif re.search(r"^(open|expand|show)\s+(folder|dir|directory)?\s*(.*)", query.lower()):
                    folder_name = re.search(r"^(open|expand|show)\s+(folder|dir|directory)?\s*(.*)", query.lower()).group(3).strip()
                    folder_name = re.sub(r"\b(folder|dir|directory)\b", "", folder_name).strip()
                    turbo_match = ("EXPAND_FOLDER", folder_name)
                elif re.search(r"^(close|collapse|hide)\s+(folder|dir|directory)?\s*(.*)", query.lower()):
                    folder_name = re.search(r"^(close|collapse|hide)\s+(folder|dir|directory)?\s*(.*)", query.lower()).group(3).strip()
                    folder_name = re.sub(r"\b(folder|dir|directory)\b", "", folder_name).strip()
                    turbo_match = ("COLLAPSE_FOLDER", folder_name)

                # 4. Commands and Lists
                elif re.search(r"^(run|execute)\s+(.*)", query.lower()):
                    cmd = re.search(r"^(run|execute)\s+(.*)", query.lower()).group(2).strip()
                    turbo_match = ("RUN_COMMAND", cmd)
                elif re.search(r"^(start|launch|open)\s+aider", query.lower()):
                    turbo_match = ("RUN_COMMAND", "aider --model ollama/qwen2.5-coder:7b --no-auto-commits")
                elif re.search(r"^(list|ls|show\s+contents?)\s*(in|of)?\s*(.*)", query.lower()):
                    path = re.search(r"^(list|ls|show\s+contents?)\s*(in|of)?\s*(.*)", query.lower()).group(3).strip()
                    path = re.sub(r"\b(folder|dir|directory|in|of)\b", "", path).strip() or "."
                    turbo_match = ("LIST_FILES", path)

                if turbo_match:
                    action, path = turbo_match
                    self.after(0, lambda: self.append_text(f"⚡ [TURBO EXECUTION]: {action} {path}\n", "sys"))
                    success = self.ide.apply_agent_action(action, path)
                    if success:
                        self.after(0, lambda: self.set_busy(False))
                        return # DONE INSTANTLY!

                # --- ZERO_CLICK SMART INTENT ---
                # Fallback keywords to force AUTO mode for navigation/building
                auto_keywords = ["open", "expand", "collapse", "create", "build", "make", "run", "delete", "navigate"]
                if any(kw in query.lower() for kw in auto_keywords):
                    intent = "AUTO"
                else:
                    intent = self.ollama.classify_intent(query)
                
                if intent == "AUTO":
                    self.after(0, lambda: self.mode_var.set("AUTO"))
                    self.after(0, lambda: self.append_text("🧠 [AUTONOMOUS AGENT ACTIVATED]\n", "sys"))
                    
                    # --- EXPLORER AWARENESS ---
                    if self.ide and hasattr(self.ide, 'explorer'):
                        explorer_tree = self.ide.explorer.get_visible_tree()
                        context += f"\n\n--- EXPLORER STATE (VISIBLE) ---\n{explorer_tree}\n"

                    # Add active file context if available
                    if self.ide and self.ide.active_path:
                        try:
                            with open(self.ide.active_path, "r", encoding="utf-8") as f:
                                file_content = f.read()
                                context += f"\n\n--- ACTIVE FILE: {os.path.basename(self.ide.active_path)} ---\n{file_content}"
                        except: pass
                        
                    self.orchestrator.run_autonomous_loop(query, context, self.handle_auto_callback)
                else:
                    self.after(0, lambda: self.mode_var.set("CHAT"))
                    system = "You are Tina AI. Be helpful, concise and smart."
                    model = self.ollama.chat_model
                    
                    self.after(0, lambda: self.append_text("TINA: ", "bot"))
                    self.ollama.stream_run(model, system, query, self.handle_stream_token)
            except Exception as e:
                self.after(0, lambda: self.append_text(f"\n[System Error]: {str(e)}", "sys"))
                self.after(0, lambda: self.set_busy(False))

        threading.Thread(target=process_logic, daemon=True).start()

    def stop_generation(self):
        self.ollama.stop()
        self.orchestrator.stop()
        self.set_busy(False)
        self.append_text("\n[Generation Stopped]", "bot")

    def regenerate(self):
        if self.last_query:
            self.entry.delete(0, "end")
            self.entry.insert(0, self.last_query)
            self.send_query()

    def apply_to_file(self):
        if not self.last_ai_code:
            self.append_text("\n[System: No code available to apply]", "sys")
            return
        if not self.ide or not self.ide.active_path:
            self.append_text("\n[System: No open file to apply to]", "sys")
            return
        
        tab = self.ide.editor_tabs.get(self.ide.active_path)
        if tab:
            tab.textbox.delete("1.0", "end")
            tab.textbox.insert("1.0", self.last_ai_code)
            self.append_text(f"\n[System: Applied code to {os.path.basename(self.ide.active_path)}]", "sys")

    def trigger_sync(self):
        self.append_text("\n[System: Starting Project Discovery...]\n", "sys")
        def run():
            import subprocess
            try:
                # Run indexer.py
                script_path = os.path.join(os.getcwd(), "scripts", "indexer.py")
                subprocess.run(["python", script_path], check=True)
                self.after(0, lambda: self.append_text("[System: Discovery Complete! RAG is now up-to-date.]\n", "sys"))
            except Exception as e:
                self.after(0, lambda: self.append_text(f"[System: Sync Error: {e}]\n", "sys"))
        threading.Thread(target=run, daemon=True).start()

    def handle_stream_token(self, token):
        if token is None: # Finished
            self.after(0, lambda: self.set_busy(False))
            self.after(0, lambda: self.append_text("\n", "bot"))
            return
        
        self.after(0, lambda t=token: self.append_text(t, "stream"))

    def handle_auto_callback(self, content, type="bot"):
        if type == "done":
            self.after(0, lambda: self.set_busy(False))
            return
        
        # Extract code from bot message for "Apply"
        if type == "bot" and "CODE IMPLEMENTED:" in content:
            code = content.split("CODE IMPLEMENTED:")[1].strip()
            # Remove markdown fences
            if "```" in code:
                code = code.split("```")[1].strip()
                if code.startswith(("python", "javascript", "html", "css", "json", "sh")):
                     code = "\n".join(code.split("\n")[1:])
            self.last_ai_code = code

        self.after(0, lambda c=content, t=type: self.append_text(c, t))

    def append_text(self, text, type="bot"):
        self.chat_display.configure(state="normal")
        if type == "user":
            self.chat_display.insert("end", f"\n{text}\n", "user_tag")
        elif type == "sys":
            self.chat_display.insert("end", f"\n{text}\n", "sys_tag")
        else:
            self.chat_display.insert("end", text)
        
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def clear_chat(self):
        self.chat_display.configure(state="normal")
        self.chat_display.delete("1.0", "end")
        self.chat_display.configure(state="disabled")
        self.sources_list.configure(text="")

    def set_zoom(self, zoom_level):
        """Scales fonts and physical dimensions based on zoom level."""
        new_h = int(14 * zoom_level)
        new_m = int(12 * zoom_level)
        
        self.header_label.configure(font=ctk.CTkFont(size=new_h, weight="bold"))
        self.latency_label.configure(font=ctk.CTkFont(size=new_m, family="Consolas"))
        self.context_label.configure(font=ctk.CTkFont(size=new_m, family="Consolas"))
        self.rag_switch.configure(font=ctk.CTkFont(size=new_h))
        self.chat_display.configure(font=ctk.CTkFont(size=new_h))
        
        # Scaling interactive component heights and fonts
        btn_h = int(35 * zoom_level)
        self.entry.configure(height=btn_h, font=ctk.CTkFont(size=new_h))
        self.send_btn.configure(height=btn_h, font=ctk.CTkFont(size=new_h))
        self.apply_btn.configure(height=int(26 * zoom_level), font=ctk.CTkFont(size=new_h))
        self.regen_btn.configure(height=int(26 * zoom_level), font=ctk.CTkFont(size=new_h))
        self.stop_btn.configure(height=int(22 * zoom_level), font=ctk.CTkFont(size=new_h))
