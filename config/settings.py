"""Compatibility shim for settings package.

This file exists so tools or code that expect `config.settings` to be a
module still work when we split settings into a package at
`config/settings/`. It imports the local settings by default.
"""

try:
    # Prefer explicit package import
    from config.settings.local import *  # type: ignore
except Exception:
    # Fallback to base if local isn't available
    from config.settings.base import *  # type: ignore
