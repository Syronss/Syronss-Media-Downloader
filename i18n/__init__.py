"""
Internationalization (i18n) system for Syronss's Media Downloader.
Supports Turkish and English with dynamic language switching.
"""

import json
from pathlib import Path
from typing import Dict, Optional

_current_language = "tr"
_translations: Dict[str, Dict[str, str]] = {}
_loaded = False


def _load_translations() -> None:
    """Load all translation files from the i18n directory."""
    global _translations, _loaded
    if _loaded:
        return

    i18n_dir = Path(__file__).parent
    for lang_file in i18n_dir.glob("*.json"):
        lang_code = lang_file.stem
        try:
            with open(lang_file, "r", encoding="utf-8") as f:
                _translations[lang_code] = json.load(f)
        except Exception:
            _translations[lang_code] = {}
    _loaded = True


def set_language(lang: str) -> None:
    """Set the active language."""
    global _current_language
    _load_translations()
    if lang in _translations:
        _current_language = lang


def get_language() -> str:
    """Get current language code."""
    return _current_language


def t(key: str, **kwargs) -> str:
    """
    Translate a key to the current language.
    Supports format placeholders: t("hello_user", name="Syronss")
    Falls back to Turkish, then returns the key itself.
    """
    _load_translations()

    text = _translations.get(_current_language, {}).get(key)
    if text is None:
        text = _translations.get("tr", {}).get(key)
    if text is None:
        return key

    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass

    return text


def get_available_languages() -> Dict[str, str]:
    """Return dict of available language codes to their native names."""
    _load_translations()
    from constants import LANGUAGES
    return {code: LANGUAGES.get(code, code) for code in _translations}
