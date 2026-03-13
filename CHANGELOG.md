# Changelog

All notable changes to Viper will be documented in this file.

## [1.0.0] — 2026-03-14

### Added
- Multi-tab editor with tab bar, close buttons, and per-tab dirty tracking
- Syntax highlighting for Python keywords, builtins, strings, comments, decorators, numbers
- Line numbers with active line indicator
- Current line highlight
- Find bar with match count, prev/next navigation (Ctrl+F)
- Auto-closing brackets and quotes
- Toggle comment (Ctrl+/)
- Duplicate line (Ctrl+D)
- Zoom in/out (Ctrl++/-, Ctrl+0 to reset)
- Auto-indent on newline after `:` blocks
- Block indent/unindent (Tab / Shift+Tab)
- Built-in terminal with real-time stdout/stderr streaming
- Interactive `input()` support during code execution
- Terminal command history with arrow keys
- pip package management from terminal
- Python expression evaluation in terminal
- File operations: New, Open (multi-select), Save, Save As
- Content-hash based dirty detection (no false positives)
- Keyboard shortcut system (F5, Ctrl+S, Ctrl+N, Ctrl+O, Ctrl+W, etc.)
- Status bar with cursor position, encoding, and file type
- Dark theme inspired by VS Code
- Smart font fallback chain (JetBrains Mono → Fira Code → system mono)
- Makefile with run, install, uninstall, check-deps targets
- pyproject.toml for modern Python packaging

### Architecture
- Modular package structure: `theme`, `constants`, `editor`, `terminal`, `app`
- Zero external dependencies — pure Python 3 + Tkinter
- Single-process design with threaded I/O for subprocess management
