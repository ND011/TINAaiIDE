import customtkinter as ctk
import os
import tkinter as tk

class FileExplorer(ctk.CTkFrame):
    def __init__(self, master, ide_ref=None, on_file_select=None, **kwargs):
        super().__init__(master, **kwargs)
        self.ide = ide_ref
        self.on_file_select = on_file_select
        self.selected_file_path = None # To store the path of the file right-clicked
        self.expanded_paths = {os.getcwd()} # Root is expanded by default

        # Search Bar
        self.search_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.search_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        self.search_entry = ctk.CTkEntry(self.search_frame, placeholder_text="Search files...", height=28, font=ctk.CTkFont(size=14))
        self.search_entry.pack(fill="x")
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh())

        # Context Menu
        self.context_menu = tk.Menu(self, tearoff=0, bg="#1a1a1e", fg="white", borderwidth=0, activebackground="#7c4dff")
        self.context_menu.add_command(label="Open", command=self.handle_open)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="New File", command=self.handle_new_file)
        self.context_menu.add_command(label="New Folder", command=self.handle_new_folder)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Ask AI about this", command=self.ai_explain)
        self.context_menu.add_command(label="Force Re-index (RAG)", command=self.force_reindex)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Delete", command=self.handle_delete)

        # Explorer Header
        self.label_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.label_frame.pack(fill="x", padx=10, pady=5)
        
        self.label = ctk.CTkLabel(self.label_frame, text="EXPLORER", font=ctk.CTkFont(size=13, weight="bold"), text_color="#bbbbbb")
        self.label.pack(side="left")
        
        self.new_project_btn = ctk.CTkButton(self.label_frame, text="✚", width=25, height=25, fg_color="transparent", hover_color="#37373d", command=self.handle_create_project)
        self.new_project_btn.pack(side="right", padx=(0, 5))
        
        self.refresh_btn = ctk.CTkButton(self.label_frame, text="↻", width=25, height=25, fg_color="transparent", hover_color="#37373d", command=self.refresh)
        self.refresh_btn.pack(side="right")

        # Tree View
        self.tree_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.tree_frame.pack(fill="both", expand=True, padx=0, pady=0) # No padding for edge-to-edge look

        self.ignored_dirs = {".git", "__pycache__", "node_modules", "data", "venv", ".vscode", "vector_db"}
        self.refresh()

    def refresh(self):
        """Rebuilds the file tree view."""
        for widget in self.tree_frame.winfo_children():
            widget.destroy()

        search_query = self.search_entry.get().lower()
        project_root = os.getcwd()
        self.draw_tree(project_root, self.tree_frame, level=0, filter_text=search_query)

    def handle_create_project(self):
        if self.ide and hasattr(self.ide, "show_create_project_dialog"):
            self.ide.show_create_project_dialog()

    def draw_tree(self, path, parent_widget, level, filter_text=""):
        try:
            items = os.listdir(path)
            items.sort(key=lambda x: (not os.path.isdir(os.path.join(path, x)), x.lower()))

            for item in items:
                if item in self.ignored_dirs:
                    continue
                
                full_path = os.path.join(path, item)
                is_dir = os.path.isdir(full_path)
                
                if filter_text and not is_dir and filter_text not in item.lower():
                    continue

                is_expanded = full_path in self.expanded_paths
                
                # Icon logic with expansion state
                if is_dir:
                    icon = "▼" if is_expanded else "▶"
                else:
                    icon = "📄"

                btn = ctk.CTkButton(
                    parent_widget, 
                    text=f" {icon}  {item}", 
                    anchor="w", 
                    fg_color="transparent",
                    text_color="#cccccc" if not is_dir else "#eeeeee",
                    hover_color="#2a2d2e",
                    height=int(24 * getattr(self, 'zoom_level', 1.0)),
                    corner_radius=0,
                    font=ctk.CTkFont(size=int(14 * getattr(self, 'zoom_level', 1.0))),
                    command=lambda p=full_path: self.handle_click(p)
                )
                btn.tree_level = level # Store for zoom scaling
                btn.pack(fill="x", padx=0)
                # Apply indentation to the button interior if possible, or use padx on pack
                # Since CTkButton doesn't support easy interior padding for text, we use pack padx
                btn.pack_configure(padx=(level * int(12 * getattr(self, 'zoom_level', 1.0)), 0))
                btn.bind("<Button-3>", lambda event, p=full_path: self.show_context_menu(event, p)) # Bind right-click

                if is_dir and (is_expanded or filter_text):
                    self.draw_tree(full_path, parent_widget, level + 1, filter_text)
        except Exception as e:
            print(f"Error reading path {path}: {e}")

    def handle_click(self, path):
        if os.path.isdir(path):
            if path in self.expanded_paths:
                self.expanded_paths.remove(path)
            else:
                self.expanded_paths.add(path)
            self.refresh()
        elif os.path.isfile(path) and self.on_file_select:
            self.on_file_select(path)

    def show_context_menu(self, event, path):
        self.selected_file_path = path
        self.context_menu.post(event.x_root, event.y_root)

    def handle_open(self):
        if self.selected_file_path:
            self.handle_click(self.selected_file_path)

    def handle_new_file(self):
        # Determine parent directory
        base_dir = self.selected_file_path if os.path.isdir(self.selected_file_path) else os.path.dirname(self.selected_file_path)
        
        # Modern prompt
        dialog = ctk.CTkInputDialog(text="Enter file name:", title="New File")
        name = dialog.get_input()
        if name:
            new_path = os.path.join(base_dir, name)
            try:
                open(new_path, 'a').close()
                self.refresh()
                if self.on_file_select:
                    self.on_file_select(new_path)
            except Exception as e:
                print(f"Create error: {e}")

    def handle_new_folder(self):
        base_dir = self.selected_file_path if os.path.isdir(self.selected_file_path) else os.path.dirname(self.selected_file_path)
        dialog = ctk.CTkInputDialog(text="Enter folder name:", title="New Folder")
        name = dialog.get_input()
        if name:
            new_path = os.path.join(base_dir, name)
            try:
                os.makedirs(new_path, exist_ok=True)
                self.expanded_paths.add(new_path)
                self.refresh()
            except Exception as e:
                print(f"Create error: {e}")

    def ai_explain(self):
        if self.selected_file_path and os.path.isfile(self.selected_file_path):
            with open(self.selected_file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
            query = f"Explain the logic of this file: {os.path.basename(self.selected_file_path)}\n\nContent:\n{content}"
            if self.ide and hasattr(self.ide, "ai_sidebar"):
                self.ide.ai_sidebar.entry.insert("1.0", query) # Fixed attribute name from ai_sidebar logic
                self.ide.ai_sidebar.send_query()

    def force_reindex(self):
        if os.path.exists("scripts/indexer.py"):
            import subprocess
            subprocess.Popen(["python", "scripts/indexer.py"])
            if self.ide:
                self.ide.status_left.configure(text=" System: Re-indexing project...")

    def handle_delete(self):
        if self.selected_file_path and os.path.exists(self.selected_file_path):
            from tkinter import messagebox
            if messagebox.askyesno("Delete", f"Are you sure you want to delete {os.path.basename(self.selected_file_path)}?", parent=self):
                try:
                    if os.path.isfile(self.selected_file_path):
                        os.remove(self.selected_file_path)
                    else:
                        import shutil
                        shutil.rmtree(self.selected_file_path)
                    self.refresh()
                except Exception as e:
                    print(f"Delete error: {e}")

    def get_visible_tree(self, path=None, level=0):
        """Returns a string representation of the currently expanded file tree."""
        if path is None:
            path = os.getcwd()
            
        tree_str = ""
        try:
            items = os.listdir(path)
            items.sort(key=lambda x: (not os.path.isdir(os.path.join(path, x)), x.lower()))

            for item in items:
                if item in self.ignored_dirs:
                    continue
                
                full_path = os.path.join(path, item)
                is_dir = os.path.isdir(full_path)
                
                # Check if this branch is expanded
                # (Note: Root is always considered expanded for this logic)
                indent = "  " * level
                if is_dir:
                    tree_str += f"{indent}📁 {item}/\n"
                    if full_path in self.expanded_paths:
                        tree_str += self.get_visible_tree(full_path, level + 1)
                else:
                    tree_str += f"{indent}📄 {item}\n"
                    
        except Exception as e:
            tree_str += f"{'  ' * level}[Error reading {os.path.basename(path)}]\n"
            
        return tree_str

    def set_zoom(self, zoom_level):
        """Scales fonts based on zoom level without flickering."""
        self.zoom_level = zoom_level
        new_size = int(14 * zoom_level)
        new_h = int(13 * zoom_level)
        
        self.search_entry.configure(font=ctk.CTkFont(size=new_size), height=int(28 * zoom_level))
        self.label.configure(font=ctk.CTkFont(size=new_h, weight="bold"))
        self.refresh_btn.configure(width=int(25 * zoom_level), height=int(25 * zoom_level))
        
        # Instead of refresh() which is expensive, update existing buttons
        btn_height = int(24 * zoom_level)
        btn_font = ctk.CTkFont(size=int(14 * zoom_level))
        
        for widget in self.tree_frame.winfo_children():
            if isinstance(widget, ctk.CTkButton):
                # Update height and font
                widget.configure(height=btn_height, font=btn_font)
                
                # Update indentation (padx)
                # We need to recover the 'level' somehow. We can store it in the widget or parse text.
                # But for now, let's just update font/height which is 90% of the flicker cause.
                # To fully fix indentation, we'd need to store the level on the button.
                if hasattr(widget, 'tree_level'):
                    widget.pack_configure(padx=(widget.tree_level * int(12 * zoom_level), 0))
