"""Tests for constants and i18n modules."""

import json
from pathlib import Path

from constants import (
    SUPPORTED_PLATFORMS, QUALITY_OPTIONS, FILENAME_TEMPLATES,
    PLATFORM_ICONS, PLATFORM_COLORS, DEFAULT_SETTINGS, LANGUAGES,
)
from i18n import t, set_language, get_language


# ─── Constants ───

def test_all_platforms_have_icons() -> None:
    for platform in SUPPORTED_PLATFORMS:
        assert platform in PLATFORM_ICONS, f"Missing icon for {platform}"


def test_all_platforms_have_colors() -> None:
    for platform in SUPPORTED_PLATFORMS:
        assert platform in PLATFORM_COLORS, f"Missing color for {platform}"


def test_default_settings_has_required_keys() -> None:
    required = {"filename_template", "theme", "language", "auto_folder", "notifications", "auto_update_check"}
    assert required.issubset(DEFAULT_SETTINGS.keys())


def test_quality_options_non_empty() -> None:
    assert len(QUALITY_OPTIONS) > 0
    assert "best" in QUALITY_OPTIONS


def test_filename_templates_non_empty() -> None:
    assert len(FILENAME_TEMPLATES) > 0


def test_languages_dict() -> None:
    assert "tr" in LANGUAGES
    assert "en" in LANGUAGES


# ─── i18n ───

def test_set_and_get_language() -> None:
    set_language("en")
    assert get_language() == "en"
    set_language("tr")
    assert get_language() == "tr"


def test_translate_known_key() -> None:
    set_language("tr")
    result = t("app_title")
    assert "Syronss" in result


def test_translate_en_key() -> None:
    set_language("en")
    result = t("btn_download")
    assert "DOWNLOAD" in result


def test_translate_fallback_to_key() -> None:
    set_language("tr")
    result = t("totally_nonexistent_key_12345")
    assert result == "totally_nonexistent_key_12345"


def test_translate_format_params() -> None:
    set_language("tr")
    result = t("status_error", error="test error")
    assert "test error" in result


def test_translate_format_params_en() -> None:
    set_language("en")
    result = t("folder_changed", folder="/tmp/downloads")
    assert "/tmp/downloads" in result


def test_both_translation_files_have_same_keys() -> None:
    """Ensure TR and EN have the same keys."""
    i18n_dir = Path(__file__).resolve().parent.parent / "i18n"
    with open(i18n_dir / "tr.json", "r", encoding="utf-8") as f:
        tr_keys = set(json.load(f).keys())
    with open(i18n_dir / "en.json", "r", encoding="utf-8") as f:
        en_keys = set(json.load(f).keys())

    missing_in_en = tr_keys - en_keys
    missing_in_tr = en_keys - tr_keys

    assert not missing_in_en, f"Keys in TR but not EN: {missing_in_en}"
    assert not missing_in_tr, f"Keys in EN but not TR: {missing_in_tr}"
