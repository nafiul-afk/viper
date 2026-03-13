"""Multi-tab code editor widget with syntax highlighting.

Provides the CodeEditor frame containing a tabbed interface, gutter
with line numbers, regex-based Python syntax highlighting, inline
find bar, and content-hash based dirty tracking that avoids false
positives from tag operations.
"""

import tkinter as tk
from viper.theme import THEME
from viper.constants import (
    MONO_FONTS, find_font, build_patterns, PAIRS, DEFAULT_CODE
)


class CodeEditor(tk.Frame):
    """Tabbed code editor with syntax highlighting and dirty tracking.

    Manages multiple file buffers through a tab bar. Each tab stores
    its content, file path, cursor position, and modification state
    independently. Uses content hashing instead of Tkinter's unreliable
    <<Modified>> event to determine if a file has unsaved changes.
    """

    def __init__(self, parent):
        super().__init__(parent, bg=THEME["editor"])
        self._hl_job = None
        self._font_size = 12
        self.fm = find_font(MONO_FONTS, 12)
        self.fms = find_font(MONO_FONTS, 11)
        self.fus = find_font(("Inter", "Ubuntu", "sans-serif"), 9)
        self.fu = find_font(("Inter", "Ubuntu", "sans-serif"), 10)
        self.patterns = build_patterns()

        self.tabs = []
        self.active_tab = -1

        self._build_tab_bar()
        self._build_find_bar()
        self._build_editor_area()
        self._setup_tags()
        self._setup_binds()

        self.new_tab()
        self.text.focus_set()

    def _build_tab_bar(self):
        self.tab_bar = tk.Frame(self, bg=THEME["bg"], height=30)
        self.tab_bar.pack(side="top", fill="x")
        self.tab_bar.pack_propagate(False)

    def _build_find_bar(self):
        self.find_frame = tk.Frame(self, bg=THEME["find_bg"])
        tk.Label(self.find_frame, text="  Find:", font=self.fus,
                 bg=THEME["find_bg"], fg=THEME["dim"]).pack(side="left", padx=(8, 4))
        self.find_entry = tk.Entry(
            self.find_frame, bg=THEME["bg"], fg=THEME["fg"], font=self.fms,
            insertbackground=THEME["cursor"], highlightthickness=0, bd=0,
            width=30, selectbackground=THEME["sel"])
        self.find_entry.pack(side="left", padx=4, pady=5)
        for label, cmd in [("  Prev  ", lambda: self.find_text(-1)),
                           ("  Next  ", lambda: self.find_text(1)),
                           ("  ✕  ", self.toggle_find)]:
            b = tk.Button(self.find_frame, text=label, command=cmd, font=self.fus,
                          bg=THEME["btn"], fg=THEME["fg"], relief="flat", bd=0,
                          activebackground=THEME["btn_hover"], cursor="hand2",
                          highlightthickness=0)
            b.pack(side="left", padx=2, pady=5)
        self.find_count_label = tk.Label(self.find_frame, text="", font=self.fus,
                                         bg=THEME["find_bg"], fg=THEME["dim"])
        self.find_count_label.pack(side="left", padx=8)
        self.find_entry.bind("<Return>", lambda e: self.find_text(1))
        self.find_entry.bind("<Escape>", lambda e: self.toggle_find())

    def _build_editor_area(self):
        area = tk.Frame(self, bg=THEME["editor"])
        area.pack(fill="both", expand=True)

        self.gutter = tk.Canvas(area, width=52, bg=THEME["gutter_bg"],
                                highlightthickness=0, bd=0)
        self.gutter.pack(side="left", fill="y")

        vscroll = tk.Scrollbar(area, orient="vertical", bg=THEME["scrollbar"],
                               troughcolor=THEME["scrollbar"], highlightthickness=0,
                               bd=0, width=10)
        vscroll.pack(side="right", fill="y")

        self.text = tk.Text(
            area, bg=THEME["editor"], fg=THEME["fg"],
            insertbackground=THEME["cursor"], selectbackground=THEME["sel"],
            selectforeground="", font=self.fm, wrap="none", undo=True,
            autoseparators=True, maxundo=-1, padx=10, pady=10,
            highlightthickness=0, bd=0, relief="flat", tabs=("4c",),
            spacing1=2, spacing3=2, insertwidth=2)
        self.text.pack(side="left", fill="both", expand=True)

        self.text.configure(yscrollcommand=lambda *a: (vscroll.set(*a), self.update_line_numbers()))
        vscroll.configure(command=lambda *a: (self.text.yview(*a), self.update_line_numbers()))

        hscroll = tk.Scrollbar(self, orient="horizontal", bg=THEME["scrollbar"],
                               troughcolor=THEME["scrollbar"], highlightthickness=0,
                               bd=0, width=7)
        hscroll.pack(side="bottom", fill="x")
        self.text.configure(xscrollcommand=hscroll.set)
        hscroll.configure(command=self.text.xview)

    def _setup_tags(self):
        for tag, key in [("kw", "kw"), ("builtin", "builtin"), ("string", "string"),
                         ("comment", "comment"), ("number", "number"),
                         ("decorator", "decorator"), ("function", "function"),
                         ("classname", "classname"), ("selfcls", "selfcls")]:
            self.text.tag_configure(tag, foreground=THEME[key])
        self.text.tag_configure("curline", background=THEME["curline"])
        self.text.tag_configure("find_hl", background=THEME["find_hl"])
        self.text.tag_lower("curline")

    def _setup_binds(self):
        self.text.bind("<KeyRelease>", self._on_key_release)
        self.text.bind("<ButtonRelease-1>", self._on_click)
        self.text.bind("<Configure>", lambda e: self.after(10, self.update_line_numbers))
        self.text.bind("<Tab>", self._handle_tab)
        self.text.bind("<Shift-Tab>", self._handle_untab)
        self.text.bind("<Return>", self._handle_return)
        self.text.bind("<Control-d>", self._handle_duplicate)
        self.text.bind("<Control-slash>", self._handle_toggle_comment)
        for keysym in ["parenleft", "bracketleft", "braceleft",
                       "quotedbl", "apostrophe"]:
            self.text.bind(f"<KeyPress-{keysym}>", self._handle_auto_close)

    def _on_click(self, event=None):
        self.text.focus_set()
        self.highlight_current_line()
        self.after(1, self.update_line_numbers)

    def _on_key_release(self, event=None):
        self.highlight_current_line()
        self._check_and_notify()
        self.schedule_highlight()
        self.after(1, self.update_line_numbers)

    def _check_and_notify(self):
        if self.active_tab < 0 or self.active_tab >= len(self.tabs):
            return
        tab = self.tabs[self.active_tab]
        h = hash(self.text.get("1.0", "end-1c"))
        new_mod = (h != tab["clean_hash"])
        if new_mod != tab["modified"]:
            tab["modified"] = new_mod
            self._refresh_tab_bar()
            if self.on_change:
                self.on_change()

    on_change = None

    @property
    def modified(self):
        if 0 <= self.active_tab < len(self.tabs):
            return self.tabs[self.active_tab]["modified"]
        return False

    def new_tab(self, name="untitled.py", path=None, content=None):
        if content is None:
            content = DEFAULT_CODE if len(self.tabs) == 0 else ""
        tab = {
            "name": name,
            "path": path,
            "content": content,
            "modified": False,
            "clean_hash": hash(content),
            "cursor": "1.0",
        }
        self.tabs.append(tab)
        self._switch_to(len(self.tabs) - 1)
        return len(self.tabs) - 1

    def open_in_tab(self, path, content):
        import os
        name = os.path.basename(path)
        for i, tab in enumerate(self.tabs):
            if tab["path"] == path:
                self._switch_to(i)
                return i
        return self.new_tab(name=name, path=path, content=content)

    def _save_current_buffer(self):
        if 0 <= self.active_tab < len(self.tabs):
            tab = self.tabs[self.active_tab]
            tab["content"] = self.text.get("1.0", "end-1c")
            tab["cursor"] = self.text.index("insert")

    def _switch_to(self, index):
        if index == self.active_tab and self.text.get("1.0", "end-1c").strip():
            return
        if self.active_tab >= 0 and self.active_tab < len(self.tabs):
            self._save_current_buffer()
        self.active_tab = index
        tab = self.tabs[index]
        self.text.delete("1.0", "end")
        if tab["content"]:
            self.text.insert("1.0", tab["content"])
        self.text.mark_set("insert", tab["cursor"])
        self.text.see(tab["cursor"])
        self.text.edit_reset()
        self._refresh_tab_bar()
        self.schedule_highlight()
        self.text.focus_set()

    def close_tab(self, index):
        if len(self.tabs) <= 1:
            return False
        tab = self.tabs[index]
        if tab["modified"]:
            from tkinter import messagebox
            r = messagebox.askyesnocancel("Viper", f"Save '{tab['name']}' before closing?")
            if r is None:
                return False
            if r and self.on_save_tab:
                self.on_save_tab(index)
        self.tabs.pop(index)
        if self.active_tab >= len(self.tabs):
            self.active_tab = len(self.tabs) - 1
        elif self.active_tab > index:
            self.active_tab -= 1
        self.active_tab = max(0, min(self.active_tab, len(self.tabs) - 1))
        self._switch_to(self.active_tab)
        return True

    on_save_tab = None

    def mark_clean(self):
        if 0 <= self.active_tab < len(self.tabs):
            tab = self.tabs[self.active_tab]
            tab["clean_hash"] = hash(self.text.get("1.0", "end-1c"))
            tab["modified"] = False
            self._refresh_tab_bar()

    def get_active_tab(self):
        if 0 <= self.active_tab < len(self.tabs):
            return self.tabs[self.active_tab]
        return None

    def _refresh_tab_bar(self):
        for w in self.tab_bar.winfo_children():
            w.destroy()
        for i, tab in enumerate(self.tabs):
            is_active = (i == self.active_tab)
            mod = " •" if tab["modified"] else ""
            name = f"  {tab['name']}{mod}  "
            bg = THEME["editor"] if is_active else THEME["bg"]
            fg = THEME["fg"] if is_active else THEME["dim"]

            frame = tk.Frame(self.tab_bar, bg=bg)
            frame.pack(side="left", pady=(3, 0), padx=(2, 0))

            lbl = tk.Label(frame, text=name, font=self.fu, bg=bg, fg=fg,
                           cursor="hand2", pady=3, padx=2)
            lbl.pack(side="left")
            lbl.bind("<Button-1>", lambda e, idx=i: self._switch_to(idx))

            if len(self.tabs) > 1:
                close = tk.Label(frame, text=" ✕", font=self.fus, bg=bg,
                                 fg=THEME["dim"], cursor="hand2", pady=3)
                close.pack(side="left")
                close.bind("<Button-1>", lambda e, idx=i: self.close_tab(idx))

    def get_cursor_position(self):
        ln, col = self.text.index("insert").split(".")
        return int(ln), int(col) + 1

    def schedule_highlight(self):
        if self._hl_job:
            self.after_cancel(self._hl_job)
        self._hl_job = self.after(80, self._do_highlight)

    def _do_highlight(self):
        self._hl_job = None
        code = self.text.get("1.0", "end-1c")
        for name, _ in self.patterns:
            self.text.tag_remove(name, "1.0", "end")
        for name, pat in self.patterns:
            for m in pat.finditer(code):
                self.text.tag_add(name, f"1.0+{m.start()}c", f"1.0+{m.end()}c")
        self.text.tag_raise("string")
        self.text.tag_raise("comment")
        self.highlight_current_line()

    def highlight_current_line(self):
        self.text.tag_remove("curline", "1.0", "end")
        self.text.tag_add("curline", "insert linestart", "insert lineend+1c")

    def update_line_numbers(self):
        self.gutter.delete("all")
        top = self.text.index("@0,0")
        bot = self.text.index(f"@0,{self.text.winfo_height()}")
        first, last = int(top.split(".")[0]), int(bot.split(".")[0])
        total = int(self.text.index("end-1c").split(".")[0])
        w = max(len(str(total)) * 9 + 22, 52)
        self.gutter.configure(width=w)
        cur_line = int(self.text.index("insert").split(".")[0])
        for i in range(first, last + 1):
            info = self.text.dlineinfo(f"{i}.0")
            if info:
                color = THEME["gutter_active"] if i == cur_line else THEME["gutter_fg"]
                self.gutter.create_text(w - 12, info[1] + 2, anchor="ne",
                                        text=str(i), font=self.fm, fill=color)

    def set_font_size(self, size):
        self._font_size = max(8, min(28, size))
        self.fm = find_font(MONO_FONTS, self._font_size)
        self.fms = find_font(MONO_FONTS, self._font_size - 1)
        self.text.configure(font=self.fm)
        self.update_line_numbers()

    def toggle_find(self):
        if self.find_frame.winfo_viewable():
            self.find_frame.pack_forget()
            self.text.tag_remove("find_hl", "1.0", "end")
            self.text.focus_set()
        else:
            children = self.winfo_children()
            idx = 1 if len(children) > 1 else 0
            self.find_frame.pack(before=children[idx], fill="x")
            self.find_entry.focus_set()
            self.find_entry.select_range(0, "end")

    def find_text(self, direction=1):
        query = self.find_entry.get()
        if not query:
            return
        self.text.tag_remove("find_hl", "1.0", "end")
        pos, count = "1.0", 0
        while True:
            pos = self.text.search(query, pos, "end", nocase=True)
            if not pos:
                break
            end = f"{pos}+{len(query)}c"
            self.text.tag_add("find_hl", pos, end)
            count += 1
            pos = end
        self.find_count_label.configure(text=f"{count} found" if count else "No results")
        if not count:
            return
        cur = self.text.index("insert")
        if direction == 1:
            found = self.text.search(query, cur, "end", nocase=True)
            if not found:
                found = self.text.search(query, "1.0", "end", nocase=True)
        else:
            found = self.text.search(query, cur + "-1c", "1.0", backwards=True, nocase=True)
            if not found:
                found = self.text.search(query, "end", "1.0", backwards=True, nocase=True)
        if found:
            self.text.mark_set("insert", found)
            self.text.see(found)

    def _handle_tab(self, event):
        if self.text.tag_ranges("sel"):
            s = int(self.text.index("sel.first").split(".")[0])
            e = int(self.text.index("sel.last").split(".")[0])
            for i in range(s, e + 1):
                self.text.insert(f"{i}.0", "    ")
        else:
            self.text.insert("insert", "    ")
        return "break"

    def _handle_untab(self, event):
        if self.text.tag_ranges("sel"):
            s = int(self.text.index("sel.first").split(".")[0])
            e = int(self.text.index("sel.last").split(".")[0])
            for i in range(s, e + 1):
                if self.text.get(f"{i}.0", f"{i}.4") == "    ":
                    self.text.delete(f"{i}.0", f"{i}.4")
        else:
            ls = self.text.index("insert linestart")
            if self.text.get(ls, f"{ls}+4c") == "    ":
                self.text.delete(ls, f"{ls}+4c")
        return "break"

    def _handle_return(self, event):
        line = self.text.get("insert linestart", "insert")
        indent = ""
        for ch in line:
            if ch in (" ", "\t"):
                indent += ch
            else:
                break
        if line.rstrip().endswith(":"):
            indent += "    "
        self.text.insert("insert", "\n" + indent)
        self.text.see("insert")
        return "break"

    def _handle_auto_close(self, event):
        ch = event.char
        if ch not in PAIRS:
            return
        closing = PAIRS[ch]
        if self.text.tag_ranges("sel"):
            selected = self.text.get("sel.first", "sel.last")
            self.text.delete("sel.first", "sel.last")
            self.text.insert("insert", ch + selected + closing)
            return "break"
        if ch in ('"', "'"):
            after = self.text.get("insert", "insert+1c")
            if after == ch:
                self.text.mark_set("insert", "insert+1c")
                return "break"
        self.text.insert("insert", ch + closing)
        self.text.mark_set("insert", "insert-1c")
        return "break"

    def _handle_duplicate(self, event):
        line = self.text.get("insert linestart", "insert lineend")
        self.text.insert("insert lineend", "\n" + line)
        return "break"

    def _handle_toggle_comment(self, event):
        if self.text.tag_ranges("sel"):
            s = int(self.text.index("sel.first").split(".")[0])
            e = int(self.text.index("sel.last").split(".")[0])
        else:
            s = e = int(self.text.index("insert").split(".")[0])
        lines = [self.text.get(f"{i}.0", f"{i}.end") for i in range(s, e + 1)]
        commenting = any(not l.lstrip().startswith("#") for l in lines if l.strip())
        for i in range(s, e + 1):
            lt = self.text.get(f"{i}.0", f"{i}.end")
            if commenting:
                self.text.insert(f"{i}.0", "# ")
            elif lt.lstrip().startswith("# "):
                idx = lt.index("# ")
                self.text.delete(f"{i}.{idx}", f"{i}.{idx+2}")
            elif lt.lstrip().startswith("#"):
                idx = lt.index("#")
                self.text.delete(f"{i}.{idx}", f"{i}.{idx+1}")
        return "break"
