import customtkinter as ctk
import threading
from src.core.ollama_client import OllamaClient
from src.core.rag import RAGEngine

class TinaApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Tina AI COD - Modular Station")
        self.geometry("1100x750")
        
        # Initialize Core Systems
        self.ollama = OllamaClient()
        self.rag = RAGEngine()
        
        self.current_model = self.ollama.chat_model
        
        # Grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="TINA AI COD", font=ctk.CTkFont(size=22, weight="bold"))
        self.logo_label.pack(pady=25, padx=20)

        self.chat_btn = ctk.CTkButton(self.sidebar, text="Chat Assistant", command=self.set_chat_mode)
        self.chat_btn.pack(pady=10, padx=20)

        self.code_btn = ctk.CTkButton(self.sidebar, text="Coding Expert", command=self.set_code_mode)
        self.code_btn.pack(pady=10, padx=20)

        self.rag_switch = ctk.CTkSwitch(self.sidebar, text="Project RAG Context")
        self.rag_switch.pack(pady=25, padx=20)
        self.rag_switch.select()

        self.clear_btn = ctk.CTkButton(self.sidebar, text="Clear Memory", fg_color="transparent", border_width=1, command=self.clear_chat)
        self.clear_btn.pack(side="bottom", pady=20, padx=20)

        # Chat Interface
        self.chat_frame = ctk.CTkFrame(self)
        self.chat_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.chat_frame.grid_rowconfigure(0, weight=1)
        self.chat_frame.grid_columnconfigure(0, weight=1)

        self.chat_display = ctk.CTkTextbox(self.chat_frame, font=ctk.CTkFont(size=14))
        self.chat_display.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.chat_display.configure(state="disabled")

        self.input_area = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        self.input_area.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        self.input_area.grid_columnconfigure(0, weight=1)

        self.entry = ctk.CTkEntry(self.input_area, placeholder_text="Ask Tina...")
        self.entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.entry.bind("<Return>", lambda e: self.send_message())

        self.send_btn = ctk.CTkButton(self.input_area, text="Query", width=120, command=self.send_message)
        self.send_btn.grid(row=0, column=1)

        self.status = ctk.CTkLabel(self.sidebar, text="Ollama: Online", text_color="green")
        self.status.pack(side="bottom", pady=5)

    def set_chat_mode(self):
        self.current_model = self.ollama.chat_model
        self.append_to_chat(f"\nMode: Chat Assist ({self.current_model})", "sys")

    def set_code_mode(self):
        self.current_model = self.ollama.code_model
        self.append_to_chat(f"\nMode: Code Expert ({self.current_model})", "sys")

    def clear_chat(self):
        self.chat_display.configure(state="normal")
        self.chat_display.delete("1.0", "end")
        self.chat_display.configure(state="disabled")

    def append_to_chat(self, text, user="user"):
        self.chat_display.configure(state="normal")
        if user == "user":
            self.chat_display.insert("end", f"\nUSER: {text}\n", "user_tag")
        elif user == "sys":
            self.chat_display.insert("end", f"\n{text}\n", "sys_tag")
        else:
            self.chat_display.insert("end", f"\nTINA: {text}\n", "bot_tag")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def send_message(self):
        user_input = self.entry.get().strip()
        if not user_input: return
        self.entry.delete(0, "end")
        self.append_to_chat(user_input, "user")
        self.status.configure(text="Processing...", text_color="yellow")
        threading.Thread(target=self.get_ai_response, args=(user_input,), daemon=True).start()

    def get_ai_response(self, prompt):
        context = self.rag.query(prompt) if self.rag_switch.get() else ""
        system = "You are Tina AI, an expert software assistant."
        if self.current_model == self.ollama.code_model:
            system = "You are Tina AI, a Senior Software Engineer."

        full_prompt = f"Relevant Context:\n{context}\n\nUser Question: {prompt}" if context else prompt
        
        response = self.ollama.run(self.current_model, system, full_prompt)
        self.after(0, lambda: self.append_to_chat(response, "bot"))
        self.after(0, lambda: self.status.configure(text="Ollama: Online", text_color="green"))
