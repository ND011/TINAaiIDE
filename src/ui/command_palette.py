import customtkinter as ctk

class CommandPalette(ctk.CTkToplevel):
    def __init__(self, master, commands=None, **kwargs):
        super().__init__(master, **kwargs)
        self.title("Command Palette")
        self.geometry("600x400")
        self.attributes("-topmost", True)
        self.overrideredirect(True) # Borderless like VS Code

        # Center on screen
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - 300
        y = (screen_height // 2) - 200
        self.geometry(f"600x400+{x}+{y}")
        
        self.commands = commands or {}
        self.filtered_keys = list(self.commands.keys())

        # Main Design
        self.configure(fg_color="#1e1e1e")
        
        self.search_entry = ctk.CTkEntry(self, placeholder_text="Type a command...", height=40, font=ctk.CTkFont(size=16))
        self.search_entry.pack(fill="x", padx=10, pady=10)
        self.search_entry.bind("<KeyRelease>", self.filter_commands)
        self.search_entry.bind("<Down>", self.focus_list)
        self.search_entry.bind("<Escape>", lambda e: self.destroy())
        self.search_entry.focus_set()

        self.list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.refresh_list()

    def filter_commands(self, event=None):
        query = self.search_entry.get().lower()
        self.filtered_keys = [k for k in self.commands.keys() if query in k.lower()]
        self.refresh_list()

    def refresh_list(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        for key in self.filtered_keys:
            btn = ctk.CTkButton(
                self.list_frame, 
                text=key, 
                anchor="w", 
                fg_color="transparent",
                hover_color="gray25",
                height=35,
                font=ctk.CTkFont(size=14),
                command=lambda k=key: self.execute(k)
            )
            btn.pack(fill="x", pady=1)

    def execute(self, key):
        func = self.commands[key]
        self.destroy()
        if func: func()

    def focus_list(self, event):
        # We don't have true arrow navigation yet but we can click
        pass
