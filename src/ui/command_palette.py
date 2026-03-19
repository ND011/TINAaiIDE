import customtkinter as ctk
import tkinter as tk

class CommandPalette(tk.Toplevel):
    def __init__(self, master, commands, **kwargs):
        super().__init__(master)
        self.master = master
        self.commands = commands
        self.commands_list = sorted(list(commands.keys()))
        
        # Window Setup
        self.wm_overrideredirect(True)
        self.attributes("-topmost", True)
        
        # Position at top center
        w, h = 600, 400
        x = master.winfo_rootx() + (master.winfo_width() // 2) - (w // 2)
        y = master.winfo_rooty() + 50
        self.geometry(f"{w}x{h}+{x}+{y}")
        
        # Main Frame
        self.main_frame = ctk.CTkFrame(self, fg_color="#252526", border_width=1, border_color="#3c3c3c", corner_radius=4)
        self.main_frame.pack(fill="both", expand=True)
        
        # Search Entry
        self.search_entry = ctk.CTkEntry(self.main_frame, placeholder_text="Type a command to run...", 
                                        height=35, fg_color="#3c3c3c", border_width=0, corner_radius=0,
                                        font=ctk.CTkFont(size=14))
        self.search_entry.pack(fill="x", padx=10, pady=(10, 5))
        self.search_entry.bind("<KeyRelease>", self.filter_commands)
        self.search_entry.bind("<Return>", lambda e: self.execute_selected())
        self.search_entry.bind("<Down>", lambda e: self.listbox.focus_set())
        self.search_entry.bind("<Escape>", lambda e: self.destroy())
        
        # Listbox
        self.listbox = tk.Listbox(self.main_frame, bg="#252526", fg="#cccccc", 
                                 font=ctk.CTkFont(size=13), borderwidth=0, highlightthickness=0,
                                 selectbackground="#007acc", selectforeground="white",
                                 activestyle="none")
        self.listbox.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.listbox.bind("<Double-Button-1>", lambda e: self.execute_selected())
        self.listbox.bind("<Return>", lambda e: self.execute_selected())
        self.listbox.bind("<Escape>", lambda e: self.destroy())
        
        self.filter_commands()
        self.search_entry.focus_set()
        
        # Close on focus out
        self.bind("<FocusOut>", lambda e: self.destroy())

    def filter_commands(self, event=None):
        query = self.search_entry.get().lower()
        self.listbox.delete(0, "end")
        for cmd in self.commands_list:
            if query in cmd.lower():
                self.listbox.insert("end", cmd)
        if self.listbox.size() > 0:
            self.listbox.selection_set(0)

    def execute_selected(self):
        try:
            selection = self.listbox.get(tk.ACTIVE)
            if selection and selection in self.commands:
                func = self.commands[selection]
                if func:
                    self.destroy()
                    func()
        except:
            self.destroy()
