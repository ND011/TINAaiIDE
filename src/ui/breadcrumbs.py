import customtkinter as ctk
import os

class Breadcrumbs(ctk.CTkFrame):
    def __init__(self, master, ide_ref, **kwargs):
        super().__init__(master, height=30, fg_color="#1e1e1e", corner_radius=0, **kwargs)
        self.ide = ide_ref
        self.path_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=12), text_color="#858585")
        self.path_label.pack(side="left", padx=15)
        
    def update_path(self, file_path):
        if not file_path:
            self.path_label.configure(text="")
            return
            
        # Get relative path from project root
        try:
            rel_path = os.path.relpath(file_path, os.getcwd())
            # Replace separators with arrows
            display_path = rel_path.replace(os.sep, "  >  ")
            self.path_label.configure(text=display_path)
        except:
            self.path_label.configure(text=os.path.basename(file_path))

    def set_zoom(self, zoom_level):
        new_size = int(12 * zoom_level)
        self.path_label.configure(font=ctk.CTkFont(size=new_size))
        self.configure(height=int(30 * zoom_level))
