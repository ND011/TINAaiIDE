import customtkinter as ctk
import os
import tkinter as tk
import subprocess

class FileExplorer(ctk.CTkFrame):
    def __init__(self, master, ide_ref=None, on_file_select=None, **kwargs):
        super().__init__(master, **kwargs)
        self.ide = ide_ref
        self.on_file_select = on_file_select
        self.selected_file_path = os.getcwd()
        self.expanded_paths = {os.getcwd()}
        
        self.icons = {
            ".py": "🐍", ".html": "🌐", ".css": "🎨", ".js": "📜", ".json": "⚙️",
            ".md": "📝", ".txt": "📄", ".bat": "⚡", ".ps1": "🐚",
            "folder": "📁", "folder_open": "📂", "default": "📄"
        }

        # Header Section
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=10, pady=(10, 0))
        self.title_lbl = ctk.CTkLabel(self.header, text="EXPLORER", font=ctk.CTkFont(size=11, weight="bold"), text_color="#bbbbbb")
        self.title_lbl.pack(side="left")
        self._create_tool_btn("↕️", self.collapse_all, "Collapse All")
        self._create_tool_btn("🔄", self.refresh, "Refresh")
        self._create_tool_btn("📁", self.handle_new_folder, "New Folder")
        self._create_tool_btn("📄", self.handle_new_file, "New File")

        # Search Bar
        self.search_entry = ctk.CTkEntry(self, placeholder_text="Search files...", height=24, font=ctk.CTkFont(size=12), border_width=1, border_color="#3c3c3c", fg_color="#1e1e1e")
        self.search_entry.pack(fill="x", padx=10, pady=10)
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh())

        self.main_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        self.main_scroll.pack(fill="both", expand=True)

        self.oe_header = self._create_section_header("OPEN EDITORS")
        self.oe_list_frame = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        self.oe_list_frame.pack(fill="x", pady=(0, 15))

        self.project_name = os.path.basename(os.getcwd()).upper()
        self.project_header = self._create_section_header(self.project_name)
        self.tree_frame = ctk.CTkFrame(self.main_scroll, fg_color="transparent")
        self.tree_frame.pack(fill="both", expand=True)

        self.ignored_dirs = {".git", "__pycache__", "node_modules", "data", "venv", ".vscode", "vector_db"}
        self.setup_context_menu()
        self.refresh()

    def _create_tool_btn(self, icon, command, tooltip):
        btn = ctk.CTkButton(self.header, text=icon, width=22, height=22, fg_color="transparent", hover_color="#333333", command=command, font=ctk.CTkFont(size=12))
        btn.pack(side="right", padx=1)
        return btn

    def _create_section_header(self, text):
        lbl = ctk.CTkLabel(self.main_scroll, text=f"▼ {text}", font=ctk.CTkFont(size=11, weight="bold"), text_color="#858585", anchor="w")
        lbl.pack(fill="x", padx=10, pady=(5, 2))
        return lbl

    def collapse_all(self):
        self.expanded_paths = {os.getcwd()}
        self.refresh()

    def setup_context_menu(self):
        self.context_menu = tk.Menu(self, tearoff=0, bg="#1a1a1e", fg="white", borderwidth=0, activebackground="#7c4dff")
        self.context_menu.add_command(label="New File", command=self.handle_new_file)
        self.context_menu.add_command(label="New Folder", command=self.handle_new_folder)
        self.context_menu.add_command(label="Rename", command=self.handle_rename)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Reveal in Explorer", command=self.reveal_in_explorer)
        self.context_menu.add_command(label="Copy Path", command=self.copy_path)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Delete", command=self.handle_delete)

    def handle_rename(self):
        if not self.selected_file_path or not os.path.exists(self.selected_file_path): return
        old_path = self.selected_file_path
        old_name = os.path.basename(old_path)
        
        dialog = ctk.CTkInputDialog(text=f"Rename '{old_name}' to:", title="Rename")
        new_name = dialog.get_input()
        
        if new_name and new_name != old_name:
            new_path = os.path.join(os.path.dirname(old_path), new_name)
            try:
                os.rename(old_path, new_path)
                self.refresh()
                if self.ide and old_path in self.ide.editor_tabs:
                    # Update internal IDE tab reference (optional, better to just reopen)
                    self.ide.open_file(new_path)
                    self.ide.handle_tab_close(old_path)
            except Exception as e:
                tk.messagebox.showerror("Error", f"Could not rename: {e}")

    def reveal_in_explorer(self):
        if self.selected_file_path:
            path = self.selected_file_path if os.path.isdir(self.selected_file_path) else os.path.dirname(self.selected_file_path)
            if os.name == 'nt': subprocess.Popen(f'explorer "{os.path.normpath(path)}"')
            else: subprocess.Popen(['xdg-open', path])

    def copy_path(self):
        if self.selected_file_path:
            self.clipboard_clear()
            self.clipboard_append(self.selected_file_path)

    def refresh(self):
        for widget in self.tree_frame.winfo_children(): widget.destroy()
        self.draw_tree(os.getcwd(), self.tree_frame, level=0, filter_text=self.search_entry.get().lower())
        self.refresh_open_editors()

    def refresh_open_editors(self):
        for widget in self.oe_list_frame.winfo_children(): widget.destroy()
        if not self.ide: return
        for path in list(self.ide.editor_tabs.keys()):
            name = os.path.basename(path)
            ext = os.path.splitext(path)[1].lower()
            icon = self.icons.get(ext, "📄")
            btn = ctk.CTkButton(self.oe_list_frame, text=f"  {icon}  {name}", anchor="w", fg_color="transparent", text_color="#cccccc", hover_color="#2a2d2e", height=22, corner_radius=0, font=ctk.CTkFont(size=12), command=lambda p=path: self.ide.show_tab(p))
            btn.pack(fill="x", padx=(15, 0))

    def draw_tree(self, path, parent_widget, level, filter_text=""):
        try:
            items = os.listdir(path)
            items.sort(key=lambda x: (not os.path.isdir(os.path.join(path, x)), x.lower()))
            for item in items:
                if item in self.ignored_dirs: continue
                full_path = os.path.join(path, item)
                is_dir = os.path.isdir(full_path)
                if filter_text and not is_dir and filter_text not in item.lower(): continue
                is_expanded = full_path in self.expanded_paths
                icon = self.icons["folder_open"] if is_dir and is_expanded else self.icons["folder"] if is_dir else self.icons.get(os.path.splitext(item)[1].lower(), "📄")
                btn = ctk.CTkButton(parent_widget, text=f" {icon}  {item}", anchor="w", fg_color="transparent", text_color="#cccccc" if not is_dir else "#eeeeee", hover_color="#2a2d2e", height=22, corner_radius=0, font=ctk.CTkFont(size=12), command=lambda p=full_path: self.handle_click(p))
                btn.pack(fill="x", padx=(level * 12 + 10, 0))
                btn.bind("<Button-3>", lambda event, p=full_path: self.show_context_menu(event, p))
                if is_dir and (is_expanded or filter_text): self.draw_tree(full_path, parent_widget, level + 1, filter_text)
        except: pass

    def handle_click(self, path):
        self.selected_file_path = path
        if os.path.isdir(path):
            if path in self.expanded_paths: self.expanded_paths.remove(path)
            else: self.expanded_paths.add(path)
            self.refresh()
        elif os.path.isfile(path) and self.on_file_select: self.on_file_select(path); self.refresh_open_editors()

    def show_context_menu(self, event, path):
        self.selected_file_path = path
        self.context_menu.post(event.x_root, event.y_root)

    def handle_new_file(self):
        base = self.selected_file_path if os.path.isdir(self.selected_file_path) else os.path.dirname(self.selected_file_path)
        name = ctk.CTkInputDialog(text="File name:", title="New File").get_input()
        if name:
            p = os.path.join(base, name)
            open(p, 'a').close(); self.refresh()
            if self.on_file_select: self.on_file_select(p)

    def handle_new_folder(self):
        base = self.selected_file_path if os.path.isdir(self.selected_file_path) else os.path.dirname(self.selected_file_path)
        name = ctk.CTkInputDialog(text="Folder name:", title="New Folder").get_input()
        if name:
            p = os.path.join(base, name)
            os.makedirs(p, exist_ok=True); self.expanded_paths.add(p); self.refresh()

    def handle_delete(self):
        if self.selected_file_path and os.path.exists(self.selected_file_path):
            if tk.messagebox.askyesno("Delete", f"Delete {os.path.basename(self.selected_file_path)}?"):
                if os.path.isfile(self.selected_file_path): os.remove(self.selected_file_path)
                else: import shutil; shutil.rmtree(self.selected_file_path)
                self.refresh()

    def set_zoom(self, level): pass
    def get_visible_tree(self): return ""
