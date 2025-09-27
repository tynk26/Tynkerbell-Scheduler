
import json, os

SETTINGS_FILE = "settings.json"

DEFAULTS = {
    "api_key": "",
    "model": "gpt-4o-mini",
    "timezone": "KST",
    "save_progress": True,
    "daily_ai_reminders": True,
    "reminder_interval_min": 120,
    "auto_reroll_missed": True,
    "cloud_backup_enabled": False
}

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        save_settings(DEFAULTS)
        return DEFAULTS.copy()
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    for k, v in DEFAULTS.items():
        if k not in data:
            data[k] = v
    return data

def save_settings(data):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
