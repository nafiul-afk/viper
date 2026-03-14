<h1 align="center">
  <br>
  🐍 Viper
  <br>
</h1>

<h4 align="center">A minimal, dark-themed Python compiler for Linux.</h4>

<p align="center">
  <em>Just Python 3 + Tkinter. No Electron. No bloat. Zero dependencies.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.8+-4ec9b0?style=flat-square&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/platform-linux-1a1a1a?style=flat-square&logo=linux&logoColor=white" />
  <img src="https://img.shields.io/badge/license-MIT-333333?style=flat-square" />
  <img src="https://img.shields.io/badge/dependencies-zero-4ec9b0?style=flat-square" />
  <img src="https://img.shields.io/badge/LOC-~1100-333333?style=flat-square" />
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#keyboard-shortcuts">Shortcuts</a> •
  <a href="#contributing">Contributing</a>
</p>

---

## Why Viper?

Most Python IDEs are heavy, slow, or require dozens of dependencies. Viper is the opposite — a clean Python package that gives you everything needed to write and run Python code on Linux. No setup wizards. No configuration files. No internet required.

## Features

### Editor
| Feature | Description |
|---------|-------------|
| **Multi-tab editing** | Open and switch between multiple files without saving |
| **Syntax highlighting** | Keywords, builtins, strings, comments, decorators, numbers |
| **Line numbers** | With active line indicator |
| **Current line highlight** | Subtle dark highlight on cursor line |
| **Auto-indent** | Smart indentation after `:` blocks |
| **Auto-close** | Brackets `()[]{}` and quotes `""''` |
| **Find bar** | Search with match count and prev/next navigation |
| **Zoom** | Ctrl+/- to resize editor font (8–28px) |

### Terminal
| Feature | Description |
|---------|-------------|
| **Run code** | F5 to execute, real-time stdout/stderr streaming |
| **Inline `input()`** | Type directly next to the prompt in the output area — just like a real terminal |
| **pip install** | Install packages directly from the terminal |
| **Expression eval** | Type Python expressions for quick evaluation |
| **Command history** | Arrow keys to cycle through previous commands |

### Workflow
| Feature | Description |
|---------|-------------|
| **No forced saving** | Open, edit, and run files freely — save when you want |
| **Multi-file open** | Select multiple files at once from the file dialog |
| **Content-hash tracking** | Only marks files as modified when content actually changes |
| **Tab management** | Close tabs with ✕, prompted to save only when needed |

## Quick Start

```bash
git clone https://github.com/nafiul-afk/viper.git
cd viper
make run
```

### Install System-Wide

```bash
sudo make install    # installs to /usr/local
viper                # launch from anywhere
```

### Install via pip

```bash
pip install -e .     # editable install
viper                # launch from anywhere
```

### Uninstall

```bash
sudo make uninstall
# or
pip uninstall viper-ide
```

## Requirements

Python 3.8+ with Tkinter:

```bash
# Ubuntu / Debian
sudo apt install python3-tk

# Fedora
sudo dnf install python3-tkinter

# Arch
sudo pacman -S tk
```

## Architecture

```
┌──────────────────────────────────────────────────┐
│                    app.py                        │
│  Main window • Toolbar • Shortcuts • File I/O    │
│  Process management • pip runner                 │
├──────────────────────────────────────────────────┤
│                                                  │
│  ┌────────────────────────────────────────────┐  │
│  │              editor.py                     │  │
│  │  Tab bar • Gutter • Text widget            │  │
│  │  Syntax highlighting • Find bar            │  │
│  │  Auto-close • Content-hash dirty tracking  │  │
│  └────────────────────────────────────────────┘  │
│                                                  │
│  ┌────────────────────────────────────────────┐  │
│  │             terminal.py                    │  │
│  │  Output display • Inline process input     │  │
│  │  Command history • Tag-based coloring      │  │
│  └────────────────────────────────────────────┘  │
│                                                  │
├───────────────┬──────────────────────────────────┤
│   theme.py    │          constants.py            │
│  Color scheme │  Keywords • Builtins • Patterns  │
│  30 tokens    │  Font chains • Regex builder     │
└───────────────┴──────────────────────────────────┘
```

### Design Decisions

- **Content-hash dirty tracking** — Tkinter's `<<Modified>>` event fires on tag operations (syntax highlighting, line highlighting), causing false "unsaved changes" dialogs. Viper uses `hash(content)` comparison instead, eliminating false positives entirely.

- **Per-keysym auto-close bindings** — A catch-all `<Key>` binding blocks text input on some Tkinter/Tcl versions. Viper binds `<KeyPress-parenleft>`, `<KeyPress-bracketleft>`, etc. individually to avoid this.

- **Threaded I/O** — Subprocess stdout/stderr are read in daemon threads using `os.read()` for immediate output (no newline buffering). The main thread polls the queue every 50ms, keeping the UI responsive during code execution.

- **Inline `input()` I/O** — When a process is running, the terminal output area becomes editable. A Tkinter text mark tracks the boundary between program output and user input. The `write()` method uses a save-insert-restore pattern so that program output arriving mid-typing is placed correctly before the user's pending keystrokes.

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `F5` | Run code |
| `Ctrl+S` | Save |
| `Ctrl+N` | New tab |
| `Ctrl+O` | Open file(s) |
| `Ctrl+W` | Close tab |
| `Ctrl+F` | Find |
| `Ctrl+D` | Duplicate line |
| `Ctrl+/` | Toggle comment |
| `Ctrl++` | Zoom in |
| `Ctrl+-` | Zoom out |
| `Ctrl+0` | Reset zoom |
| `Tab` | Indent |
| `Shift+Tab` | Unindent |
| `↑ / ↓` | Terminal history |

## Project Structure

```
viper/
├── viper/
│   ├── __init__.py         # Package metadata
│   ├── __main__.py         # Entry point
│   ├── app.py              # Main application (~360 lines)
│   ├── editor.py           # Code editor (~435 lines)
│   ├── terminal.py         # Terminal widget (~215 lines)
│   ├── theme.py            # Color scheme (37 lines)
│   └── constants.py        # Language constants (63 lines)
├── run.py                  # Convenience launcher
├── pyproject.toml          # Modern Python packaging
├── Makefile                # Build / install / uninstall
├── CHANGELOG.md            # Release history
├── CONTRIBUTING.md         # Contribution guidelines
├── LICENSE                 # MIT License
├── README.md
└── .gitignore
```

## Philosophy

> One theme. One purpose. Zero compromise.

Viper is not trying to be VS Code. It is a focused tool for writing and running Python on Linux — nothing more, nothing less. Every feature exists because it removes friction, not because it looks good on a feature list.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT — see [LICENSE](LICENSE)

---

<p align="center">
  <sub>Built with 🐍 by <a href="https://github.com/nafiul-afk">Nafiul Islam</a></sub>
</p>
