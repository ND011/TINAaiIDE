import customtkinter as ctk
import subprocess
import threading
import os
import sys
import queue

class IntegratedTerminal(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.process = None
        self.stdout_queue = queue.Queue()
        self.stderr_queue = queue.Queue()
        
        # Header / Tool Bar
        self.toolbar = ctk.CTkFrame(self, height=30, fg_color="transparent")
        self.toolbar.pack(fill="x", side="top")
        self.title_label = ctk.CTkLabel(self.toolbar, text="TERMINAL (POWERSHELL)", font=ctk.CTkFont(size=11, weight="bold"), text_color="#bbbbbb")
        self.title_label.pack(side="left", padx=15)
        
        self.clear_btn = ctk.CTkButton(self.toolbar, text="🗑️", width=25, height=25, fg_color="transparent", hover_color="#333333", command=self.clear_output)
        self.clear_btn.pack(side="right", padx=10)

        # Input Area
        self.input_frame = ctk.CTkFrame(self, height=35, fg_color="#1e1e1e")
        self.input_frame.pack(fill="x", side="bottom", padx=10, pady=(0, 10))
        self.prompt_label = ctk.CTkLabel(self.input_frame, text="PS >", font=("Consolas", 12), text_color="#007acc")
        self.prompt_label.pack(side="left", padx=5)
        self.cmd_entry = ctk.CTkEntry(self.input_frame, fg_color="#1e1e1e", text_color="#ffffff", border_width=0, font=("Consolas", 12))
        self.cmd_entry.pack(fill="x", side="left", expand=True)
        self.cmd_entry.bind("<Return>", lambda e: self.run_user_command())

        # Output Display
        self.output_box = ctk.CTkTextbox(self, font=("Consolas", 12), fg_color="#1e1e1e", text_color="#cccccc", undo=False, corner_radius=0)
        self.output_box.pack(fill="both", expand=True, padx=10, pady=(0, 5))
        self.output_box.configure(state="disabled")
        
        self.start_shell()
        self.update_ui_loop()

    def start_shell(self):
        try:
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            self.process = subprocess.Popen(
                ["powershell.exe", "-NoLogo", "-NoExit", "-Command", "-"],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, encoding='utf-8', bufsize=0, startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            threading.Thread(target=self._read_stream, args=(self.process.stdout, self.stdout_queue), daemon=True).start()
            threading.Thread(target=self._read_stream, args=(self.process.stderr, self.stderr_queue), daemon=True).start()
        except Exception as e:
            self.append_text(f"Failed to start PowerShell: {e}\n", "red")

    def _read_stream(self, stream, q):
        while True:
            line = stream.readline()
            if not line: break
            q.put(line)

    def update_ui_loop(self):
        while not self.stdout_queue.empty(): self.append_text(self.stdout_queue.get_nowait(), "white")
        while not self.stderr_queue.empty(): self.append_text(self.stderr_queue.get_nowait(), "red")
        self.after(50, self.update_ui_loop)

    def run_user_command(self):
        cmd = self.cmd_entry.get().strip()
        if cmd:
            self.cmd_entry.delete(0, "end")
            self.execute_command(cmd)

    def execute_command(self, cmd):
        """Standard method for both user and AI to inject commands."""
        if self.process and self.process.poll() is None:
            self.append_text(f"\nPS > {cmd}\n", "#00ff00")
            try:
                self.process.stdin.write(cmd + "\n")
                self.process.stdin.flush()
            except: self.start_shell()
        else:
            self.start_shell()
            self.execute_command(cmd)

    def append_text(self, text, color="white"):
        self.output_box.configure(state="normal")
        tag = f"color_{color}"
        self.output_box.tag_config(tag, foreground=color)
        self.output_box.insert("end", text, tag)
        self.output_box.configure(state="disabled")
        self.output_box.see("end")

    def clear_output(self):
        self.output_box.configure(state="normal")
        self.output_box.delete("1.0", "end")
        self.output_box.configure(state="disabled")

    def set_zoom(self, zoom):
        new_f = int(12 * zoom)
        self.title_label.configure(font=ctk.CTkFont(size=new_f, weight="bold"))
        self.output_box.configure(font=("Consolas", new_f))
        self.cmd_entry.configure(font=("Consolas", new_f))
        self.prompt_label.configure(font=("Consolas", new_f))
