import customtkinter as ctk
import subprocess
import threading
import os

class IntegratedTerminal(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # 1. Header / Tool Bar (Pack Top)
        self.toolbar = ctk.CTkFrame(self, height=30, fg_color="transparent")
        self.toolbar.pack(fill="x", side="top")
        
        self.title_label = ctk.CTkLabel(self.toolbar, text="TERMINAL", font=ctk.CTkFont(size=13, weight="bold"), text_color="#bbbbbb")
        self.title_label.pack(side="left", padx=20)
        
        self.clear_btn = ctk.CTkButton(self.toolbar, text="🗑️", width=25, height=25, fg_color="transparent", hover_color="#37373d", command=self.clear_output)
        self.clear_btn.pack(side="right", padx=10)

        # 2. Input Area (Pack Bottom - Fixed Priority)
        self.input_frame = ctk.CTkFrame(self, height=45, fg_color="#1e1e1e")
        self.input_frame.pack(fill="x", side="bottom", padx=10, pady=(0, 10))
        
        self.prompt_label = ctk.CTkLabel(self.input_frame, text="PS >", font=("Consolas", 14), text_color="#007acc")
        self.prompt_label.pack(side="left", padx=(5, 5))
        
        self.cmd_entry = ctk.CTkEntry(self.input_frame, fg_color="#1e1e1e", text_color="#ffffff", border_width=0, font=("Consolas", 14), corner_radius=0)
        self.cmd_entry.pack(fill="x", side="left", expand=True)
        self.cmd_entry.bind("<Return>", lambda e: self.run_command())

        # 3. Output Display (Pack Center - Fill Remaining space)
        self.output_box = ctk.CTkTextbox(self, font=("Consolas", 14), fg_color="#1e1e1e", text_color="#cccccc", undo=False, corner_radius=0)
        self.output_box.pack(fill="both", expand=True, padx=10, pady=(0, 5))
        self.output_box.configure(state="disabled")

    def clear_output(self):
        self.output_box.configure(state="normal")
        self.output_box.delete("1.0", "end")
        self.output_box.configure(state="disabled")

    def run_command(self):
        cmd = self.cmd_entry.get().strip()
        if not cmd: return
        self.cmd_entry.delete(0, "end")
        
        self.append_text(f"\nPS > {cmd}\n", "#00ff00")
        
        threading.Thread(target=self._execute, args=(cmd,), daemon=True).start()

    def _execute(self, cmd):
        try:
            # Use powershell for commands
            process = subprocess.Popen(
                ["powershell", "-Command", cmd],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            
            stdout, stderr = process.communicate()
            
            if stdout:
                self.after(0, lambda: self.append_text(stdout, "white"))
            if stderr:
                self.after(0, lambda: self.append_text(stderr, "red"))
                
        except Exception as e:
            self.after(0, lambda: self.append_text(f"Terminal Error: {str(e)}\n", "red"))

    def append_text(self, text, color="white"):
        self.output_box.configure(state="normal")
        # Creating a unique tag for the color
        tag_name = f"color_{color}"
        self.output_box.tag_config(tag_name, foreground=color)
        self.output_box.insert("end", text, tag_name)
        self.output_box.configure(state="disabled")
        self.output_box.see("end")

    def write(self, text):
        """Compatibility alias for append_text."""
        self.append_text(text)

    def execute_command(self, cmd):
        """Programmatically inject a command into the terminal."""
        cmd = cmd.strip()
        if "\n" not in cmd:
            self.cmd_entry.delete(0, "end")
            self.cmd_entry.insert(0, cmd)
            self.run_command()
        else:
            self.append_text(f"\nPS > [Executing Script Block]\n", "#00ff00")
            threading.Thread(target=self._execute, args=(cmd,), daemon=True).start()

    def set_zoom(self, zoom_level):
        """Scales fonts based on zoom level."""
        base_title = 13
        base_mono = 14
        
        new_title = int(base_title * zoom_level)
        new_mono = int(base_mono * zoom_level)
        
        self.title_label.configure(font=ctk.CTkFont(size=new_title, weight="bold"))
        self.prompt_label.configure(font=("Consolas", new_mono))
        self.cmd_entry.configure(font=("Consolas", new_mono))
        self.output_box.configure(font=("Consolas", new_mono))
        
        # Scaling heights and padding
        self.input_frame.configure(height=int(45 * zoom_level))
        self.prompt_label.configure(padx=int(10 * zoom_level))
