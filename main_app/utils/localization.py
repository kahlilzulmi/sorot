"""
Localization Module

Handles bilingual support (English/Indonesian) for the application.
Loads translations from JSON files and provides text retrieval functions.

Author: Kahlil Gibran Al Zulmi
NRP: 5049221015
Medical Technology Study Program - ITS
"""

import json
import os


# Global translation cache
_translations = {}
_current_language = "en"
_available_languages = ["en", "id"]


def load_translations(language_code="en", translations_dir="assets/translations"):
    """
    Load translations for specified language.
    
    Args:
        language_code (str): Language code ('en' or 'id')
        translations_dir (str): Directory containing translation files
        
    Returns:
        dict: Translation dictionary
    """
    global _translations, _current_language
    
    if language_code not in _available_languages:
        print(f"Language '{language_code}' not available. Using 'en'.")
        language_code = "en"
    
    translation_file = os.path.join(translations_dir, f"{language_code}.json")
    
    if not os.path.exists(translation_file):
        print(f"Translation file not found: {translation_file}")
        return {}
    
    try:
        with open(translation_file, 'r', encoding='utf-8') as f:
            _translations = json.load(f)
        _current_language = language_code
        return _translations
    except Exception as e:
        print(f"Error loading translations: {e}")
        return {}


def get_text(key, language=None, **kwargs):
    """
    Get translated text for a key.
    Supports nested keys using dot notation (e.g., 'menu.detection').
    Supports string formatting using kwargs.
    
    Args:
        key (str): Translation key (supports dot notation)
        language (str, optional): Override current language
        **kwargs: Format arguments for string interpolation
        
    Returns:
        str: Translated text or key if not found
    """
    global _translations, _current_language
    
    if language and language != _current_language:
        load_translations(language)
    
    if not _translations:
        load_translations(_current_language)
    
    # Navigate nested dictionary using dot notation
    keys = key.split('.')
    value = _translations
    
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return key  # Return key itself if not found
    
    # Format string if kwargs provided
    if isinstance(value, str) and kwargs:
        try:
            value = value.format(**kwargs)
        except KeyError:
            pass  # Return unformatted if format args missing
    
    return value


def switch_language(new_language, config_path="config.json"):
    """
    Switch to a different language and save preference.
    
    Args:
        new_language (str): New language code
        config_path (str): Path to configuration file
        
    Returns:
        bool: True if successful
    """
    if new_language not in _available_languages:
        print(f"Language '{new_language}' not available.")
        return False
    
    load_translations(new_language)
    
    # Save to config
    try:
        from utils.config_manager import update_config_value
        return update_config_value(config_path, "language", "", new_language)
    except Exception as e:
        print(f"Error saving language preference: {e}")
        return False


def get_available_languages():
    """
    Get list of available languages.
    
    Returns:
        list: List of tuples (code, name)
    """
    return [
        ("en", "English"),
        ("id", "Bahasa Indonesia")
    ]


def get_current_language():
    """
    Get current language code.
    
    Returns:
        str: Current language code
    """
    return _current_language


def get_language_name(language_code):
    """
    Get language name from code.
    
    Args:
        language_code (str): Language code
        
    Returns:
        str: Language name
    """
    languages = dict(get_available_languages())
    return languages.get(language_code, "Unknown")


# Helper functions for commonly used texts
def t(key, **kwargs):
    """
    Shorthand for get_text().
    
    Args:
        key (str): Translation key
        **kwargs: Format arguments
        
    Returns:
        str: Translated text
    """
    return get_text(key, **kwargs)


def menu_text(item):
    """
    Get menu item text.
    
    Args:
        item (str): Menu item key
        
    Returns:
        str: Translated menu text
    """
    return get_text(f"menu.{item}")


def message_text(msg_key, **kwargs):
    """
    Get message text with formatting.
    
    Args:
        msg_key (str): Message key
        **kwargs: Format arguments
        
    Returns:
        str: Translated message
    """
    return get_text(f"messages.{msg_key}", **kwargs)


def common_text(item):
    """
    Get common UI text (OK, Cancel, etc.).
    
    Args:
        item (str): Common text key
        
    Returns:
        str: Translated text
    """
    return get_text(f"common.{item}")


if __name__ == "__main__":
    # Test localization
    print("Testing Localization Module...")
    print("="*60)
    
    # Test English
    print("\n1. Testing English:")
    load_translations("en")
    print(f"   App Title: {get_text('app_title')}")
    print(f"   Menu Detection: {menu_text('detection')}")
    print(f"   Common OK: {common_text('ok')}")
    print(f"   Message (formatted): {message_text('processing_complete', path='output/')}")
    
    # Test Indonesian
    print("\n2. Testing Indonesian:")
    load_translations("id")
    print(f"   App Title: {get_text('app_title')}")
    print(f"   Menu Detection: {menu_text('detection')}")
    print(f"   Common OK: {common_text('ok')}")
    print(f"   Message (formatted): {message_text('processing_complete', path='output/')}")
    
    # Test nested keys
    print("\n3. Testing nested keys:")
    print(f"   detection.methods.hough: {get_text('detection.methods.hough')}")
    print(f"   system_status.windows_ok: {get_text('system_status.windows_ok')}")
    
    # Test shorthand
    print("\n4. Testing shorthand function:")
    print(f"   t('app_title'): {t('app_title')}")
    
    # Test available languages
    print("\n5. Available languages:")
    for code, name in get_available_languages():
        print(f"   {code}: {name}")
    
    print("\n" + "="*60)
    print("Localization test complete!")
