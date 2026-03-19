import json
import os

class SettingsManager:
    DEFAULT_SETTINGS = {
        "theme": "Dark",
        "font_family": "Consolas",
        "font_size": 16,
        "auto_save": True,
        "ghost_text_enabled": True,
        "minimap_visible": True,
        "zoom_level": 1.0
    }

    def __init__(self):
        self.path = os.path.join("data", "settings.json")
        self.settings = self.DEFAULT_SETTINGS.copy()
        self.load()

    def load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r") as f:
                    user_settings = json.load(f)
                    self.settings.update(user_settings)
            except: pass

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        try:
            with open(self.path, "w") as f:
                json.dump(self.settings, f, indent=4)
        except: pass

    def get(self, key):
        return self.settings.get(key, self.DEFAULT_SETTINGS.get(key))

    def set(self, key, value):
        self.settings[key] = value
        self.save()
