from src.ui.explorer import FileExplorer
from src.ui.ai_sidebar import AISidebar
from src.ui.tabs import TabBar
from src.ui.terminal import IntegratedTerminal
from src.ui.command_palette import CommandPalette
from src.ui.resizable_layout import ResizablePane
from src.editor.editor_tab import EditorTab
from src.core.project_templates import ProjectTemplateManager
from src.core.plugin_manager import PluginManager
import os
import threading
import time
import tkinter as tk
import customtkinter as ctk

class TinaIDE(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Tina AI IDE V2")
        self.geometry("1400x900")
        self.after(0, lambda: self.state('zoomed'))
        
        # Increase Menu Font Size Globally (User requested BIG for Menu: 20pt)
        self.option_add('*Menu.font', '{Segoe UI} 20') 
        self.option_add('*Menu.background', '#252526')
        self.option_add('*Menu.foreground', 'white')
        self.option_add('*Menu.activeBackground', '#7c4dff')
        self.option_add('*Menu.activeForeground', 'white')
        
        # Plugin System
        self.plugin_manager = PluginManager(os.path.join(os.getcwd(), "src", "plugins"))
        self.plugin_manager.discover_plugins()

        # Zoom state
        self.zoom_level = 1.0

        # Layout Configuration
        self.grid_columnconfigure(0, weight=0) # Activity Bar
        self.grid_columnconfigure(1, weight=0) # Explorer
        self.grid_columnconfigure(2, weight=1) # Central Area (The one that grows)
        self.grid_columnconfigure(3, weight=0) # AI Sidebar
        self.grid_rowconfigure(0, weight=1)

        # 1. Activity Bar
        self.activity_bar = ctk.CTkFrame(self, width=55, corner_radius=0, fg_color="#333333")
        self.activity_bar.grid(row=0, column=0, rowspan=2, sticky="nsew") # Span both rows
        
        # Activity Bar Icons (Standard size: 24)
        self.explorer_icon = ctk.CTkLabel(self.activity_bar, text="📁", font=ctk.CTkFont(size=24), text_color="#ffffff")
        self.explorer_icon.pack(pady=20)
        
        self.ai_icon = ctk.CTkLabel(self.activity_bar, text="🤖", font=ctk.CTkFont(size=24), text_color="#858585")
        self.ai_icon.pack(pady=20)
        
        self.settings_icon = ctk.CTkLabel(self.activity_bar, text="⚙️", font=ctk.CTkFont(size=24), text_color="#858585")
        self.settings_icon.pack(side="bottom", pady=20)
        
        # Move Context Menu for Activity Bar
        self.activity_menu = tk.Menu(self, tearoff=0, bg="#1a1a1e", fg="white", borderwidth=0, activebackground="#7c4dff")
        self.activity_menu.add_command(label="Swap Sidebar Positions", command=self.swap_sidebars)
        
        self.activity_bar.bind("<Button-3>", lambda e: self.activity_menu.post(e.x_root, e.y_root))
        self.explorer_icon.bind("<Button-3>", lambda e: self.activity_menu.post(e.x_root, e.y_root))
        self.ai_icon.bind("<Button-3>", lambda e: self.activity_menu.post(e.x_root, e.y_root))

        # 2. Explorer (Resizable)
        self.explorer_pane = ResizablePane(self, initial_size=280, min_size=150, orientation="horizontal", side="left")
        self.explorer_pane.grid(row=0, column=1, rowspan=2, sticky="nsew") # Span both rows
        
        self.explorer = FileExplorer(self.explorer_pane, ide_ref=self, on_file_select=self.open_file, corner_radius=0, fg_color="#252526")
        self.explorer.pack(fill="both", expand=True)

        # 3. Main Horizontal Split (Editor area at top, Terminal at bottom)
        self.main_split = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_split.grid(row=0, column=2, rowspan=2, sticky="nsew")
        self.main_split.grid_rowconfigure(0, weight=1) # Editor grows
        self.main_split.grid_rowconfigure(1, weight=0) # Terminal stays fixed
        self.main_split.grid_columnconfigure(0, weight=1)

        # 3a. Central Area (Tabs + Editor)
        self.central_area = ctk.CTkFrame(self.main_split, corner_radius=0, fg_color="#1e1e1e")
        self.central_area.grid(row=0, column=0, sticky="nsew")
        self.central_area.grid_rowconfigure(1, weight=1)
        self.central_area.grid_columnconfigure(0, weight=1)

        # Tab Bar UI
        self.tab_container = ctk.CTkFrame(self.central_area, height=35, corner_radius=0, fg_color="#2d2d2d")
        self.tab_container.grid(row=0, column=0, sticky="ew")
        self.tab_container.grid_propagate(False)

        self.tab_bar = TabBar(self.tab_container, on_tab_change=self.show_tab, on_tab_close=self.handle_tab_close, fg_color="transparent")
        self.tab_bar.pack(fill="both", expand=True)

        self.editor_tabs = {} # path -> EditorTab
        self.active_path = None

        # 3b. Integrated Terminal (Bottom - Resizable)
        self.terminal_pane = ResizablePane(self.main_split, initial_size=250, min_size=120, orientation="vertical", side="bottom")
        self.terminal_pane.grid(row=1, column=0, sticky="nsew")

        self.terminal = IntegratedTerminal(self.terminal_pane, fg_color="#1e1e1e")
        self.terminal.pack(fill="both", expand=True)

        # 4. AI Sidebar (Resizable)
        self.ai_pane = ResizablePane(self, initial_size=350, min_size=150, orientation="horizontal", side="right")
        self.ai_pane.grid(row=0, column=3, rowspan=2, sticky="nsew") # Span both rows

        self.ai_sidebar = AISidebar(self.ai_pane, ide_ref=self, corner_radius=0, fg_color="#252526")
        self.ai_sidebar.pack(fill="both", expand=True)

        # 5. Status Bar
        self.status_bar = ctk.CTkFrame(self, height=22, corner_radius=0, fg_color="#333333")
        self.status_bar.grid(row=2, column=0, columnspan=5, sticky="ew")
        
        self.status_left = ctk.CTkLabel(self.status_bar, text=" 🟡 CONNECTING...", font=ctk.CTkFont(size=13, weight="bold"), text_color="white")
        self.status_left.pack(side="left", padx=10)
        
        self.status_right = ctk.CTkLabel(self.status_bar, text="UTF-8 | Qwen 2.5 | RAG: CHECKING... ", font=ctk.CTkFont(size=13), text_color="white")
        self.status_right.pack(side="right", padx=10)

        # 6. Global Shortcuts
        self.bind("<Control-o>", lambda e: self.open_file(tk.filedialog.askopenfilename()))
        self.bind("<Control-O>", lambda e: self.open_file(tk.filedialog.askopenfilename()))
        self.bind("<Control-k><Control-o>", lambda e: self.open_folder_dialog())
        self.bind("<Control-n>", lambda e: self.new_file_dialog())
        self.bind("<Control-N>", lambda e: self.new_file_dialog())
        self.bind("<Control-f>", lambda e: self.find_in_active_tab())
        self.bind("<Control-F>", lambda e: self.find_in_active_tab())
        self.bind("<Control-Shift-s>", lambda e: self.save_as_dialog())
        self.bind("<Control-Shift-S>", lambda e: self.save_as_dialog())
        self.bind("<Control-s>", lambda e: self.save_active_tab())
        self.bind("<Control-S>", lambda e: self.save_active_tab())
        self.bind("<Control-w>", lambda e: self.close_active_tab())
        self.bind("<Control-W>", lambda e: self.close_active_tab())
        
        # Zoom shortcuts
        self.bind("<Control-plus>", lambda e: self.zoom_in())
        self.bind("<Control-equal>", lambda e: self.zoom_in())
        self.bind("<Control-minus>", lambda e: self.zoom_out())
        self.bind("<Control-0>", lambda e: self.reset_zoom())

        # Menu Bar (Call after components are initialized)
        self.create_menu_bar()

        # Startup Sequence
        self.after(500, self.startup_sequence)

    def startup_sequence(self):
        """Automated boot sequence: checks services and opens documentation."""
        # 1. Auto-open README.md
        readme_path = os.path.join(os.getcwd(), "README.md")
        if os.path.exists(readme_path):
            self.open_file(readme_path)
            self.status_left.configure(text=" 📖 READING GUIDE...")

        # 2. Asynchronous Diagnostics
        def run_diagnostics():
            # Welcome Message
            self.terminal.write("\n[SYSTEM] INITIALIZING TINA AI WORKSTATION...\n")
            self.terminal.write(f"[SYSTEM] OLLAMA VERSION: 0.15.4\n")
            
            # Check Ollama
            ollama_ready = self.ai_sidebar.ollama.check_connection()
            
            # Check RAG (Simple check if directory exists)
            rag_ready = os.path.exists(os.path.join(os.getcwd(), "vector_db"))
            
            # Update UI
            def update_ui():
                if ollama_ready:
                    self.status_bar.configure(fg_color="#007acc") # Switch to Blue
                    self.status_left.configure(text=" 🟢 LIVE")
                    rag_status = "ON" if rag_ready else "OFF"
                    model_display = self.ai_sidebar.ollama.chat_model.split(":")[0].upper()
                    self.status_right.configure(text=f"UTF-8 | {model_display} | RAG: {rag_status} ")
                    self.terminal.write(f"[SYSTEM] TINA ENGINE IS LIVE (MODEL: {model_display})\n")
                    self.terminal.write("[SYSTEM] ALL SYSTEMS GO. READY FOR COMMANDS.\n")
                else:
                    self.status_bar.configure(fg_color="#d32f2f") # Switch to Red
                    self.status_left.configure(text=" 🔴 OLLAMA OFFLINE")
                    self.terminal.write("[ERROR] OLLAMA SERVER NOT DETECTED. PLEASE START OLLAMA.\n")

            self.after(0, update_ui)

        threading.Thread(target=run_diagnostics, daemon=True).start()

    def save_active_tab(self):
        if self.active_path and self.active_path in self.editor_tabs:
            self.editor_tabs[self.active_path].save_file()
            self.status_left.configure(text=f" Saved: {os.path.basename(self.active_path)}")

    def close_active_tab(self):
        if self.active_path:
            self.tab_bar.close_tab(self.active_path)

    def open_folder_dialog(self):
        folder = tk.filedialog.askdirectory(initialdir=os.getcwd(), title="Select Project Folder")
        if folder:
            os.chdir(folder)
            self.explorer.refresh()
            self.status_left.configure(text=f" Folder: {os.path.basename(folder)}")

    def new_file_dialog(self):
        dialog = ctk.CTkInputDialog(text="Enter file name:", title="New File")
        name = dialog.get_input()
        if name:
            new_path = os.path.join(os.getcwd(), name)
            try:
                open(new_path, 'a').close()
                self.open_file(new_path)
                self.explorer.refresh()
            except Exception as e:
                tk.messagebox.showerror("Error", f"Could not create file: {e}")

    def save_as_dialog(self):
        if self.active_path:
            initial_name = os.path.basename(self.active_path)
            new_path = tk.filedialog.asksaveasfilename(initialfile=initial_name, defaultextension=".py")
            if new_path:
                content = self.editor_tabs[self.active_path].textbox.get("1.0", "end-1c")
                try:
                    with open(new_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    self.open_file(new_path) # Open the new one
                    self.status_left.configure(text=f" Saved As: {os.path.basename(new_path)}")
                except Exception as e:
                    tk.messagebox.showerror("Error", f"Could not save file: {e}")

    def find_in_active_tab(self):
        if self.active_path:
            dialog = ctk.CTkInputDialog(text="Search text:", title="Find")
            query = dialog.get_input()
            if query:
                self.editor_tabs[self.active_path].find_text(query)

    def resolve_path(self, path):
        """Resolves a partial name or relative path to a full absolute path."""
        if not path: return os.getcwd()
        
        # 1. Try exact match from CWD
        full_path = os.path.abspath(os.path.join(os.getcwd(), path))
        if os.path.exists(full_path):
            return full_path
            
        # 2. Try to find a matching folder/file name in the project
        # We limit the search to avoid long hangs on huge projects
        for root, dirs, files in os.walk(os.getcwd()):
            # Check if current directory name matches
            if os.path.basename(root).lower() == path.lower():
                return root
            # Check children
            for d in dirs:
                if d.lower() == path.lower():
                    return os.path.join(root, d)
            for f in files:
                if f.lower() == path.lower() or f.lower().startswith(path.lower()):
                    return os.path.join(root, f)
            # Break early if we've searched too much (optional, but good for safety)
            if len(dirs) + len(files) > 1000: break
            
        return full_path # Fallback

    def apply_agent_action(self, action_type, path, content=None):
        """Action handler for the Autonomous Agent."""
        try:
            # Universal Path Resolution
            full_path = self.resolve_path(path)
            
            if action_type == "CREATE_FILE" or action_type == "UPDATE_FILE":
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content if content is not None else "")
                self.open_file(full_path)
                self.status_left.configure(text=f" 🤖 Agent: {action_type} {os.path.basename(path)}")
                
            elif action_type == "DELETE_FILE":
                if os.path.exists(full_path):
                    os.remove(full_path)
                    if self.active_path == full_path:
                        self.close_active_tab()
                self.status_left.configure(text=f" 🤖 Agent: DELETED {os.path.basename(path)}")
                
            elif action_type == "OPEN_FILE":
                if os.path.exists(full_path):
                    self.open_file(full_path)
            
            elif action_type == "CREATE_FOLDER":
                os.makedirs(full_path, exist_ok=True)
                self.status_left.configure(text=f" 🤖 Agent: CREATED FOLDER {os.path.basename(path)}")

            elif action_type == "EXPAND_FOLDER":
                if os.path.isdir(full_path):
                    self.explorer.expanded_paths.add(full_path)
                    self.status_left.configure(text=f" 🤖 Agent: EXPANDED {os.path.basename(path)}")
            
            elif action_type == "COLLAPSE_FOLDER":
                if os.path.isdir(full_path) and full_path in self.explorer.expanded_paths:
                    self.explorer.expanded_paths.remove(full_path)
                    self.status_left.configure(text=f" 🤖 Agent: COLLAPSED {os.path.basename(path)}")
            
            elif action_type == "RUN_COMMAND":
                # Execute in the integrated terminal
                self.terminal.execute_command(path) # 'path' here is the command string
                self.status_left.configure(text=f" 🤖 Agent: RUN_COMMAND {path[:20]}...")

            elif action_type == "LIST_FILES":
                if os.path.exists(full_path) and os.path.isdir(full_path):
                    files = os.listdir(full_path)
                    self.terminal.write(f"\n[AGENT DISCOVERY] Contents of {path}:\n" + "\n".join(files) + "\n")
                    self.status_left.configure(text=f" 🤖 Agent: LISTED {os.path.basename(path)}")

            elif action_type == "OPEN_FOLDER_FILES":
                if os.path.exists(full_path) and os.path.isdir(full_path):
                    for root, _, files in os.walk(full_path):
                        for f in files:
                            # Filter for text/code files
                            if f.lower().endswith(('.py', '.html', '.css', '.js', '.md', '.json', '.txt', '.java', '.c', '.cpp')):
                                self.open_file(os.path.join(root, f))
                    self.status_left.configure(text=f" 🤖 Agent: OPENED ALL FILES IN {os.path.basename(path)}")

            elif action_type == "AIDER_TASK":
                # Execute aider with the provided message/task
                cmd = f"aider --model ollama/qwen2.5-coder:7b --message \"{path}\" --no-auto-commits"
                self.terminal.execute_command(cmd)
                self.status_left.configure(text=f" 🤖 Agent: AIDER_TASK {path[:20]}...")

            elif action_type == "GLOB_SEARCH":
                import glob
                results = glob.glob(path, recursive=True)
                self.terminal.write(f"\n[AGENT GLOB] Results for '{path}':\n" + "\n".join(results[:50]) + "\n")
            
            elif action_type == "GREP_SEARCH":
                import re
                query, pattern = path.split(" ", 1) if " " in path else (path, "*")
                matches = []
                for root, _, files in os.walk(os.getcwd()):
                    for f in files:
                        if f.endswith(('.py', '.html', '.css', '.js', '.md')):
                            try:
                                with open(os.path.join(root, f), 'r', encoding='utf-8') as file:
                                    if query in file.read():
                                        matches.append(os.path.join(root, f))
                            except: pass
                self.terminal.write(f"\n[AGENT GREP] Matches for '{query}':\n" + "\n".join(matches[:20]) + "\n")

            elif action_type == "WEB_FETCH":
                import requests
                try:
                    res = requests.get(path, timeout=10)
                    self.terminal.write(f"\n[AGENT WEB] Fetched {path} ({len(res.text)} chars)\n")
                except Exception as e:
                    self.terminal.write(f"\n[AGENT WEB ERROR] {str(e)}\n")

            elif action_type == "TODO_WRITE":
                todo_path = os.path.join(os.getcwd(), ".kiro", "todos.json")
                os.makedirs(os.path.dirname(todo_path), exist_ok=True)
                with open(todo_path, "w") as f:
                    f.write(content if content else "[]")
                self.terminal.write(f"\n[AGENT TODO] Updated mission todos.\n")

            elif action_type == "SUB_AGENT":
                self.ai_sidebar.send_query(f"SUBMISSION: {path}") # path is the sub-task
                self.terminal.write(f"\n[AGENT MISSION] Spawning sub-agent for: {path}\n")

            self.explorer.refresh()
            return True
        except Exception as e:
            self.terminal.write(f"[AGENT ERROR]: {str(e)}\n")
            return False

    def show_command_palette(self):
        commands = {
            "Project: Create New Project": self.show_create_project_dialog,
            "File: Open Project Explorer": lambda: print("Explorer focused"),
            "AI: Clear Chat Memory": self.ai_sidebar.clear_chat if hasattr(self.ai_sidebar, "clear_chat") else None,
            "RAG: Force Re-index Project": lambda: os.system("python scripts/indexer.py"),
            "IDE: Toggle Sidebar": lambda: print("Toggle logic"),
            "Model: Switch to Expert (7B)": lambda: self.ai_sidebar.mode_var.set("CODE"),
            "Model: Switch to Chat (4B)": lambda: self.ai_sidebar.mode_var.set("CHAT"),
            "Mode: Autonomous Agent": lambda: self.ai_sidebar.mode_var.set("AUTO"),
            "View: Zoom In": self.zoom_in,
            "View: Zoom Out": self.zoom_out,
            "View: Reset Zoom": self.reset_zoom
        }
        palette = CommandPalette(self, commands=commands)

    def zoom_in(self):
        self.zoom_level = min(3.0, self.zoom_level + 0.1)
        self.update_ui_zoom()

    def zoom_out(self):
        self.zoom_level = max(0.5, self.zoom_level - 0.1)
        self.update_ui_zoom()

    def reset_zoom(self):
        self.zoom_level = 1.0
        self.update_ui_zoom()

    def update_ui_zoom(self):
        """Broadcast zoom level to all components."""
        # Scale physical dimensions
        new_activity_w = int(55 * self.zoom_level)
        new_status_h = int(22 * self.zoom_level)
        new_tab_h = int(35 * self.zoom_level)
        new_icon_size = int(24 * self.zoom_level)
        
        self.activity_bar.configure(width=new_activity_w)
        self.explorer_icon.configure(font=ctk.CTkFont(size=new_icon_size), pady=int(20 * self.zoom_level))
        self.ai_icon.configure(font=ctk.CTkFont(size=new_icon_size), pady=int(20 * self.zoom_level))
        self.settings_icon.configure(font=ctk.CTkFont(size=new_icon_size), pady=int(20 * self.zoom_level))
        
        self.tab_container.configure(height=new_tab_h)
        self.tab_bar.set_zoom(self.zoom_level)
        
        self.status_bar.configure(height=new_status_h)
        new_status_font = int(13 * self.zoom_level)
        self.status_left.configure(font=ctk.CTkFont(size=new_status_font, weight="bold"))
        self.status_right.configure(font=ctk.CTkFont(size=new_status_font))
        
        # Update Components
        self.explorer.set_zoom(self.zoom_level)
        self.terminal.set_zoom(self.zoom_level)
        self.ai_sidebar.set_zoom(self.zoom_level)
        
        # Update all Editor Tabs
        for tab in self.editor_tabs.values():
            tab.set_zoom(self.zoom_level)
        
        self.status_left.configure(text=f" Zoom: {int(self.zoom_level * 100)}%")
        
        # Consolidate all layout changes to reduce flickering
        self.update_idletasks()

    def open_file(self, file_path):
        name = os.path.basename(file_path)
        if file_path not in self.editor_tabs:
            tab = EditorTab(self.central_area, file_path, on_change=self.tab_bar.mark_modified, ide_ref=self)
            self.editor_tabs[file_path] = tab
            self.tab_bar.add_tab(file_path, name)
        
        self.tab_bar.select_tab(file_path)

    def show_tab(self, file_path):
        # Hide previous
        if self.active_path and self.active_path in self.editor_tabs:
            self.editor_tabs[self.active_path].grid_forget()
        
        # Show current
        self.active_path = file_path
        self.editor_tabs[file_path].grid(row=1, column=0, sticky="nsew")
        self.status_left.configure(text=f" Editing: {os.path.basename(file_path)}")
        
        self.plugin_manager.execute_plugin_hook("on_file_open", file_path)

    def toggle_explorer(self):
        if self.explorer_pane.winfo_viewable():
            self.explorer_pane.grid_remove()
        else:
            self.explorer_pane.grid()

    def toggle_ai_sidebar(self):
        if self.ai_pane.winfo_viewable():
            self.ai_pane.grid_remove()
        else:
            self.ai_pane.grid()

    def run_active_file(self):
        if self.active_path:
            self.terminal.execute_command(f"python {self.active_path}")

    def toggle_comment(self):
        if self.active_path and self.active_path in self.editor_tabs:
            self.editor_tabs[self.active_path].toggle_comment()

    def undo_action(self):
        if self.active_path and self.active_path in self.editor_tabs:
            self.editor_tabs[self.active_path].textbox.edit_undo()

    def redo_action(self):
        if self.active_path and self.active_path in self.editor_tabs:
            self.editor_tabs[self.active_path].textbox.edit_redo()

    def duplicate_selection(self):
        if self.active_path and self.active_path in self.editor_tabs:
            self.editor_tabs[self.active_path].duplicate_selection()

    def run_build_task(self, event=None):
        self.terminal.execute_command("python scripts/build_project.py")

    def run_selected_text(self):
        """Runs the currently selected text in the active editor in the terminal."""
        if self.active_path and self.active_path in self.editor_tabs:
            tab = self.editor_tabs[self.active_path]
            try:
                # Use sel.first/sel.last for CTkTextbox
                selection = tab.textbox.get("sel.first", "sel.last")
                if selection:
                    self.terminal.execute_command(selection)
                else:
                    self.status_left.configure(text=" No text selected")
            except tk.TclError:
                # tk.SEL_FIRST throws if no selection
                self.status_left.configure(text=" No text selected")

    def terminal_action_stub(self, action_name):
        """Generic stub for terminal actions not yet fully implemented."""
        self.status_left.configure(text=f" Terminal: {action_name} triggered")
        self.terminal.append_text(f"\n[INFO] {action_name} is currently a placeholder.\n", "yellow")

    def run_task_dialog(self):
        from tkinter import simpledialog
        task = simpledialog.askstring("Run Task", "Enter command to run as task:", parent=self)
        if task:
            self.terminal.execute_command(task)

    def create_menu_bar(self):
        self.menu_bar = tk.Menu(self)
        
        # 1. File Menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="New Text File", accelerator="Ctrl+N", command=self.new_file_dialog)
        self.file_menu.add_command(label="New Project...", command=self.show_create_project_dialog)
        self.file_menu.add_command(label="New Window", accelerator="Ctrl+Shift+N")
        
        self.profile_menu = tk.Menu(self.file_menu, tearoff=0)
        self.profile_menu.add_command(label="Default")
        self.file_menu.add_cascade(label="New Window with Profile", menu=self.profile_menu)
        
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Open File...", accelerator="Ctrl+O", command=lambda: self.open_file(tk.filedialog.askopenfilename()))
        self.file_menu.add_command(label="Open Folder...", accelerator="Ctrl+K Ctrl+O", command=self.open_folder_dialog)
        self.file_menu.add_command(label="Open Workspace from File...")
        
        self.recent_menu = tk.Menu(self.file_menu, tearoff=0)
        self.recent_menu.add_command(label="No Recent Workspaces")
        self.file_menu.add_cascade(label="Open Recent", menu=self.recent_menu)
        
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Add Folder to Workspace...")
        self.file_menu.add_command(label="Save Workspace As...")
        self.file_menu.add_command(label="Duplicate Workspace")
        
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Save", accelerator="Ctrl+S", command=self.save_active_tab)
        self.file_menu.add_command(label="Save As...", accelerator="Ctrl+Shift+S", command=self.save_as_dialog)
        self.file_menu.add_command(label="Save All", accelerator="Ctrl+K S")
        
        self.file_menu.add_separator()
        self.share_menu = tk.Menu(self.file_menu, tearoff=0)
        self.share_menu.add_command(label="Export...")
        self.file_menu.add_cascade(label="Share", menu=self.share_menu)
        
        self.file_menu.add_separator()
        self.auto_save_var = tk.BooleanVar(value=False)
        self.file_menu.add_checkbutton(label="Auto Save", variable=self.auto_save_var)
        
        self.prefs_menu = tk.Menu(self.file_menu, tearoff=0)
        self.prefs_menu.add_command(label="Settings")
        self.prefs_menu.add_command(label="Keyboard Shortcuts")
        self.file_menu.add_cascade(label="Preferences", menu=self.prefs_menu)
        
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Revert File")
        self.file_menu.add_command(label="Close Editor", accelerator="Ctrl+F4", command=self.close_active_tab)
        self.file_menu.add_command(label="Close Folder", accelerator="Ctrl+K F")
        self.file_menu.add_command(label="Close Window", accelerator="Alt+F4")
        
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.quit)
        
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        
        # 2. Edit Menu
        self.edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.edit_menu.add_command(label="Undo", accelerator="Ctrl+Z", command=self.undo_action)
        self.edit_menu.add_command(label="Redo", accelerator="Ctrl+Y", command=self.redo_action)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Cut", accelerator="Ctrl+X")
        self.edit_menu.add_command(label="Copy", accelerator="Ctrl+C")
        self.edit_menu.add_command(label="Paste", accelerator="Ctrl+V")
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Find", accelerator="Ctrl+F", command=self.find_in_active_tab)
        self.edit_menu.add_command(label="Replace", accelerator="Ctrl+H")
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Find in Files", accelerator="Ctrl+Shift+F")
        self.edit_menu.add_command(label="Replace in Files", accelerator="Ctrl+Shift+H")
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Toggle Line Comment", accelerator="Ctrl+/", command=self.toggle_comment)
        self.edit_menu.add_command(label="Toggle Block Comment", accelerator="Shift+Alt+A")
        self.edit_menu.add_command(label="Emmet: Expand Abbreviation", accelerator="Tab")
        self.menu_bar.add_cascade(label="Edit", menu=self.edit_menu)
        
        # 3. Selection Menu
        self.selection_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.selection_menu.add_command(label="Select All", accelerator="Ctrl+A")
        self.selection_menu.add_command(label="Expand Selection", accelerator="Shift+Alt+RightArrow")
        self.selection_menu.add_command(label="Shrink Selection", accelerator="Shift+Alt+LeftArrow")
        self.selection_menu.add_separator()
        self.selection_menu.add_command(label="Copy Line Up", accelerator="Shift+Alt+UpArrow")
        self.selection_menu.add_command(label="Copy Line Down", accelerator="Shift+Alt+DownArrow")
        self.selection_menu.add_command(label="Move Line Up", accelerator="Alt+UpArrow")
        self.selection_menu.add_command(label="Move Line Down", accelerator="Alt+DownArrow")
        self.selection_menu.add_command(label="Duplicate Selection", command=self.duplicate_selection)
        self.selection_menu.add_separator()
        self.selection_menu.add_command(label="Add Cursor Above", accelerator="Ctrl+Alt+UpArrow")
        self.selection_menu.add_command(label="Add Cursor Below", accelerator="Ctrl+Alt+DownArrow")
        self.selection_menu.add_command(label="Add Cursors to Line Ends", accelerator="Shift+Alt+I")
        self.selection_menu.add_command(label="Add Next Occurrence", accelerator="Ctrl+D")
        self.selection_menu.add_command(label="Add Previous Occurrence")
        self.selection_menu.add_command(label="Select All Occurrences")
        self.selection_menu.add_separator()
        self.selection_menu.add_command(label="Switch to Ctrl+Click for Multi-Cursor")
        self.selection_menu.add_command(label="Column Selection Mode")
        self.menu_bar.add_cascade(label="Selection", menu=self.selection_menu)
        
        # 4. View Menu
        self.view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.view_menu.add_command(label="Command Palette...", accelerator="Ctrl+Shift+P", command=self.show_command_palette)
        self.view_menu.add_command(label="Open View...")
        self.view_menu.add_separator()
        
        self.appearance_menu = tk.Menu(self.view_menu, tearoff=0)
        self.appearance_menu.add_command(label="Full Screen")
        self.appearance_menu.add_command(label="Zen Mode")
        self.view_menu.add_cascade(label="Appearance", menu=self.appearance_menu)
        
        self.layout_menu = tk.Menu(self.view_menu, tearoff=0)
        self.layout_menu.add_command(label="Split Editor Up")
        self.view_menu.add_cascade(label="Editor Layout", menu=self.layout_menu)
        
        self.view_menu.add_separator()
        self.view_menu.add_command(label="Explorer", accelerator="Ctrl+Shift+E", command=self.toggle_explorer)
        self.view_menu.add_command(label="Search", accelerator="Ctrl+Shift+F")
        self.view_menu.add_command(label="Source Control", accelerator="Ctrl+Shift+G")
        self.view_menu.add_command(label="Run", accelerator="Ctrl+Shift+D")
        self.view_menu.add_command(label="Extensions", accelerator="Ctrl+Shift+X")
        self.view_menu.add_command(label="Testing")
        
        self.view_menu.add_separator()
        self.view_menu.add_command(label="Problems", accelerator="Ctrl+Shift+M")
        self.view_menu.add_command(label="Output", accelerator="Ctrl+Shift+U")
        self.view_menu.add_command(label="Debug Console", accelerator="Ctrl+Shift+Y")
        self.view_menu.add_command(label="Terminal", accelerator="Ctrl+`")
        
        self.view_menu.add_separator()
        self.view_menu.add_checkbutton(label="Word Wrap", accelerator="Alt+Z")
        self.menu_bar.add_cascade(label="View", menu=self.view_menu)
        
        # 5. Go Menu
        self.go_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.go_menu.add_command(label="Back", accelerator="Alt+LeftArrow")
        self.go_menu.add_command(label="Forward", accelerator="Alt+RightArrow")
        self.go_menu.add_command(label="Last Edit Location", accelerator="Ctrl+K Ctrl+Q")
        self.go_menu.add_separator()
        self.go_menu.add_command(label="Switch Editor")
        self.go_menu.add_command(label="Switch Group")
        self.go_menu.add_separator()
        self.go_menu.add_command(label="Go to File...", accelerator="Ctrl+P")
        self.go_menu.add_command(label="Go to Symbol in Workspace...", accelerator="Ctrl+T")
        self.go_menu.add_separator()
        self.go_menu.add_command(label="Go to Symbol in Editor...", accelerator="Ctrl+Shift+O")
        self.go_menu.add_command(label="Go to Definition", accelerator="F12")
        self.go_menu.add_command(label="Go to Declaration")
        self.go_menu.add_command(label="Go to Type Definition")
        self.go_menu.add_command(label="Go to Implementations", accelerator="Ctrl+F12")
        self.go_menu.add_command(label="Go to References", accelerator="Shift+F12")
        self.go_menu.add_separator()
        self.go_menu.add_command(label="Go to Line/Column...", accelerator="Ctrl+G")
        self.go_menu.add_command(label="Go to Bracket", accelerator="Ctrl+Shift+\\")
        self.go_menu.add_separator()
        self.go_menu.add_command(label="Next Problem", accelerator="F8")
        self.go_menu.add_command(label="Previous Problem", accelerator="Shift+F8")
        self.go_menu.add_separator()
        self.go_menu.add_command(label="Next Change", accelerator="Alt+F3")
        self.go_menu.add_command(label="Previous Change", accelerator="Shift+Alt+F3")
        self.menu_bar.add_cascade(label="Go", menu=self.go_menu)
        
        # 6. Run Menu
        self.run_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.run_menu.add_command(label="Start Debugging", accelerator="F5")
        self.run_menu.add_command(label="Run Without Debugging", accelerator="Ctrl+F5", command=self.run_active_file)
        self.run_menu.add_command(label="Stop Debugging", accelerator="Shift+F5")
        self.run_menu.add_command(label="Restart Debugging", accelerator="Ctrl+Shift+F5")
        self.run_menu.add_separator()
        self.run_menu.add_command(label="Open Configurations")
        self.run_menu.add_command(label="Add Configuration...")
        self.run_menu.add_separator()
        self.run_menu.add_command(label="Step Over", accelerator="F10")
        self.run_menu.add_command(label="Step Into", accelerator="F11")
        self.run_menu.add_command(label="Step Out", accelerator="Shift+F11")
        self.run_menu.add_command(label="Continue", accelerator="F5")
        self.run_menu.add_separator()
        self.run_menu.add_command(label="Toggle Breakpoint", accelerator="F9")
        self.new_bp_menu = tk.Menu(self.run_menu, tearoff=0)
        self.new_bp_menu.add_command(label="Conditional Breakpoint...")
        self.run_menu.add_cascade(label="New Breakpoint", menu=self.new_bp_menu)
        self.run_menu.add_separator()
        self.run_menu.add_command(label="Enable All Breakpoints")
        self.run_menu.add_command(label="Disable All Breakpoints")
        self.run_menu.add_command(label="Remove All Breakpoints")
        self.run_menu.add_separator()
        self.run_menu.add_command(label="Install Additional Debuggers...")
        self.menu_bar.add_cascade(label="Run", menu=self.run_menu)
        
        # 7. Terminal Menu
        self.terminal_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.terminal_menu.add_command(label="New Terminal", accelerator="Ctrl+Shift+`", command=self.terminal.clear_output)
        self.terminal_menu.add_command(label="Split Terminal", accelerator="Ctrl+Shift+5", command=lambda: self.terminal_action_stub("Split Terminal"))
        self.terminal_menu.add_command(label="New Terminal Window", accelerator="Ctrl+Shift+Alt+`", command=lambda: self.terminal_action_stub("New Window"))
        self.terminal_menu.add_separator()
        self.terminal_menu.add_command(label="Run Task...", command=self.run_task_dialog)
        self.terminal_menu.add_command(label="Run Build Task...", accelerator="Ctrl+Shift+B", command=self.run_build_task)
        self.terminal_menu.add_command(label="Run Active File", command=self.run_active_file)
        self.terminal_menu.add_command(label="Run Selected Text", command=self.run_selected_text)
        self.terminal_menu.add_separator()
        self.terminal_menu.add_command(label="Clear Terminal", command=self.terminal.clear_output)
        self.terminal_menu.add_command(label="Show Running Tasks...", command=lambda: self.terminal_action_stub("Show Tasks"))
        self.terminal_menu.add_command(label="Restart Running Task...", command=lambda: self.terminal_action_stub("Restart Task"))
        self.terminal_menu.add_command(label="Terminate Task...", command=lambda: self.terminal_action_stub("Terminate Task"))
        self.terminal_menu.add_separator()
        self.terminal_menu.add_command(label="Configure Tasks...", command=lambda: self.terminal_action_stub("Configure Tasks"))
        self.terminal_menu.add_command(label="Configure Default Build Task...")
        self.menu_bar.add_cascade(label="Terminal", menu=self.terminal_menu)
        
        # 8. Help Menu
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.help_menu.add_command(label="Welcome")
        self.help_menu.add_command(label="Show All Commands", accelerator="Ctrl+Shift+P", command=self.show_command_palette)
        self.help_menu.add_command(label="Editor Playground")
        self.help_menu.add_command(label="Open Walkthrough...")
        self.help_menu.add_separator()
        self.help_menu.add_command(label="View License")
        self.help_menu.add_separator()
        self.help_menu.add_command(label="Toggle Developer Tools")
        self.help_menu.add_command(label="Open Process Explorer")
        self.help_menu.add_separator()
        self.help_menu.add_command(label="Check for Updates...")
        self.help_menu.add_separator()
        self.help_menu.add_command(label="About", command=self.show_about)
        self.menu_bar.add_cascade(label="Help", menu=self.help_menu)
        
        self.config(menu=self.menu_bar)

    def show_create_project_dialog(self):
        # 1. Ask for Project Name
        name_dialog = ctk.CTkInputDialog(text="Enter Project Name:", title="Create Project")
        project_name = name_dialog.get_input()
        if not project_name: return

        # 2. Ask for Project Type
        # Since CTkInputDialog only takes text, we'll use a simple approach:
        # Ask the user to type the type, or we could build a small Toplevel window.
        # For simplicity and style, let's use a small custom choice dialog.
        
        choice_dialog = tk.Toplevel(self)
        choice_dialog.title("Select Project Type")
        choice_dialog.geometry("300x250")
        choice_dialog.configure(bg="#252526")
        choice_dialog.transient(self)
        choice_dialog.grab_set()
        
        label = ctk.CTkLabel(choice_dialog, text="Select Template:", font=ctk.CTkFont(size=14, weight="bold"))
        label.pack(pady=20)
        
        selected_type = tk.StringVar(value="Python")
        
        for p_type in ProjectTemplateManager.TEMPLATES.keys():
            rb = ctk.CTkRadioButton(choice_dialog, text=p_type, variable=selected_type, value=p_type, 
                                     hover_color="#7c4dff", fg_color="#7c4dff")
            rb.pack(pady=5, padx=20, anchor="w")
            
        def on_confirm():
            p_type = selected_type.get()
            choice_dialog.destroy()
            
            success, result = ProjectTemplateManager.create_project(p_type, os.getcwd(), project_name)
            if success:
                self.status_left.configure(text=f" Created {p_type} project: {project_name}")
                self.explorer.refresh()
                # Optional: Open the main file
                main_file = "main.py" if p_type == "Python" else "index.html" if p_type == "Web" else "index.js"
                full_path = os.path.join(result, main_file)
                if os.path.exists(full_path):
                    self.open_file(full_path)
            else:
                tk.messagebox.showerror("Error", f"Failed to create project: {result}")

        confirm_btn = ctk.CTkButton(choice_dialog, text="Create", command=on_confirm, fg_color="#7c4dff", hover_color="#6a3de8")
        confirm_btn.pack(pady=20)

    def show_about(self):
        tk.messagebox.showinfo("About Tina AI IDE", "Tina AI IDE V2.0\nYour Offline AI-Powered Workstation.\n\nBuilt with CustomTkinter & Ollama.")

    def handle_tab_close(self, file_path):
        if file_path in self.editor_tabs:
            self.editor_tabs[file_path].destroy()
            del self.editor_tabs[file_path]
        
        if not self.editor_tabs:
            self.active_path = None
            self.status_left.configure(text=" Ready")

    def swap_sidebars(self):
        """Swaps the Explorer and AI Sidebar positions and updates grid weights."""
        if self.explorer_pane.side == "left":
            # Explorer (col 1) -> Right (col 3)
            # AI Sidebar (col 3) -> Left (col 1)
            # Activity Bar (col 0) -> Right (col 4)
            
            # 1. Add extra column for activity bar on right
            self.grid_columnconfigure(4, weight=0)
            
            # 2. Update Column Indices
            self.activity_bar.grid_configure(column=4)
            self.explorer_pane.grid_configure(column=3)
            self.ai_pane.grid_configure(column=1)
            self.main_split.grid_configure(column=2)
            
            # 3. Update Pane Properties (Sash sides)
            self.explorer_pane.side = "right"
            self.explorer_pane.sash.pack_forget()
            self.explorer_pane.sash.pack(side="left", fill="y")
            
            self.ai_pane.side = "left"
            self.ai_pane.sash.pack_forget()
            self.ai_pane.sash.pack(side="right", fill="y")
            
            # 4. Reset weights
            self.grid_columnconfigure(1, weight=0)
            self.grid_columnconfigure(3, weight=0)
            self.grid_columnconfigure(2, weight=1)
            self.grid_columnconfigure(4, weight=0)
            self.grid_columnconfigure(0, weight=0)
            
        else:
            # Restore Original Layout (Explorer Left, AI Right, Activity Bar Left)
            self.activity_bar.grid_configure(column=0)
            self.explorer_pane.grid_configure(column=1)
            self.ai_pane.grid_configure(column=3)
            self.main_split.grid_configure(column=2)
            
            self.explorer_pane.side = "left"
            self.explorer_pane.sash.pack_forget()
            self.explorer_pane.sash.pack(side="right", fill="y")
            
            self.ai_pane.side = "right"
            self.ai_pane.sash.pack_forget()
            self.ai_pane.sash.pack(side="left", fill="y")
            
            # Reset weights
            self.grid_columnconfigure(1, weight=0)
            self.grid_columnconfigure(3, weight=0)
            self.grid_columnconfigure(2, weight=1)
            self.grid_columnconfigure(0, weight=0)
            self.grid_columnconfigure(4, weight=0)
            
        self.update()
        self.status_left.configure(text=" Layout: Swapped sidebar positions")
