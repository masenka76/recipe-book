"""Починка путей к системным библиотекам до импорта WeasyPrint.

На macOS Homebrew ставит pango/glib в ``/opt/homebrew/lib`` (Apple Silicon) или
``/usr/local/lib`` (Intel), но динамический загрузчик туда не смотрит, и WeasyPrint
падает с ``cannot load library 'libgobject-2.0-0'``. Переменную ``DYLD_*`` нельзя
задать после старта процесса — dyld читает её только при exec, — поэтому при
необходимости перезапускаем процесс с уже выставленной переменной.
"""

from __future__ import annotations

import os
import platform
import sys

_MARKER = "_RECIPE_BOOK_DYLD_FIXED"


def ensure_native_libs() -> None:
    if platform.system() != "Darwin" or os.environ.get(_MARKER):
        return

    for brew_lib in ("/opt/homebrew/lib", "/usr/local/lib"):
        if os.path.isdir(brew_lib):
            break
    else:
        return

    current = os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", "")
    if brew_lib in current.split(":"):
        return

    os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = (
        f"{brew_lib}:{current}" if current else f"{brew_lib}:/usr/local/lib:/usr/lib"
    )
    os.environ[_MARKER] = "1"
    os.execv(sys.executable, [sys.executable, "-m", "recipe_book.cli", *sys.argv[1:]])
