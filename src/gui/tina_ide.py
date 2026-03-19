from src.ui.explorer import FileExplorer
from src.ui.ai_sidebar import AISidebar
from src.ui.tabs import TabBar
from src.ui.terminal import IntegratedTerminal
from src.ui.command_palette import CommandPalette
from src.ui.resizable_layout import ResizablePane
from src.editor.editor_tab import EditorTab
from src.core.project_templates import ProjectTemplateManager
from src.core.plugin_manager import PluginManager
from src.ui.plugin_view import PluginManagerUI
from src.ui.global_search import GlobalSearch
from src.ui.breadcrumbs import Breadcrumbs
from src.ui.git_sidebar import GitSidebar
from src.core.settings_manager import SettingsManager
import os
import threading
import time
import json
import tkinter as tk
import customtkinter as ctk

class TinaIDE(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Tina AI IDE V2")
        self.geometry("1400x900")
        self.state_path = os.path.join(os.getcwd(), "data", "workspace_state.json")
        
        self.settings = SettingsManager()
        self.editor_tabs = {}
        self.active_path = None
        self.zoom_level = self.settings.get("zoom_level")
        
        self.option_add('*Menu.font', '{Segoe UI} 20') 
        self.option_add('*Menu.background', '#252526')
        self.option_add('*Menu.foreground', 'white')
        
        self.plugin_manager = PluginManager(os.path.join(os.getcwd(), "src", "plugins"))
        self.plugin_manager.discover_plugins()

        self.grid_columnconfigure(0, weight=0); self.grid_columnconfigure(1, weight=0); self.grid_columnconfigure(2, weight=1); self.grid_columnconfigure(3, weight=0); self.grid_rowconfigure(0, weight=1)

        # 1. Activity Bar
        self.activity_bar = ctk.CTkFrame(self, width=55, corner_radius=0, fg_color="#333333")
        self.activity_bar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self._create_activity_icon("📁", "explorer")
        self._create_activity_icon("🔍", "search")
        self._create_activity_icon("🌿", "git")
        self._create_activity_icon("🤖", "ai_toggle")
        self._create_activity_icon("🧩", "extensions")
        
        # 2. Main Sidebar
        self.sidebar_pane = ResizablePane(self, initial_size=280, min_size=150, orientation="horizontal", side="left")
        self.sidebar_pane.grid(row=0, column=1, rowspan=2, sticky="nsew")
        self.explorer = FileExplorer(self.sidebar_pane, ide_ref=self, on_file_select=self.open_file, corner_radius=0, fg_color="#252526")
        self.global_search = GlobalSearch(self.sidebar_pane, ide_ref=self, corner_radius=0, fg_color="#252526")
        self.git_sidebar = GitSidebar(self.sidebar_pane, ide_ref=self, corner_radius=0, fg_color="#252526")
        self.plugin_view = PluginManagerUI(self.sidebar_pane, self.plugin_manager, corner_radius=0, fg_color="#252526")
        self.show_sidebar_view("explorer")

        # 3. Central Area
        self.main_split = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent"); self.main_split.grid(row=0, column=2, rowspan=2, sticky="nsew"); self.main_split.grid_rowconfigure(0, weight=1); self.main_split.grid_rowconfigure(1, weight=0); self.main_split.grid_columnconfigure(0, weight=1)
        
        self.central_area = ctk.CTkFrame(self.main_split, corner_radius=0, fg_color="#1e1e1e"); self.central_area.grid(row=0, column=0, sticky="nsew"); self.central_area.grid_rowconfigure(2, weight=1); self.central_area.grid_columnconfigure(0, weight=1)
        
        # Top Bar (Breadcrumbs + Actions)
        self.top_action_bar = ctk.CTkFrame(self.central_area, height=35, fg_color="#1e1e1e", corner_radius=0)
        self.top_action_bar.grid(row=0, column=0, sticky="ew")
        
        self.breadcrumbs = Breadcrumbs(self.top_action_bar, self, fg_color="transparent")
        self.breadcrumbs.pack(side="left", fill="y")
        
        # RUN BUTTON (Now in top-right of editor area)
        self.run_btn = ctk.CTkButton(self.top_action_bar, text="▶️ Run", width=60, height=24, fg_color="#2d2d2d", hover_color="#404040", text_color="#4CAF50", font=ctk.CTkFont(size=12, weight="bold"), command=self.run_active_file)
        self.run_btn.pack(side="right", padx=10, pady=5)

        self.tab_container = ctk.CTkFrame(self.central_area, height=35, corner_radius=0, fg_color="#2d2d2d")
        self.tab_container.grid(row=1, column=0, sticky="ew")
        self.tab_bar = TabBar(self.tab_container, on_tab_change=self.show_tab, on_tab_close=self.handle_tab_close, fg_color="transparent"); self.tab_bar.pack(fill="both", expand=True)

        self.terminal_pane = ResizablePane(self.main_split, initial_size=250, min_size=120, orientation="vertical", side="bottom")
        self.terminal_pane.grid(row=1, column=0, sticky="nsew"); self.terminal = IntegratedTerminal(self.terminal_pane, fg_color="#1e1e1e"); self.terminal.pack(fill="both", expand=True)

        self.ai_pane = ResizablePane(self, initial_size=350, min_size=150, orientation="horizontal", side="right")
        self.ai_pane.grid(row=0, column=3, rowspan=2, sticky="nsew"); self.ai_sidebar = AISidebar(self.ai_pane, ide_ref=self, corner_radius=0, fg_color="#252526"); self.ai_sidebar.pack(fill="both", expand=True)

        self.status_bar = ctk.CTkFrame(self, height=22, corner_radius=0, fg_color="#333333"); self.status_bar.grid(row=2, column=0, columnspan=5, sticky="ew")
        self.status_left = ctk.CTkLabel(self.status_bar, text=" 🟢 LIVE", font=ctk.CTkFont(size=13, weight="bold"), text_color="white"); self.status_left.pack(side="left", padx=10)

        self._setup_bindings(); self.create_menu_bar(); self.after(100, self.load_workspace_state); self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _create_activity_icon(self, text, view_name):
        lbl = ctk.CTkLabel(self.activity_bar, text=text, font=ctk.CTkFont(size=24), text_color="#858585"); lbl.pack(pady=20)
        if view_name == "ai_toggle": lbl.bind("<Button-1>", lambda e: self.toggle_ai_sidebar())
        else: lbl.bind("<Button-1>", lambda e: self.show_sidebar_view(view_name))
        setattr(self, f"{view_name}_icon", lbl)

    def show_sidebar_view(self, view_name):
        self.current_sidebar_view = view_name
        for view in [self.explorer, self.global_search, self.git_sidebar, self.plugin_view]: view.pack_forget()
        for icon in [self.explorer_icon, self.search_icon, self.git_icon, self.extensions_icon]: icon.configure(text_color="#858585")
        if view_name == "explorer": self.explorer.pack(fill="both", expand=True); self.explorer_icon.configure(text_color="#ffffff")
        elif view_name == "search": self.global_search.pack(fill="both", expand=True); self.search_icon.configure(text_color="#ffffff")
        elif view_name == "git": self.git_sidebar.pack(fill="both", expand=True); self.git_sidebar.refresh(); self.git_icon.configure(text_color="#ffffff")
        elif view_name == "extensions": self.plugin_view.pack(fill="both", expand=True); self.plugin_view.refresh(); self.extensions_icon.configure(text_color="#ffffff")
        if not self.sidebar_pane.winfo_viewable(): self.sidebar_pane.grid()

    def _setup_bindings(self):
        self.bind("<Control-o>", lambda e: self.open_file(tk.filedialog.askopenfilename())); self.bind("<Control-k><Control-o>", lambda e: self.open_folder_dialog()); self.bind("<Control-n>", lambda e: self.new_file_dialog()); self.bind("<Control-Shift-F>", lambda e: self.show_sidebar_view("search")); self.bind("<Control-Shift-G>", lambda e: self.show_sidebar_view("git")); self.bind("<Control-Shift-P>", lambda e: self.show_command_palette()); self.bind("<Control-plus>", lambda e: self.zoom_in()); self.bind("<Control-minus>", lambda e: self.zoom_out()); self.bind("<Control-s>", lambda e: self.save_active_tab())
        self.bind("<F5>", lambda e: self.run_active_file())

    def on_close(self): self.save_workspace_state(); self.settings.save(); self.destroy()

    def save_workspace_state(self):
        state = {"open_files": list(self.editor_tabs.keys()), "active_path": self.active_path, "zoom_level": self.zoom_level, "sidebar_view": self.current_sidebar_view}
        try:
            os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
            with open(self.state_path, "w") as f: json.dump(state, f, indent=4)
        except: pass

    def load_workspace_state(self, state_data=None):
        if not state_data and not os.path.exists(self.state_path): return
        try:
            if not state_data:
                with open(self.state_path, "r") as f: state_data = json.load(f)
            self.show_sidebar_view(state_data.get("sidebar_view", "explorer"))
            self.zoom_level = state_data.get("zoom_level", self.settings.get("zoom_level")); self.update_ui_zoom()
            for path in state_data.get("open_files", []):
                if os.path.exists(path): self.open_file(path)
            active = state_data.get("active_path")
            if active and active in self.editor_tabs: self.show_tab(active)
        except: pass

    def open_file(self, file_path):
        if not file_path: return
        if file_path not in self.editor_tabs:
            tab = EditorTab(self.central_area, file_path, on_change=self.tab_bar.mark_modified, ide_ref=self)
            self.editor_tabs[file_path] = tab; self.tab_bar.add_tab(file_path, os.path.basename(file_path))
        self.tab_bar.select_tab(file_path); self.explorer.refresh_open_editors()

    def show_tab(self, file_path):
        if self.active_path and self.active_path in self.editor_tabs: self.editor_tabs[self.active_path].grid_forget()
        self.active_path = file_path; self.editor_tabs[file_path].grid(row=2, column=0, sticky="nsew")
        self.status_left.configure(text=f" Editing: {os.path.basename(file_path)}")
        self.breadcrumbs.update_path(file_path)

    def run_active_file(self):
        if not self.active_path: return
        self.save_active_tab()
        ext = os.path.splitext(self.active_path)[1].lower()
        if ext == ".py": cmd = f"python \"{self.active_path}\""
        elif ext == ".js": cmd = f"node \"{self.active_path}\""
        elif ext == ".bat": cmd = f"\"{self.active_path}\""
        else: return
        self.terminal.execute_command(cmd)

    def handle_tab_close(self, file_path):
        if file_path in self.editor_tabs: self.editor_tabs[file_path].destroy(); del self.editor_tabs[file_path]
        if not self.editor_tabs: self.active_path = None; self.breadcrumbs.update_path(None)
        self.explorer.refresh_open_editors()

    def zoom_in(self): self.zoom_level = min(3.0, self.zoom_level + 0.1); self._sync_zoom()
    def zoom_out(self): self.zoom_level = max(0.5, self.zoom_level - 0.1); self._sync_zoom()
    def _sync_zoom(self): self.settings.set("zoom_level", self.zoom_level); self.update_ui_zoom()

    def update_ui_zoom(self):
        self.tab_bar.set_zoom(self.zoom_level); self.breadcrumbs.set_zoom(self.zoom_level)
        for tab in self.editor_tabs.values(): tab.set_zoom(self.zoom_level)
        self.terminal.set_zoom(self.zoom_level); self.update_idletasks()

    def apply_agent_action(self, action_type, path, content=None):
        try:
            full_path = self.resolve_path(path)
            if action_type in ["CREATE_FILE", "UPDATE_FILE"]:
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as f: f.write(content if content is not None else "")
                self.open_file(full_path)
            elif action_type == "RUN_COMMAND": self.terminal.execute_command(path)
            self.explorer.refresh(); return True
        except Exception as e:
            self.terminal.write(f"[AGENT ERROR]: {str(e)}\n"); return False

    def resolve_path(self, path):
        if not path: return os.getcwd()
        full_path = os.path.abspath(os.path.join(os.getcwd(), path))
        if os.path.exists(full_path): return full_path
        for root, dirs, files in os.walk(os.getcwd()):
            if os.path.basename(root).lower() == path.lower(): return root
            for d in dirs:
                if d.lower() == path.lower(): return os.path.join(root, d)
            for f in files:
                if f.lower() == path.lower() or f.lower().startswith(path.lower()): return os.path.join(root, f)
            if len(dirs) + len(files) > 1000: break
        return full_path

    def save_active_tab(self):
        if self.active_path and self.active_path in self.editor_tabs: self.editor_tabs[self.active_path].save_file()

    def open_folder_dialog(self):
        folder = tk.filedialog.askdirectory()
        if folder: os.chdir(folder); self.explorer.refresh()

    def new_file_dialog(self):
        name = ctk.CTkInputDialog(text="File name:", title="New File").get_input()
        if name: p = os.path.join(os.getcwd(), name); open(p, 'a').close(); self.open_file(p); self.explorer.refresh()

    def show_command_palette(self):
        palette = CommandPalette(self, commands={"File: New File": self.new_file_dialog, "Run: Active File": self.run_active_file, "View: Explorer": lambda: self.show_sidebar_view("explorer")})

    def toggle_ai_sidebar(self):
        if self.ai_pane.winfo_viewable(): self.ai_pane.grid_remove()
        else: self.ai_pane.grid()

    def create_menu_bar(self):
        m = tk.Menu(self); f = tk.Menu(m, tearoff=0); f.add_command(label="New File", command=self.new_file_dialog); f.add_command(label="Run Active File", accelerator="F5", command=self.run_active_file); f.add_command(label="Exit", command=self.on_close); m.add_cascade(label="File", menu=f)
        self.config(menu=m)
