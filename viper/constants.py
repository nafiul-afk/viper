"""Language constants, font resolution, and syntax highlighting patterns.

Contains Python keyword/builtin sets, bracket pair mappings, font
fallback chains, and compiled regex patterns for tokenizing Python
source code in the editor.
"""

import re
import tkinter.font as tkfont

KEYWORDS = {
    'False','None','True','and','as','assert','async','await','break','class',
    'continue','def','del','elif','else','except','finally','for','from',
    'global','if','import','in','is','lambda','nonlocal','not','or','pass',
    'raise','return','try','while','with','yield',
}

BUILTINS = {
    'abs','all','any','bin','bool','bytes','callable','chr','classmethod',
    'compile','complex','delattr','dict','dir','divmod','enumerate','eval',
    'exec','filter','float','format','frozenset','getattr','globals','hasattr',
    'hash','help','hex','id','input','int','isinstance','issubclass','iter',
    'len','list','locals','map','max','memoryview','min','next','object','oct',
    'open','ord','pow','print','property','range','repr','reversed','round',
    'set','setattr','slice','sorted','staticmethod','str','sum','super',
    'tuple','type','vars','zip','Exception','ValueError','TypeError',
    'KeyError','IndexError','AttributeError','ImportError','OSError',
    'RuntimeError','StopIteration','ZeroDivisionError','FileNotFoundError',
    'NameError','SyntaxError','IndentationError','PermissionError','EOFError',
    '__name__','__main__','__file__','__init__',
}

PAIRS = {'(': ')', '[': ']', '{': '}', '"': '"', "'": "'"}

MONO_FONTS = ("JetBrains Mono","Fira Code","Source Code Pro","Ubuntu Mono",
              "DejaVu Sans Mono","Liberation Mono","monospace")
UI_FONTS = ("Inter","Segoe UI","Ubuntu","Cantarell","DejaVu Sans","sans-serif")

DEFAULT_CODE = 'print("Hello, World!")\n\nfor i in range(1, 6):\n    print(f"{i} squared is {i**2}")\n'


def find_font(families, size=12, weight="normal"):
    available = set(tkfont.families())
    for f in families:
        if f in available:
            return (f, size, weight)
    return (families[-1], size, weight)


def build_patterns():
    kp = r'\b(?:' + '|'.join(KEYWORDS) + r')\b'
    bp = r'\b(?:' + '|'.join(BUILTINS) + r')\b'
    return [
        ("number",    re.compile(r'\b(?:0[xXoObB][\da-fA-F_]+|\d[\d_]*(?:\.[\d_]*)?(?:[eE][+-]?\d+)?)\b')),
        ("builtin",   re.compile(bp)),
        ("kw",        re.compile(kp)),
        ("selfcls",   re.compile(r'\b(?:self|cls)\b')),
        ("decorator", re.compile(r'^\s*@[\w.]+', re.MULTILINE)),
        ("function",  re.compile(r'(?<=\bdef\s)\w+')),
        ("classname", re.compile(r'(?<=\bclass\s)\w+')),
        ("string",    re.compile(r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'|"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'')),
        ("comment",   re.compile(r'#[^\n]*')),
    ]
