"""Integrated terminal widget with inline process I/O.

Provides a Terminal frame with a read-only output area that switches
to editable mode when a subprocess is running, allowing the user to
type input directly next to the prompt — just like a real terminal.
"""

import tkinter as tk
from viper.theme import THEME
from viper.constants import MONO_FONTS, find_font


class Terminal(tk.Frame):
    """Terminal widget with inline stdin support for running processes."""

    def __init__(self, parent):
        super().__init__(parent, bg=THEME["term"])
        self.cmd_history = []
        self.cmd_index = 0
        self.on_command = None
        self.on_input = None
        self._process_mode = False

        self.fms = find_font(MONO_FONTS, 11)
        self.fus = find_font(("Inter", "Ubuntu", "sans-serif"), 9)

        self._build_header()
        self._build_input()
        self._build_output()

        self.write("Viper Terminal\n", "sys")
        self.write("Type Python expressions or pip install <package>\n\n", "echo")

    # ── UI Construction ───────────────────────────────────────

    def _build_header(self):
        header = tk.Frame(self, bg=THEME["bg"], height=28)
        header.pack(side="top", fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="  TERMINAL", font=self.fus,
                 bg=THEME["bg"], fg=THEME["dim"]).pack(side="left")

    def _build_output(self):
        scroll = tk.Scrollbar(self, orient="vertical", bg=THEME["scrollbar"],
                              troughcolor=THEME["scrollbar"], highlightthickness=0,
                              bd=0, width=10)
        scroll.pack(side="right", fill="y")

        self.output = tk.Text(
            self, bg=THEME["term"], fg=THEME["fg"], font=self.fms,
            wrap="word", state="disabled", cursor="arrow",
            highlightthickness=0, bd=0, padx=12, pady=8,
            yscrollcommand=scroll.set, selectbackground=THEME["sel"],
            insertwidth=2)
        self.output.pack(side="top", fill="both", expand=True)
        scroll.configure(command=self.output.yview)

        for tag, color in [("out", THEME["fg"]), ("err", THEME["red"]),
                           ("sys", THEME["accent"]), ("prompt", THEME["comment"]),
                           ("echo", THEME["dim"])]:
            self.output.tag_configure(tag, foreground=color)

        # Inline input bindings (active only in process mode)
        self.output.bind("<Key>", self._on_output_key)
        self.output.bind("<Return>", self._on_output_return)
        self.output.bind("<BackSpace>", self._on_output_backspace)

    def _build_input(self):
        tk.Frame(self, bg=THEME["border"], height=1).pack(side="bottom", fill="x")
        frame = tk.Frame(self, bg=THEME["term"])
        frame.pack(side="bottom", fill="x")

        tk.Label(frame, text="  ›", font=self.fms,
                 bg=THEME["term"], fg=THEME["accent"]).pack(side="left")

        self.entry = tk.Entry(
            frame, bg=THEME["term"], fg=THEME["fg"], font=self.fms,
            insertbackground=THEME["cursor"], highlightthickness=0, bd=0,
            relief="flat", selectbackground=THEME["sel"])
        self.entry.pack(side="left", fill="x", expand=True, padx=(4, 10), pady=7)

        self.entry.bind("<Return>", self._on_enter)
        self.entry.bind("<Up>", self._history_prev)
        self.entry.bind("<Down>", self._history_next)

    # ── Process Mode (inline input in the output area) ────────

    def start_process_mode(self):
        """Enable inline input — output area becomes editable at the end."""
        self._process_mode = True
        self.output.configure(state="normal", cursor="xterm",
                              insertbackground=THEME["cursor"])
        self.output.mark_set("input_start", "end-1c")
        self.output.mark_gravity("input_start", "left")
        self.output.mark_set("insert", "end-1c")
        self.output.focus_set()

    def stop_process_mode(self):
        """Disable inline input — output area goes back to read-only."""
        self._process_mode = False
        self.output.configure(state="disabled", cursor="arrow")

    def _on_output_key(self, event):
        """Gate all keystrokes: allow edits only in process mode, only after the mark."""
        if not self._process_mode:
            # Allow Ctrl+C for copy
            if event.state & 0x4 and event.keysym.lower() == "c":
                return
            return "break"

        # Let Return / Backspace go to their dedicated handlers
        if event.keysym in ("Return", "BackSpace"):
            return

        # Allow modifier shortcuts (copy, paste, select-all)
        if event.state & 0x4:
            return

        # Allow pure navigation / modifier keys
        if event.keysym in ("Left", "Right", "Up", "Down", "Home", "End",
                            "Shift_L", "Shift_R", "Control_L", "Control_R",
                            "Alt_L", "Alt_R", "Caps_Lock", "Tab",
                            "Delete", "Insert", "Escape"):
            return

        # Printable character — make sure cursor is in the editable zone
        if not event.char:
            return
        if self.output.compare("insert", "<", "input_start"):
            self.output.mark_set("insert", "end-1c")

    def _on_output_backspace(self, event):
        """Block backspace if cursor is at or before the input boundary."""
        if not self._process_mode:
            return "break"
        if self.output.compare("insert", "<=", "input_start"):
            return "break"

    def _on_output_return(self, event):
        """Grab the user's typed text, send it to the process, and advance the mark."""
        if not self._process_mode:
            return "break"
        user_input = self.output.get("input_start", "end-1c")
        self.output.insert("end-1c", "\n")
        self.output.mark_set("input_start", "end-1c")
        self.output.mark_set("insert", "end-1c")
        self.output.see("end")
        if self.on_input:
            self.on_input(user_input)
        return "break"

    # ── Entry Bar (bottom prompt for expressions / pip) ───────

    def _on_enter(self, event):
        cmd = self.entry.get().strip()
        self.entry.delete(0, "end")
        if not cmd:
            return
        self.cmd_history.append(cmd)
        self.cmd_index = len(self.cmd_history)
        if self.on_command:
            self.on_command(cmd)

    def _history_prev(self, event):
        if self.cmd_history and self.cmd_index > 0:
            self.cmd_index -= 1
            self.entry.delete(0, "end")
            self.entry.insert(0, self.cmd_history[self.cmd_index])
        return "break"

    def _history_next(self, event):
        if self.cmd_index < len(self.cmd_history) - 1:
            self.cmd_index += 1
            self.entry.delete(0, "end")
            self.entry.insert(0, self.cmd_history[self.cmd_index])
        elif self.cmd_index == len(self.cmd_history) - 1:
            self.cmd_index = len(self.cmd_history)
            self.entry.delete(0, "end")
        return "break"

    # ── Output Helpers ────────────────────────────────────────

    def write(self, text, tag="out"):
        """Append program output to the terminal.

        In process mode the text is inserted *before* any pending user
        input so that program output and user input never get mixed up.
        """
        if self._process_mode:
            # Temporarily remove any text the user has already typed
            user_text = self.output.get("input_start", "end-1c")
            if user_text:
                self.output.delete("input_start", "end-1c")
            # Append program output
            self.output.insert("end-1c", text, tag)
            # Advance the mark to *after* the new output
            self.output.mark_set("input_start", "end-1c")
            # Put user's pending text back
            if user_text:
                self.output.insert("end-1c", user_text)
            self.output.mark_set("insert", "end-1c")
        else:
            self.output.configure(state="normal")
            self.output.insert("end", text, tag)
            self.output.configure(state="disabled")
        self.output.see("end")

    def clear(self):
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.configure(state="disabled")

    def set_font_size(self, size):
        self.fms = find_font(MONO_FONTS, size)
        self.output.configure(font=self.fms)
        self.entry.configure(font=self.fms)
