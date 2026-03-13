import tkinter as tk
from viper.theme import THEME
from viper.constants import MONO_FONTS, find_font


class Terminal(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=THEME["term"])
        self.cmd_history = []
        self.cmd_index = 0
        self.on_command = None
        self.on_input = None

        self.fms = find_font(MONO_FONTS, 11)
        self.fus = find_font(("Inter","Ubuntu","sans-serif"), 9)

        self._build_header()
        self._build_output()
        self._build_input()

        self.write("Viper Terminal\n", "sys")
        self.write("Type Python expressions or pip install <package>\n\n", "echo")

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
            yscrollcommand=scroll.set, selectbackground=THEME["sel"])
        self.output.pack(side="top", fill="both", expand=True)
        scroll.configure(command=self.output.yview)

        for tag, color in [("out", THEME["fg"]), ("err", THEME["red"]),
                           ("sys", THEME["accent"]), ("prompt", THEME["comment"]),
                           ("echo", THEME["dim"])]:
            self.output.tag_configure(tag, foreground=color)

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

    def write(self, text, tag="out"):
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
