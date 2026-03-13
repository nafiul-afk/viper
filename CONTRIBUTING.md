# Contributing to Viper

Thanks for your interest in contributing to Viper!

## Development Setup

```bash
git clone https://github.com/nafiul-afk/viper.git
cd viper
make check-deps
make run
```

## Project Structure

```
viper/
├── __init__.py       # Package metadata and version
├── __main__.py       # Entry point (python -m viper)
├── app.py            # Main window, toolbar, file & process management
├── editor.py         # Multi-tab code editor with syntax highlighting
├── terminal.py       # Terminal widget with I/O and command history
├── theme.py          # Centralized dark color scheme
└── constants.py      # Language constants, fonts, regex patterns
```

## Guidelines

- **Zero dependencies** — Viper uses only Python's standard library (Tkinter). Don't add external packages.
- **One file, one concern** — Keep modules focused. Editor logic stays in `editor.py`, terminal in `terminal.py`, etc.
- **Dark theme only** — All colors come from `theme.py`. Don't hardcode hex values elsewhere.
- **Test on Linux** — Viper targets Linux desktops. Test with both X11 and Wayland if possible.

## Making Changes

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Test by running: `make run`
5. Submit a pull request

## Code Style

- No comments in production code — the code should be self-documenting
- Use docstrings for modules and classes
- Keep methods short and focused
- Follow PEP 8 naming conventions

## Reporting Issues

Open an issue with:
- Python version (`python3 --version`)
- Linux distribution
- Steps to reproduce
- Expected vs actual behavior
