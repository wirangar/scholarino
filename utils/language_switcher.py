import json
import os

class LanguageSwitcher:
    def __init__(self, lang_dir):
        self.lang_dir = lang_dir
        self.user_languages = {}  # In-memory cache for user languages
        
        # Load all language files
        self.translations = {}
        for lang_file in os.listdir(lang_dir):
            if lang_file.endswith('.json'):
                lang_code = lang_file.split('.')[0]
                with open(os.path.join(lang_dir, lang_file), 'r', encoding='utf-8') as f:
                    self.translations[lang_code] = json.load(f)
    
    def get_user_language(self, user_id, default='fa'):
        return self.user_languages.get(str(user_id), default)
    
    def set_user_language(self, user_id, lang_code):
        self.user_languages[str(user_id)] = lang_code
    
    def get_translation(self, lang_code, key):
        if lang_code in self.translations and key in self.translations[lang_code]:
            return self.translations[lang_code][key]
        elif key in self.translations['fa']:  # Fallback to Persian
            return self.translations['fa'][key]
        else:
            return key  # Return the key itself if no translation found