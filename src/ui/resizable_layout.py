import customtkinter as ctk

class DraggableSash(ctk.CTkFrame):
    def __init__(self, master, orientation="horizontal", on_resize=None, **kwargs):
        # horizontal orientation means a vertical sash for horizontal resizing
        # vertical orientation means a horizontal sash for vertical resizing
        cursor = "sb_h_double_arrow" if orientation == "horizontal" else "sb_v_double_arrow"
        width = 4 if orientation == "horizontal" else 0 
        height = 0 if orientation == "horizontal" else 4
        
        super().__init__(master, width=width, height=height, cursor=cursor, fg_color="transparent", **kwargs)
        self.orientation = orientation
        self.on_resize = on_resize
        
        self.bind("<Button-1>", self.on_start)
        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<Enter>", lambda e: self.configure(fg_color="#7c4dff"))
        self.bind("<Leave>", lambda e: self.configure(fg_color="transparent"))

    def on_start(self, event):
        self.start_pos = event.x_root if self.orientation == "horizontal" else event.y_root

    def on_drag(self, event):
        current_pos = event.x_root if self.orientation == "horizontal" else event.y_root
        delta = current_pos - self.start_pos
        self.start_pos = current_pos
        if self.on_resize:
            self.on_resize(delta)

class ResizablePane(ctk.CTkFrame):
    def __init__(self, master, initial_size=280, min_size=100, orientation="horizontal", side="left", **kwargs):
        # initial_size is width for horizontal, height for vertical
        width = initial_size if orientation == "horizontal" else 0
        height = initial_size if orientation == "vertical" else 0
        
        super().__init__(master, width=width, height=height, corner_radius=0, **kwargs)
        self.grid_propagate(False)
        self.pack_propagate(False)
        self.current_size = initial_size
        self.min_size = min_size
        self.orientation = orientation
        self.side = side # left, right for horizontal; top, bottom for vertical
        
        # Sash placement
        if orientation == "horizontal":
            sash_side = "right" if side == "left" else "left"
        else:
            sash_side = "bottom" if side == "top" else "top"
            
        self.sash = DraggableSash(self, orientation=orientation, on_resize=self.adjust_size)
        self.sash.pack(side=sash_side, fill="y" if orientation == "horizontal" else "x")

    def adjust_size(self, delta):
        multiplier = 1 if self.side in ["left", "top"] else -1
        new_size = self.current_size + (delta * multiplier)
        
        max_size = 1200
        
        if self.min_size < new_size < max_size:
            self.current_size = new_size
            if self.orientation == "horizontal":
                self.configure(width=self.current_size)
            else:
                self.configure(height=self.current_size)
            
            # Reduce flickering during drag by forcing idle tasks
            self.update_idletasks()
