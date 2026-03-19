import customtkinter as ctk
import tkinter as tk

class Minimap(tk.Canvas):
    def __init__(self, master, editor_textbox, **kwargs):
        # Professional IDEs use a very narrow width for minimap (around 60-100px)
        kwargs.setdefault('width', 80)
        kwargs.setdefault('bg', '#1e1e1e')
        kwargs.setdefault('highlightthickness', 0)
        kwargs.setdefault('borderwidth', 0)
        super().__init__(master, **kwargs)
        
        self.editor = editor_textbox
        self.editor_tab = master
        self.font_size = 2 # Tiny font for minimap representation
        
        # Overlay for visible area
        self.view_rect = self.create_rectangle(0, 0, 80, 0, outline="#404040", fill="#ffffff", stipple="gray25", width=1)
        
        # Bindings
        self.bind("<Button-1>", self.on_click)
        self.bind("<B1-Motion>", self.on_click)
        
        # Syncing
        self.update_needed = False
        self.after(500, self.periodic_update)

    def periodic_update(self):
        """Redraws the minimap representation of the code."""
        if self.update_needed:
            self.redraw()
            self.update_needed = False
        
        self.update_view_rect()
        self.after(200, self.periodic_update)

    def trigger_update(self):
        self.update_needed = True

    def redraw(self):
        self.delete("code")
        content = self.editor.get("1.0", "end-1c")
        lines = content.split("\n")
        
        y = 5
        char_w = 2
        line_h = 3
        
        # We only draw a representative "line" rather than actual characters for performance
        for line in lines[:500]: # Limit for performance on huge files
            if line.strip():
                # Find indentation
                indent = len(line) - len(line.lstrip())
                length = len(line.strip())
                
                # Draw a colored rectangle representing the code line
                # In a more advanced version, we'd use the tag colors from the editor
                self.create_rectangle(
                    indent * char_w, y, 
                    (indent + length) * char_w, y + 1, 
                    fill="#404040", outline="", tags="code"
                )
            y += line_h

    def update_view_rect(self):
        """Updates the highlighted rectangle to show the currently visible area of the editor."""
        try:
            # Get scroll fractions (0.0 to 1.0)
            y_start, y_end = self.editor._textbox.yview()
            
            # Map fractions to canvas height
            canvas_h = self.winfo_height()
            rect_y1 = y_start * canvas_h
            rect_y2 = y_end * canvas_h
            
            self.coords(self.view_rect, 0, rect_y1, 80, rect_y2)
        except: pass

    def on_click(self, event):
        """Scroll the main editor to the clicked position in the minimap."""
        canvas_h = self.winfo_height()
        if canvas_h > 0:
            fraction = event.y / canvas_h
            # Calculate where the top of the visible area should be
            # We want the click to be in the middle of the new view area
            y_start, y_end = self.editor._textbox.yview()
            visible_fraction = y_end - y_start
            target_start = max(0, min(1.0 - visible_fraction, fraction - (visible_fraction / 2)))
            
            self.editor._textbox.yview_moveto(target_start)
            self.update_view_rect()
