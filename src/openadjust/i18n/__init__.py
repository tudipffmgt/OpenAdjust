"""
Internationalization (i18n) module.
"""

import gettext
import os
from pathlib import Path

LOCALE_DIR = Path(__file__).parent
SUPPORTED_LANGUAGES = ['de', 'en']
DEFAULT_LANGUAGE = 'de'

_current_language = DEFAULT_LANGUAGE
_translator = None


def set_language(lang: str) -> None:
    """Sets the active language."""
    global _current_language, _translator
    
    if lang not in SUPPORTED_LANGUAGES:
        lang = DEFAULT_LANGUAGE
    
    _current_language = lang
    
    try:
        _translator = gettext.translation(
            'openadjust',
            localedir=str(LOCALE_DIR),
            languages=[lang],
            fallback=True
        )
        _translator.install()
    except Exception:
        _translator = None


def _(message: str) -> str:
    """Translation function."""
    if _translator:
        return _translator.gettext(message)
    return message


def get_current_language() -> str:
    """Returns the current language code."""
    return _current_language


# Set default language on import
set_language(DEFAULT_LANGUAGE)
