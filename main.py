from src.gui.tina_ide import TinaIDE
import customtkinter as ctk

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    
    # Increase UI Scale for better readability
    ctk.set_widget_scaling(1.25)
    ctk.set_window_scaling(1.25)
    
    print("Launching Tina AI IDE...")
    app = TinaIDE()
    app.mainloop()
