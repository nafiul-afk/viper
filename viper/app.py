import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess, threading, os, sys, queue, tempfile

from viper import __version__
from viper.theme import THEME
from viper.constants import UI_FONTS, find_font
from viper.editor import CodeEditor
from viper.terminal import Terminal


class Viper(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Viper")
        self.geometry("1100x750")
        self.configure(bg=THEME["bg"])
        self.minsize(640, 420)

        self.process = None
        self._output_queue = queue.Queue()

        self.fu = find_font(UI_FONTS, 10)
        self.fub = find_font(UI_FONTS, 10, "bold")
        self.fus = find_font(UI_FONTS, 9)

        self._build_toolbar()
        self._build_main_area()
        self._build_statusbar()
        self._setup_shortcuts()
        self._update_title()
        self._poll_output()

    def _build_toolbar(self):
        toolbar = tk.Frame(self, bg=THEME["bg"], height=42)
        toolbar.pack(side="top", fill="x")
        toolbar.pack_propagate(False)

        brand = tk.Frame(toolbar, bg=THEME["bg"])
        brand.pack(side="left", padx=(12, 0))
        tk.Label(brand, text="VIPER", font=(self.fub[0], 11, "bold"),
                 bg=THEME["bg"], fg=THEME["accent"]).pack(side="left")
        tk.Label(brand, text=f"  v{__version__}", font=self.fus,
                 bg=THEME["bg"], fg=THEME["dim"]).pack(side="left", pady=(2, 0))

        self._sep(toolbar)
        self._toolbar_btn(toolbar, "  New  ", self.new_file)
        self._toolbar_btn(toolbar, "  Open  ", self.open_file)
        self._toolbar_btn(toolbar, "  Save  ", self.save_file)
        self._sep(toolbar)
        self.btn_run = self._toolbar_btn(toolbar, "  ▶ Run  ", self.run_code, fg=THEME["accent"])
        self.btn_stop = self._toolbar_btn(toolbar, "  ■ Stop  ", self.stop_code, fg=THEME["red"])
        self.btn_stop.configure(state="disabled")
        self._sep(toolbar)
        self._toolbar_btn(toolbar, "  Clear  ", lambda: self.terminal.clear())
        self._toolbar_btn(toolbar, "  🔍 Find  ", lambda: self.editor.toggle_find())

        tk.Frame(self, bg=THEME["accent"], height=1).pack(side="top", fill="x")

    def _sep(self, parent):
        tk.Frame(parent, bg=THEME["border"], width=1, height=20).pack(
            side="left", padx=6, pady=11)

    def _toolbar_btn(self, parent, text, command, fg=None):
        btn = tk.Button(parent, text=text, command=command, font=self.fu,
                        bg=THEME["btn"], fg=fg or THEME["fg"],
                        activebackground=THEME["btn_hover"],
                        activeforeground=fg or THEME["fg"],
                        relief="flat", bd=0, pady=5, cursor="hand2",
                        highlightthickness=0)
        btn.pack(side="left", padx=1, pady=7)
        btn.bind("<Enter>", lambda e: btn.configure(bg=THEME["btn_hover"]))
        btn.bind("<Leave>", lambda e: btn.configure(bg=THEME["btn"]))
        return btn

    def _build_main_area(self):
        paned = tk.PanedWindow(self, orient=tk.VERTICAL, bg=THEME["border"],
                                sashwidth=3, sashrelief="flat", bd=0, opaqueresize=True)
        paned.pack(fill="both", expand=True)

        self.editor = CodeEditor(paned)
        self.editor.on_change = self._update_title
        self.editor.on_save_tab = self._save_tab_at
        paned.add(self.editor, minsize=120, stretch="always")

        self.terminal = Terminal(paned)
        self.terminal.on_command = self._handle_terminal_command
        paned.add(self.terminal, minsize=80, stretch="never")

        self.after(50, lambda: paned.sash_place(0, 0, 440))

        self.editor.text.bind("<KeyRelease>", self._on_editor_event, add=True)
        self.editor.text.bind("<ButtonRelease-1>", self._on_editor_event, add=True)

    def _build_statusbar(self):
        bar = tk.Frame(self, bg=THEME["bg"], height=24)
        bar.pack(side="bottom", fill="x")
        bar.pack_propagate(False)
        self.status_label = tk.Label(bar, text=" Ready", font=self.fus,
                                     bg=THEME["bg"], fg=THEME["dim"])
        self.status_label.pack(side="left", padx=6)
        self.cursor_label = tk.Label(bar, text="Ln 1, Col 1  ", font=self.fus,
                                     bg=THEME["bg"], fg=THEME["dim"])
        self.cursor_label.pack(side="right", padx=6)
        tk.Label(bar, text="Python  ", font=self.fus,
                 bg=THEME["bg"], fg=THEME["dim"]).pack(side="right")
        tk.Label(bar, text="UTF-8  ", font=self.fus,
                 bg=THEME["bg"], fg=THEME["dim"]).pack(side="right")

    def _setup_shortcuts(self):
        self.bind("<F5>", lambda e: self.run_code())
        self.bind("<Control-s>", lambda e: self.save_file())
        self.bind("<Control-n>", lambda e: self.new_file())
        self.bind("<Control-o>", lambda e: self.open_file())
        self.bind("<Control-f>", lambda e: self.editor.toggle_find())
        self.bind("<Control-w>", lambda e: self.editor.close_tab(self.editor.active_tab))
        self.bind("<Control-equal>", lambda e: self._zoom(1))
        self.bind("<Control-minus>", lambda e: self._zoom(-1))
        self.bind("<Control-0>", lambda e: self._zoom(0))

    def _on_editor_event(self, event=None):
        ln, col = self.editor.get_cursor_position()
        self.cursor_label.configure(text=f"Ln {ln}, Col {col}  ")

    def _zoom(self, delta):
        size = 12 if delta == 0 else self.editor._font_size + delta
        self.editor.set_font_size(size)
        self.terminal.set_font_size(size - 1)

    def _update_title(self):
        tab = self.editor.get_active_tab()
        if not tab:
            return
        name = tab["name"]
        marker = " •" if tab["modified"] else ""
        self.title(f"Viper — {name}{marker}")

    def new_file(self):
        self.editor.new_tab()
        self._update_title()

    def open_file(self):
        paths = filedialog.askopenfilenames(
            filetypes=[("Python files", "*.py"), ("All files", "*.*")])
        for path in paths:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.editor.open_in_tab(path, content)
                self._update_title()
            except Exception as ex:
                messagebox.showerror("Viper", str(ex))

    def save_file(self):
        tab = self.editor.get_active_tab()
        if not tab:
            return
        path = tab["path"] or filedialog.asksaveasfilename(
            defaultextension=".py",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")])
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.editor.text.get("1.0", "end-1c"))
            tab["path"] = path
            tab["name"] = os.path.basename(path)
            self.editor.mark_clean()
            self._update_title()
            self.terminal.write(f"Saved → {path}\n", "sys")
        except Exception as ex:
            messagebox.showerror("Viper", str(ex))

    def _save_tab_at(self, index):
        prev = self.editor.active_tab
        self.editor._switch_to(index)
        self.save_file()
        if prev != index and prev < len(self.editor.tabs):
            self.editor._switch_to(prev)

    def run_code(self):
        if self.process:
            return
        code = self.editor.text.get("1.0", "end-1c")
        if not code.strip():
            return
        self._tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8")
        self._tmp.write(code)
        self._tmp.close()

        self.terminal.write("▶ Running\n", "sys")
        self.terminal.write("─" * 44 + "\n", "sys")
        self.status_label.configure(text=" Running...", fg=THEME["accent"])
        self.btn_run.configure(state="disabled")
        self.btn_stop.configure(state="normal")

        try:
            self.process = subprocess.Popen(
                [sys.executable, "-u", self._tmp.name],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                stdin=subprocess.PIPE, text=True, bufsize=1)
            threading.Thread(target=self._read_stream,
                             args=(self.process.stdout, "out"), daemon=True).start()
            threading.Thread(target=self._read_stream,
                             args=(self.process.stderr, "err"), daemon=True).start()
            threading.Thread(target=self._await_process, daemon=True).start()
        except Exception as ex:
            self.terminal.write(f"Error: {ex}\n", "err")
            self._finalize_process()

    def _read_stream(self, stream, tag):
        try:
            for line in iter(stream.readline, ""):
                if line:
                    self._output_queue.put((line, tag))
            stream.close()
        except (ValueError, OSError):
            pass

    def _await_process(self):
        if self.process:
            self.process.wait()
            self._output_queue.put((None, "_done"))

    def _poll_output(self):
        try:
            while True:
                text, tag = self._output_queue.get_nowait()
                if text is None and tag == "_done":
                    self._finalize_process()
                else:
                    self.terminal.write(text, tag)
        except queue.Empty:
            pass
        self.after(50, self._poll_output)

    def _finalize_process(self):
        rc = self.process.returncode if self.process else -1
        self.process = None
        if hasattr(self, "_tmp"):
            try:
                os.unlink(self._tmp.name)
            except OSError:
                pass
        self.terminal.write("─" * 44 + "\n", "sys")
        if rc == 0:
            self.terminal.write("✓ Process exited with code 0\n\n", "sys")
        else:
            self.terminal.write(f"✗ Process exited with code {rc}\n\n", "err")
        self.status_label.configure(text=" Ready", fg=THEME["dim"])
        self.btn_run.configure(state="normal")
        self.btn_stop.configure(state="disabled")

    def stop_code(self):
        if not self.process:
            return
        try:
            self.process.terminate()
        except OSError:
            pass
        self.after(500, self._force_kill)
        self.terminal.write("\n⚠ Terminated by user\n", "err")

    def _force_kill(self):
        if self.process and self.process.poll() is None:
            try:
                self.process.kill()
            except OSError:
                pass

    def _handle_terminal_command(self, cmd):
        if self.process and self.process.stdin:
            try:
                self.terminal.write(cmd + "\n", "echo")
                self.process.stdin.write(cmd + "\n")
                self.process.stdin.flush()
            except (BrokenPipeError, OSError):
                pass
            return

        self.terminal.write(f"› {cmd}\n", "prompt")

        if cmd.lower() == "clear":
            self.terminal.clear()
        elif cmd.lower().startswith(("pip install", "pip3 install", "pip ", "pip3 ")):
            self._run_pip(cmd)
        else:
            self._run_expression(cmd)

    def _run_pip(self, cmd):
        self.terminal.write("Installing...\n", "sys")
        self.status_label.configure(text=" Installing...", fg=THEME["accent"])

        def worker():
            try:
                parts = cmd.split()
                args = parts[1:] if parts[0] in ("pip", "pip3") else parts
                result = subprocess.run(
                    [sys.executable, "-m", "pip"] + args,
                    capture_output=True, text=True, timeout=120)
                if result.stdout:
                    self._output_queue.put((result.stdout, "out"))
                if result.stderr:
                    self._output_queue.put((result.stderr, "err"))
                if result.returncode == 0:
                    self._output_queue.put(("✓ Done\n\n", "sys"))
                else:
                    self._output_queue.put((f"✗ Failed (code {result.returncode})\n\n", "err"))
            except subprocess.TimeoutExpired:
                self._output_queue.put(("✗ Timed out\n\n", "err"))
            except Exception as ex:
                self._output_queue.put((f"Error: {ex}\n\n", "err"))
            finally:
                self.after(0, lambda: self.status_label.configure(
                    text=" Ready", fg=THEME["dim"]))

        threading.Thread(target=worker, daemon=True).start()

    def _run_expression(self, cmd):
        def worker():
            try:
                result = subprocess.run(
                    [sys.executable, "-c", cmd],
                    capture_output=True, text=True, timeout=10)
                if result.stdout:
                    self._output_queue.put((result.stdout, "out"))
                if result.stderr:
                    self._output_queue.put((result.stderr, "err"))
            except subprocess.TimeoutExpired:
                self._output_queue.put(("Timed out\n", "err"))
            except Exception as ex:
                self._output_queue.put((f"Error: {ex}\n", "err"))
            self._output_queue.put(("\n", "out"))

        threading.Thread(target=worker, daemon=True).start()
