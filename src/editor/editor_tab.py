import customtkinter as ctk
import os
import tkinter as tk
import keyword
import re
from pygments import lexers, util as pygments_util
from pygments.token import Token
from src.editor.minimap import Minimap

class EditorTab(ctk.CTkFrame):
    def __init__(self, master, file_path, on_change=None, ide_ref=None, **kwargs):
        super().__init__(master, **kwargs)
        self.ide = ide_ref
        self.file_path = file_path
        self.on_change = on_change
        self.is_modified = False
        
        # Performance/Feature Timers
        self.highlight_timer = None
        self.autosave_timer = None
        self.ghost_timer = None

        # State
        self.autocomplete_active = False
        self.autocomplete_listbox = None
        self.autocomplete_window = None
        self.ghost_text = ""
        self.ghost_index = ""

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

        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)
        self.grid_rowconfigure(0, weight=1)

        self.line_numbers = tk.Text(self, width=4, padx=5, pady=5, fg="#858585", bg="#1e1e1e", font=self.font, borderwidth=0, highlightthickness=0, state="disabled", cursor="arrow")
        self.line_numbers.grid(row=0, column=0, sticky="ns")

        self.textbox = ctk.CTkTextbox(self, font=self.font, corner_radius=0, fg_color="#1e1e1e", text_color="#d4d4d4", undo=True, wrap="none")
        self.textbox.grid(row=0, column=1, sticky="nsew")
        
        self.minimap = Minimap(self, self.textbox, width=80)
        self.minimap.grid(row=0, column=2, sticky="ns")
        
        # Tags
        for token, hex_color in self.colors.items(): self.textbox.tag_config(token, foreground=hex_color)
        self.textbox.tag_config("find", background="#4B3B00", foreground="white")
        self.textbox.tag_config("ghost", foreground="#5c6370") # Gray ghost text

        self.load_file()
        
        # Bindings
        self.textbox.bind("<KeyRelease>", self.on_text_key_release)
        self.textbox.bind("<KeyPress>", self.on_text_key_press)
        self.textbox._textbox.bind("<MouseWheel>", self.sync_scroll, add="+")
        self.textbox._textbox.bind("<Button-1>", self.sync_scroll, add="+")
        self.textbox._textbox.bind("<Key>", self.sync_scroll, add="+")
        self.textbox.bind("<Button-3>", self.show_context_menu)

    def load_file(self):
        try:
            with open(self.file_path, "r", encoding="utf-8", errors="ignore") as f: content = f.read()
            self.textbox.delete("1.0", "end")
            self.textbox.insert("1.0", content)
            self.apply_highlighting()
            self.update_line_numbers()
            self.minimap.trigger_update()
            self.textbox.edit_modified(False)
            self.is_modified = False
        except Exception as e: self.textbox.insert("1.0", f"Error loading file: {e}")

    def sync_scroll(self, event=None):
        fraction = self.textbox._textbox.yview()[0]
        self.line_numbers.yview_moveto(fraction)
        self.minimap.update_view_rect()

    def update_line_numbers(self):
        line_count = int(self.textbox.index('end-1c').split('.')[0])
        lines_text = "\n".join(str(i) for i in range(1, line_count + 1))
        self.line_numbers.configure(state="normal")
        self.line_numbers.delete("1.0", "end")
        self.line_numbers.insert("1.0", lines_text)
        self.line_numbers.configure(state="disabled")
        self.sync_scroll()

    def on_text_key_press(self, event):
        if self.autocomplete_active:
            if event.keysym in ("Up", "Down"): self.autocomplete_listbox.focus_set(); return "break"
            if event.keysym in ("Return", "Tab"): self.complete_text(); return "break"
            if event.keysym == "Escape": self.hide_autocomplete(); return "break"
            
        # Ghost Text Acceptance
        if self.ghost_text and event.keysym == "Tab":
            self.accept_ghost()
            return "break"
        elif self.ghost_text:
            self.clear_ghost()

    def on_text_key_release(self, event=None):
        if not self.is_modified:
            self.is_modified = True
            if self.on_change: self.on_change(self.file_path, True)
        
        self.update_line_numbers()
        self.minimap.trigger_update()
        
        if self.highlight_timer: self.after_cancel(self.highlight_timer)
        self.highlight_timer = self.after(500, self.apply_highlighting)
        
        if self.autosave_timer: self.after_cancel(self.autosave_timer)
        if self.is_modified: self.autosave_timer = self.after(3000, self.save_file)
            
        if event and event.keysym not in ("Up", "Down", "Left", "Right", "Return", "Tab", "Escape", "Shift_L", "Shift_R", "Control_L", "Control_R"):
            self.show_autocomplete(event)
            # Trigger Ghost Text after a delay
            if self.ghost_timer: self.after_cancel(self.ghost_timer)
            self.ghost_timer = self.after(1000, self.trigger_ghost)

    def trigger_ghost(self):
        """Requests AI completion for ghost text."""
        if not self.ide or not hasattr(self.ide, 'ai_sidebar'): return
        
        cursor_idx = self.textbox.index("insert")
        # Get context (last 500 chars)
        context = self.textbox.get("1.0", cursor_idx)[-500:]
        
        self.ide.ai_sidebar.ollama.complete_code(context, self.show_ghost)

    def show_ghost(self, text):
        if not text or not text.strip(): return
        self.ghost_text = text
        self.ghost_index = self.textbox.index("insert")
        self.textbox.insert(self.ghost_index, text, "ghost")
        # Move cursor back to before ghost text
        self.textbox.mark_set("insert", self.ghost_index)

    def clear_ghost(self):
        if self.ghost_text:
            # We must be careful not to delete user typed text
            self.textbox.tag_remove("ghost", "1.0", "end")
            # This is a bit naive but works for simple cases
            start = self.ghost_index
            end = f"{start} + {len(self.ghost_text)}c"
            # Verify it's actually our ghost text
            if self.textbox.get(start, end) == self.ghost_text:
                self.textbox.delete(start, end)
            self.ghost_text = ""

    def accept_ghost(self):
        if self.ghost_text:
            self.textbox.tag_remove("ghost", "1.0", "end")
            # Move cursor to end of accepted text
            new_idx = f"{self.ghost_index} + {len(self.ghost_text)}c"
            self.textbox.mark_set("insert", new_idx)
            self.ghost_text = ""
            self.apply_highlighting()

    def show_autocomplete(self, event):
        cursor_idx = self.textbox.index("insert")
        line_start = f"{cursor_idx} linestart"
        text_before_cursor = self.textbox.get(line_start, cursor_idx)
        match = re.search(r"(\w+)$", text_before_cursor)
        if not match: self.hide_autocomplete(); return
        word_prefix = match.group(1)
        if len(word_prefix) < 1: self.hide_autocomplete(); return
        suggestions = self.get_suggestions(word_prefix)
        if not suggestions: self.hide_autocomplete(); return
        if not self.autocomplete_window:
            self.autocomplete_window = tk.Toplevel(self)
            self.autocomplete_window.wm_overrideredirect(True)
            self.autocomplete_listbox = tk.Listbox(self.autocomplete_window, bg="#2d2d2d", fg="#d4d4d4", font=self.font, borderwidth=0, highlightthickness=1, highlightbackground="#404040", selectbackground="#007acc")
            self.autocomplete_listbox.pack()
            self.autocomplete_listbox.bind("<Double-Button-1>", lambda e: self.complete_text())
            self.autocomplete_listbox.bind("<Return>", lambda e: self.complete_text())
            self.autocomplete_listbox.bind("<Escape>", lambda e: self.hide_autocomplete())
        self.autocomplete_listbox.delete(0, "end")
        for s in suggestions: self.autocomplete_listbox.insert("end", s)
        self.autocomplete_listbox.selection_set(0)
        bbox = self.textbox._textbox.bbox(cursor_idx)
        if bbox:
            x = self.textbox.winfo_rootx() + bbox[0] + 40
            y = self.textbox.winfo_rooty() + bbox[1] + bbox[3]
            self.autocomplete_window.wm_geometry(f"+{x}+{y}")
            self.autocomplete_active = True
            self.autocomplete_window.deiconify(); self.autocomplete_window.lift()

    def hide_autocomplete(self):
        if self.autocomplete_window: self.autocomplete_window.withdraw()
        self.autocomplete_active = False

    def get_suggestions(self, prefix):
        words = set()
        if self.file_path.endswith(".py"):
            words.update(keyword.kwlist)
            words.update(["print", "len", "range", "enumerate", "zip", "dict", "list", "set", "int", "str", "float"])
        content = self.textbox.get("1.0", "end")
        words.update(re.findall(r"\b\w+\b", content))
        matches = [w for w in words if w.startswith(prefix) and w != prefix]
        return sorted(list(matches))[:10]

    def complete_text(self):
        if not self.autocomplete_active: return
        selection = self.autocomplete_listbox.get(tk.ACTIVE)
        if selection:
            cursor_idx = self.textbox.index("insert")
            line_start = f"{cursor_idx} linestart"
            text_before_cursor = self.textbox.get(line_start, cursor_idx)
            match = re.search(r"(\w+)$", text_before_cursor)
            if match:
                start_idx = f"{cursor_idx} - {len(match.group(1))}c"
                self.textbox.delete(start_idx, cursor_idx); self.textbox.insert(start_idx, selection)
        self.hide_autocomplete(); self.apply_highlighting()

    def apply_highlighting(self):
        code = self.textbox.get("1.0", "end-1c")
        try: lexer = lexers.get_lexer_for_filename(self.file_path)
        except pygments_util.ClassNotFound: return
        for tag in self.colors.keys(): self.textbox.tag_remove(tag, "1.0", "end")
        offset = 0
        for token_type, value in lexer.get_tokens(code):
            token_str = str(token_type)
            if token_str in self.colors:
                start_idx = f"1.0 + {offset} chars"; end_idx = f"1.0 + {offset + len(value)} chars"
                self.textbox.tag_add(token_str, start_idx, end_idx)
            offset += len(value)

    def toggle_comment(self):
        try:
            try: sel_start = self.textbox.index("sel.first"); sel_end = self.textbox.index("sel.last")
            except tk.TclError:
                idx = self.textbox.index("insert")
                sel_start = idx.split(".")[0] + ".0"; sel_end = idx.split(".")[0] + ".end"
            start_line = int(sel_start.split(".")[0]); end_line = int(sel_end.split(".")[0])
            if end_line > start_line and sel_end.split(".")[1] == "0": end_line -= 1
            should_uncomment = True
            for line_num in range(start_line, end_line + 1):
                line_content = self.textbox.get(f"{line_num}.0", f"{line_num}.end")
                if line_content.strip() and not line_content.strip().startswith("#"): should_uncomment = False; break
            for line_num in range(start_line, end_line + 1):
                line_start = f"{line_num}.0"; line_content = self.textbox.get(line_start, f"{line_num}.end")
                if should_uncomment:
                    comment_idx = line_content.find("#")
                    if comment_idx != -1:
                        self.textbox.delete(f"{line_num}.{comment_idx}", f"{line_num}.{comment_idx + 1}")
                        if line_content[comment_idx+1:comment_idx+2] == " ": self.textbox.delete(f"{line_num}.{comment_idx + 1}")
                else: self.textbox.insert(line_start, "# ")
            self.apply_highlighting(); self.on_text_key_release()
        except Exception as e: print(f"Comment Error: {e}")

    def show_context_menu(self, event): self.context_menu.post(event.x_root, event.y_root)

    def trigger_ai(self, prompt_prefix):
        try: selected_text = self.textbox.get("sel.first", "sel.last").strip()
        except tk.TclError: selected_text = self.textbox.get("insert linestart", "insert lineend").strip()
        if not selected_text: return
        query = f"{prompt_prefix}\n\n```python\n{selected_text}\n```"
        if self.ide and hasattr(self.ide, "ai_sidebar"):
            sidebar = self.ide.ai_sidebar; sidebar.entry.delete(0, "end"); sidebar.entry.insert(0, query); sidebar.send_query()

    def find_text(self, query):
        self.textbox.tag_remove("find", "1.0", "end")
        if not query: return
        idx = "1.0"
        while True:
            idx = self.textbox._textbox.search(query, idx, nocase=True, stopindex="end")
            if not idx: break
            lastidx = f"{idx}+{len(query)}c"; self.textbox.tag_add("find", idx, lastidx); idx = lastidx

    def duplicate_selection(self):
        try:
            try: sel_content = self.textbox.get("sel.first", "sel.last"); self.textbox.insert("sel.last", sel_content)
            except tk.TclError:
                line_idx = self.textbox.index("insert").split(".")[0]; line_content = self.textbox.get(f"{line_idx}.0", f"{line_idx}.end")
                self.textbox.insert(f"{line_idx}.end", "\n" + line_content)
            self.apply_highlighting(); self.update_line_numbers()
        except Exception as e: print(f"Duplicate Error: {e}")

    def save_file(self):
        if not self.is_modified: return
        try:
            content = self.textbox.get("1.0", "end-1c")
            with open(self.file_path, "w", encoding="utf-8") as f: f.write(content)
            self.is_modified = False
            if self.on_change: self.on_change(self.file_path, False)
            self.apply_highlighting()
            if self.autosave_timer: self.after_cancel(self.autosave_timer); self.autosave_timer = None
        except Exception as e: print(f"Error saving file: {e}")

    def set_zoom(self, zoom_level):
        new_size = int(16 * zoom_level); self.font = ("Consolas", new_size); self.textbox.configure(font=self.font)
        self.line_numbers.configure(font=self.font, width=int(4 * zoom_level)); self.apply_highlighting()
