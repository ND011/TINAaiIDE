import customtkinter as ctk
import os
import tkinter as tk
from pygments import lexers, util as pygments_util
from pygments.token import Token

class EditorTab(ctk.CTkFrame):
    def __init__(self, master, file_path, on_change=None, ide_ref=None, **kwargs):
        super().__init__(master, **kwargs)
        self.ide = ide_ref
        self.file_path = file_path
        self.on_change = on_change
        self.is_modified = False

        # Color Configuration
        self.colors = {
            str(Token.Keyword): "#C678DD",
            str(Token.Name.Function): "#61AFEF",
            str(Token.Name.Class): "#E5C07B",
            str(Token.String): "#98C379",
            str(Token.Comment): "#5C6370",
            str(Token.Number): "#D19A66",
            str(Token.Operator): "#56B6C2"
        }

        self.font = ("Consolas", 16)

        # Layout: [Line Numbers] [Editor]
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Line Number Gutter
        # We use a standard tk.Text because CTkTextbox doesn't allow such granular control easily
        self.line_numbers = tk.Text(self, width=4, padx=5, pady=5, 
                                   fg="#858585", bg="#1e1e1e", 
                                   font=self.font, borderwidth=0, highlightthickness=0,
                                   state="disabled", cursor="arrow")
        self.line_numbers.grid(row=0, column=0, sticky="ns")

        # Main Text Editor
        # We use the underlying tk text for better scroll synchronization
        self.textbox = ctk.CTkTextbox(self, font=self.font, corner_radius=0, 
                                     fg_color="#1e1e1e", text_color="#d4d4d4",
                                     undo=True, wrap="none")
        self.textbox.grid(row=0, column=1, sticky="nsew")
        
        # Configure Tags
        for token, hex_color in self.colors.items():
            self.textbox.tag_config(token, foreground=hex_color)
        
        self.textbox.tag_config("find", background="#4B3B00", foreground="white")

        self.load_file()
        
        # Bind events for synchronization and highlighting
        self.textbox.bind("<KeyRelease>", self.on_text_key_release)
        # Bind the underlying mousewheel to sync
        self.textbox._textbox.bind("<MouseWheel>", self.sync_scroll, add="+")
        self.textbox._textbox.bind("<Button-1>", self.sync_scroll, add="+")
        self.textbox._textbox.bind("<Key>", self.sync_scroll, add="+")
        self.textbox.bind("<Button-3>", self.show_context_menu)
        
        # Setup Context Menu
        self.context_menu = tk.Menu(self, tearoff=0, bg="#1e1e1e", fg="#d4d4d4", 
                                   activebackground="#007acc", activeforeground="white",
                                   borderwidth=0)
        self.context_menu.add_command(label="Explain Selection", command=lambda: self.trigger_ai("Explain this code section:"))
        self.context_menu.add_command(label="Refactor Selection", command=lambda: self.trigger_ai("Refactor this for better readability and efficiency:"))
        self.context_menu.add_command(label="Find Bugs", command=lambda: self.trigger_ai("Find any bugs or potential issues in this code:"))
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Comment / Uncomment", command=self.toggle_comment)
        self.context_menu.add_command(label="Duplicate Line", command=self.duplicate_selection)

    def load_file(self):
        try:
            with open(self.file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            self.textbox.delete("1.0", "end")
            self.textbox.insert("1.0", content)
            self.apply_highlighting()
            self.update_line_numbers()
            self.textbox.edit_modified(False)
            self.is_modified = False
        except Exception as e:
            self.textbox.insert("1.0", f"Error loading file: {e}")

    def sync_scroll(self, event=None):
        """Synchronize the line numbers scroll position with the editor."""
        fraction = self.textbox._textbox.yview()[0]
        self.line_numbers.yview_moveto(fraction)

    def update_line_numbers(self):
        line_count = int(self.textbox.index('end-1c').split('.')[0])
        lines_text = "\n".join(str(i) for i in range(1, line_count + 1))
        
        self.line_numbers.configure(state="normal")
        self.line_numbers.delete("1.0", "end")
        self.line_numbers.insert("1.0", lines_text)
        self.line_numbers.configure(state="disabled")
        self.sync_scroll()

    def on_text_key_release(self, event=None):
        # Mark as modified
        if not self.is_modified:
            self.is_modified = True
            if self.on_change:
                self.on_change(self.file_path, True)
        
        self.update_line_numbers()
        
        # Basic highlighting trigger
        if event and event.keysym in ("Return", "space", "Tab", "BackSpace", "Delete"):
            self.apply_highlighting()

    def apply_highlighting(self):
        code = self.textbox.get("1.0", "end-1c")
        try:
            lexer = lexers.get_lexer_for_filename(self.file_path)
        except pygments_util.ClassNotFound:
            return

        for tag in self.colors.keys():
            self.textbox.tag_remove(tag, "1.0", "end")

        offset = 0
        for token_type, value in lexer.get_tokens(code):
            token_str = str(token_type)
            if token_str in self.colors:
                start_idx = f"1.0 + {offset} chars"
                end_idx = f"1.0 + {offset + len(value)} chars"
                self.textbox.tag_add(token_str, start_idx, end_idx)
            offset += len(value)

    def toggle_comment(self):
        """Toggle single line comments using #."""
        try:
            try:
                sel_start = self.textbox.index("sel.first")
                sel_end = self.textbox.index("sel.last")
            except tk.TclError:
                idx = self.textbox.index("insert")
                sel_start = idx.split(".")[0] + ".0"
                sel_end = idx.split(".")[0] + ".end"

            start_line = int(sel_start.split(".")[0])
            end_line = int(sel_end.split(".")[0])

            if end_line > start_line and sel_end.split(".")[1] == "0":
                end_line -= 1

            should_uncomment = True
            for line_num in range(start_line, end_line + 1):
                line_content = self.textbox.get(f"{line_num}.0", f"{line_num}.end")
                if line_content.strip() and not line_content.strip().startswith("#"):
                    should_uncomment = False
                    break
            
            for line_num in range(start_line, end_line + 1):
                line_start = f"{line_num}.0"
                line_content = self.textbox.get(line_start, f"{line_num}.end")
                
                if should_uncomment:
                    comment_idx = line_content.find("#")
                    if comment_idx != -1:
                        # Remove # and potentially one space
                        self.textbox.delete(f"{line_num}.{comment_idx}", f"{line_num}.{comment_idx + 1}")
                        if line_content[comment_idx+1:comment_idx+2] == " ":
                            self.textbox.delete(f"{line_num}.{comment_idx + 1}")
                else:
                    self.textbox.insert(line_start, "# ")
            
            self.apply_highlighting()
            self.on_text_key_release() # Trigger modified state and line updates
        except Exception as e:
            print(f"Comment Error: {e}")

    def show_context_menu(self, event):
        self.context_menu.post(event.x_root, event.y_root)

    def trigger_ai(self, prompt_prefix):
        try:
            selected_text = self.textbox.get("sel.first", "sel.last").strip()
        except tk.TclError:
            selected_text = self.textbox.get("insert linestart", "insert lineend").strip()
        
        if not selected_text: return
        
        query = f"{prompt_prefix}\n\n```python\n{selected_text}\n```"
        if self.ide and hasattr(self.ide, "ai_sidebar"):
            sidebar = self.ide.ai_sidebar
            sidebar.entry.delete(0, "end")
            sidebar.entry.insert(0, query)
            sidebar.send_query()
            # Bring sidebar into view if it was hidden/minimized (not explicitly handled in layout yet)

    def find_text(self, query):
        self.textbox.tag_remove("find", "1.0", "end")
        if not query: return
        
        idx = "1.0"
        while True:
            idx = self.textbox._textbox.search(query, idx, nocase=True, stopindex="end")
            if not idx: break
            lastidx = f"{idx}+{len(query)}c"
            self.textbox.tag_add("find", idx, lastidx)
            idx = lastidx

    def duplicate_selection(self):
        try:
            try:
                sel_content = self.textbox.get("sel.first", "sel.last")
                self.textbox.insert("sel.last", sel_content)
            except tk.TclError:
                line_idx = self.textbox.index("insert").split(".")[0]
                line_content = self.textbox.get(f"{line_idx}.0", f"{line_idx}.end")
                self.textbox.insert(f"{line_idx}.end", "\n" + line_content)
            self.apply_highlighting()
            self.update_line_numbers()
        except Exception as e:
            print(f"Duplicate Error: {e}")

    def save_file(self):
        try:
            content = self.textbox.get("1.0", "end-1c")
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write(content)
            self.is_modified = False
            if self.on_change:
                self.on_change(self.file_path, False)
            self.apply_highlighting()
        except Exception as e:
            print(f"Error saving file: {e}")

    def set_zoom(self, zoom_level):
        """Scales fonts based on zoom level."""
        new_size = int(16 * zoom_level)
        self.font = ("Consolas", new_size)
        self.textbox.configure(font=self.font)
        self.line_numbers.configure(font=self.font, width=int(4 * zoom_level))
        # Force refresh highlighting since it relies on char offsets (though offsets shouldn't change, display might)
        self.apply_highlighting()
