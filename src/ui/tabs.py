import customtkinter as ctk

class TabBar(ctk.CTkFrame):
    def __init__(self, master, on_tab_change=None, on_tab_close=None, **kwargs):
        super().__init__(master, height=35, **kwargs)
        self.on_tab_change = on_tab_change
        self.on_tab_close = on_tab_close
        
        self.zoom_level = 1.0
        self.tabs = {} # path -> TabButton
        self.active_path = None

        self.scroll_frame = ctk.CTkScrollableFrame(self, orientation="horizontal", height=35, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True)

    def add_tab(self, path, name):
        if path in self.tabs:
            self.select_tab(path)
            return

        tab_btn_frame = ctk.CTkFrame(self.scroll_frame, fg_color="#2d2d2d", corner_radius=0, height=35)
        tab_btn_frame.pack(side="left", padx=0, pady=0) # No padding for seamless look

        # Active indicator (top border)
        indicator = ctk.CTkFrame(tab_btn_frame, height=2, fg_color="transparent")
        indicator.pack(side="top", fill="x")

        btn = ctk.CTkButton(
            tab_btn_frame, 
            text=name, 
            width=int(120 * self.zoom_level), 
            height=int(33 * self.zoom_level),
            fg_color="transparent", 
            text_color="#969696",
            hover_color="#2d2d2d",
            corner_radius=0,
            font=ctk.CTkFont(size=int(14 * self.zoom_level)),
            command=lambda p=path: self.select_tab(p)
        )
        btn.pack(side="left", padx=(int(10 * self.zoom_level), 0))

        close_btn = ctk.CTkButton(
            tab_btn_frame, 
            text="×", 
            width=int(20 * self.zoom_level), 
            height=int(33 * self.zoom_level),
            fg_color="transparent", 
            hover_color="#37373d", 
            corner_radius=0,
            font=ctk.CTkFont(size=int(18 * self.zoom_level)),
            command=lambda p=path: self.close_tab(p)
        )
        close_btn.pack(side="right", padx=int(5 * self.zoom_level))

        self.tabs[path] = {
            "frame": tab_btn_frame,
            "button": btn,
            "close": close_btn,
            "indicator": indicator,
            "modified": False
        }
        self.select_tab(path)

    def select_tab(self, path):
        if self.active_path == path: return
        
        # Dim previous
        if self.active_path and self.active_path in self.tabs:
            self.tabs[self.active_path]["frame"].configure(fg_color="#2d2d2d")
            self.tabs[self.active_path]["button"].configure(text_color="#969696")
            self.tabs[self.active_path]["indicator"].configure(fg_color="transparent")

        # Highlight current
        self.active_path = path
        self.tabs[path]["frame"].configure(fg_color="#1e1e1e")
        self.tabs[path]["button"].configure(text_color="#ffffff")
        self.tabs[path]["indicator"].configure(fg_color="#007acc")
        
        if self.on_tab_change:
            self.on_tab_change(path)

    def close_tab(self, path):
        if path in self.tabs:
            self.tabs[path]["frame"].destroy()
            del self.tabs[path]
            
            if self.active_path == path:
                self.active_path = None
                # Switch to last tab if any
                if self.tabs:
                    new_path = list(self.tabs.keys())[-1]
                    self.select_tab(new_path)
            
            if self.on_tab_close:
                self.on_tab_close(path)

    def mark_modified(self, path, is_modified):
        if path in self.tabs:
            self.tabs[path]["modified"] = is_modified
            current_text = self.tabs[path]["button"].cget("text").replace("*", "").strip()
            new_text = f"{current_text} *" if is_modified else current_text
            self.tabs[path]["button"].configure(text=new_text)

    def set_zoom(self, zoom_level):
        """Scales tab sizes and fonts."""
        self.zoom_level = zoom_level
        new_h = int(35 * zoom_level)
        new_font = int(14 * zoom_level)
        new_close_font = int(18 * zoom_level)
        
        self.configure(height=new_h)
        self.scroll_frame.configure(height=new_h)
        
        for tab in self.tabs.values():
            tab["frame"].configure(height=new_h)
            tab["button"].configure(
                width=int(120 * zoom_level),
                height=int(33 * zoom_level),
                font=ctk.CTkFont(size=new_font)
            )
            tab["close"].configure(
                width=int(20 * zoom_level),
                height=int(33 * zoom_level),
                font=ctk.CTkFont(size=new_close_font)
            )
            tab["indicator"].configure(height=int(2 * zoom_level))
