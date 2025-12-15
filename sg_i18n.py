"""
Internationalization (i18n) support module for stable-gimpfusion3

GIMP automatically looks for .mo files in locale/ subdirectory
with text domain equal to the plug-in name.
"""

from __future__ import annotations

import gettext
import locale
import logging
import os

from collections.abc import Callable

DOMAIN = "stable-gimpfusion3"


def setup_i18n() -> Callable[[str], str]:
    """Initialize internationalization support"""

    # Get the directory where this script is located
    plugin_dir = os.path.dirname(os.path.abspath(__file__))
    locale_dir = os.path.join(plugin_dir, "locale")

    try:
        locale.setlocale(locale.LC_ALL, "")
    except locale.Error:
        try:
            locale.setlocale(locale.LC_ALL, "C.UTF-8")
        except locale.Error:
            locale.setlocale(locale.LC_ALL, "C")

    try:
        translation = gettext.translation(DOMAIN, locale_dir, fallback=True)
        translation.install()
        return translation.gettext
    except OSError as e:
        logging.error(f"Translation files not found: {e}")
        import builtins

        def fallback_gettext(x: str) -> str:
            return x

        builtins.__dict__["_"] = fallback_gettext
        return fallback_gettext
    except Exception as e:
        logging.error(f"Unexpected i18n error: {e}")
        import builtins

        def fallback_gettext(x: str) -> str:
            return x

        builtins.__dict__["_"] = fallback_gettext
        return fallback_gettext


_: Callable[[str], str] = setup_i18n()


def gettext_lazy(s: str) -> str:
    """Lazy translation function (returns string as-is, translation happens later)"""
    return s


def get_localized_list(original_list: list[str]) -> list[str]:
    """
    Get a localized version of a list of strings.

    Args:
        original_list: List of strings to localize

    Returns:
        List of localized strings
    """
    return [_(item) for item in original_list]


def get_localized_dict(original_dict: dict[str, str]) -> dict[str, str]:
    """
    Get a localized version of a dictionary with string values.

    Args:
        original_dict: Dictionary with string values to localize

    Returns:
        Dictionary with localized values
    """
    return {key: _(value) for key, value in original_dict.items()}
