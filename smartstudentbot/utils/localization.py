import json
from pathlib import Path

# Cache for translations to avoid reading files on every request
_translations = {}
_default_lang = "en"

def load_translations():
    """
    Loads all translation files from the 'lang' directory into the cache.
    """
    lang_dir = Path(__file__).parent.parent / "lang"
    if not lang_dir.exists():
        # This should not happen in a normal run, but good to have a check
        print(f"Language directory not found at {lang_dir}")
        return

    for lang_file in lang_dir.glob("*.json"):
        lang_code = lang_file.stem
        with open(lang_file, "r", encoding="utf-8") as f:
            _translations[lang_code] = json.load(f)

    print(f"Loaded translations for: {list(_translations.keys())}")

def get_string(language_code: str, key: str) -> str:
    """
    Gets a translated string for a given language and key.

    Args:
        language_code: The language code (e.g., "en", "fa").
        key: The key for the string (e.g., "welcome").

    Returns:
        The translated string. Falls back to the default language if the key
        or language is not found.
    """
    if not _translations:
        load_translations()

    # Fallback to default language if the requested language doesn't exist
    lang_dict = _translations.get(language_code, _translations.get(_default_lang, {}))

    # Get the string, falling back to the default language's string if the key is missing
    return lang_dict.get(key, _translations.get(_default_lang, {}).get(key, key))

# Example of how to use it:
if __name__ == "__main__":
    load_translations()

    print("\n--- Testing Translations ---")
    print(f"English 'welcome': {get_string('en', 'welcome')}")
    print(f"Farsi 'welcome': {get_string('fa', 'welcome')}")
    print(f"Italian 'welcome': {get_string('it', 'welcome')}")
    print(f"Non-existent language 'fr' for 'welcome': {get_string('fr', 'welcome')}")
    print(f"Non-existent key 'goodbye' for 'en': {get_string('en', 'goodbye')}")
    print("--------------------------\n")
