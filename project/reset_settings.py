# reset_settings.py
import os
from settings import SettingsManager


def reset_settings():
    """Сбрасывает настройки к defaults"""
    if os.path.exists("user_settings.json"):
        os.remove("user_settings.json")
        print("✅ Файл настроек удален")

    manager = SettingsManager()
    print("✅ Настройки сброшены к значениям по умолчанию")


if __name__ == "__main__":
    reset_settings()