import customtkinter as ctk

class PluginManagerUI(ctk.CTkFrame):
    def __init__(self, master, plugin_manager, **kwargs):
        super().__init__(master, **kwargs)
        self.pm = plugin_manager
        
        # Header
        self.header_label = ctk.CTkLabel(self, text="EXTENSIONS", font=ctk.CTkFont(size=13, weight="bold"), text_color="#bbbbbb")
        self.header_label.pack(pady=(10, 5), padx=20, anchor="w")
        
        # Search Box
        self.search_entry = ctk.CTkEntry(self, placeholder_text="Search extensions...", height=28)
        self.search_entry.pack(fill="x", padx=10, pady=5)
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh())

        # Plugin List (Scrollable)
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.refresh()

    def refresh(self):
        """Rebuilds the plugin list view."""
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
            
        search_query = self.search_entry.get().lower()
        plugins = self.pm.get_all_plugin_info()
        
        for p in plugins:
            if search_query and search_query not in p['name'].lower():
                continue
                
            p_frame = ctk.CTkFrame(self.scroll_frame, fg_color="#2d2d2d", corner_radius=4)
            p_frame.pack(fill="x", pady=2, padx=2)
            
            # Icon Placeholder
            icon_lbl = ctk.CTkLabel(p_frame, text="🧩", font=ctk.CTkFont(size=20))
            icon_lbl.pack(side="left", padx=10, pady=10)
            
            # Name and Status
            info_frame = ctk.CTkFrame(p_frame, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, pady=5)
            
            name_lbl = ctk.CTkLabel(info_frame, text=p['name'].replace('_', ' ').title(), font=ctk.CTkFont(size=13, weight="bold"), anchor="w")
            name_lbl.pack(fill="x")
            
            status_text = "Enabled" if p['loaded'] else "Disabled"
            status_color = "#4CAF50" if p['loaded'] else "#858585"
            status_lbl = ctk.CTkLabel(info_frame, text=status_text, font=ctk.CTkFont(size=11), text_color=status_color, anchor="w")
            status_lbl.pack(fill="x")
            
            # Toggle Switch
            switch = ctk.CTkSwitch(p_frame, text="", width=40, command=lambda n=p['name'], s=p['enabled']: self.toggle_plugin(n, not s))
            if p['enabled']:
                switch.select()
            switch.pack(side="right", padx=10)

    def toggle_plugin(self, name, new_state):
        self.pm.toggle_plugin(name, new_state)
        self.refresh()
