import json
import os
from dataclasses import dataclass, asdict, field
from typing import List, Optional, Any, Dict
from enum import Enum


class DisplayMode(Enum):
    MINIMAL = "minimal"
    STANDARD = "standard"
    FULL = "full"


class GamesCount(Enum):
    ONE = 1
    TWO = 2
    THREE = 3
    SIX = 6
    TWELVE = 12


class GameMode(Enum):
    POPULAR = "popular"
    DISCOUNTED = "discounted"
    CATEGORY = "category"


@dataclass
class UserPagination:
    current_games: List[dict] = field(default_factory=list)
    current_index: int = 0
    all_loaded_games: List[dict] = field(default_factory=list)
    total_count: int = 0
    offset: int = 0
    has_more: bool = True
    game_mode: GameMode = GameMode.POPULAR
    current_category: str = ""  # Поле для хранения текущей категории

    def to_dict(self) -> Dict[str, Any]:
        return {
            'current_games': self.current_games,
            'current_index': self.current_index,
            'all_loaded_games': self.all_loaded_games,
            'total_count': self.total_count,
            'offset': self.offset,
            'has_more': self.has_more,
            'game_mode': self.game_mode.value,
            'current_category': self.current_category
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserPagination':
        return cls(
            current_games=data.get('current_games', []),
            current_index=data.get('current_index', 0),
            all_loaded_games=data.get('all_loaded_games', []),
            total_count=data.get('total_count', 0),
            offset=data.get('offset', 0),
            has_more=data.get('has_more', True),
            game_mode=GameMode(data.get('game_mode', 'popular')),
            current_category=data.get('current_category', '')
        )


@dataclass
class UserSettings:
    display_mode: DisplayMode = DisplayMode.STANDARD
    games_count: GamesCount = GamesCount.ONE
    pagination: Optional[UserPagination] = None
    awaiting_category: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'display_mode': self.display_mode.value,
            'games_count': self.games_count.value,
            'pagination': self.pagination.to_dict() if self.pagination else None,
            'awaiting_category': self.awaiting_category
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserSettings':
        pagination_data = data.get('pagination')
        pagination = UserPagination.from_dict(pagination_data) if pagination_data else None

        return cls(
            display_mode=DisplayMode(data.get('display_mode', 'standard')),
            games_count=GamesCount(data.get('games_count', 1)),
            pagination=pagination,
            awaiting_category=data.get('awaiting_category', False)
        )


class SettingsManager:
    def __init__(self):
        self.settings_file = "../user_settings.json"
        self.user_settings = {}
        self._load_settings()

    def _load_settings(self):
        """Загружает настройки из файла"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()

                    # Проверяем, что файл не пустой
                    if not content:
                        print("⚠️ Файл настроек пуст, создаем новый")
                        self._create_default_settings()
                        return

                    # Проверяем валидность JSON
                    try:
                        data = json.loads(content)
                    except json.JSONDecodeError as e:
                        print(f"❌ Ошибка JSON в файле настроек: {e}")
                        print("🧹 Создаем новый файл настроек")
                        self._create_default_settings()
                        return

                    print(f"📊 Загружено настроек для {len(data)} пользователей")
                    for user_id, settings_data in data.items():
                        try:
                            self.user_settings[int(user_id)] = UserSettings.from_dict(settings_data)
                        except Exception as e:
                            print(f"⚠️ Ошибка загрузки настроек пользователя {user_id}: {e}")
                            # Создаем default настройки для этого пользователя
                            self.user_settings[int(user_id)] = UserSettings()

            except Exception as e:
                print(f"❌ Критическая ошибка загрузки настроек: {e}")
                print("🧹 Создаем новый файл настроек")
                self._create_default_settings()
        else:
            print("ℹ️ Файл настроек не найден, создаем новый")
            self._create_default_settings()

    def _create_default_settings(self):
        """Создает default настройки"""
        self.user_settings = {}
        self._save_settings()
        print("✅ Создан новый файл настроек по умолчанию")

    def _save_settings(self):
        """Сохраняет настройки в файл"""
        try:
            data = {}
            for user_id, settings in self.user_settings.items():
                # Проверяем, что настройки можно сериализовать
                try:
                    settings_dict = settings.to_dict()
                    # Проверяем, что все значения сериализуемы
                    json.dumps(settings_dict)  # Тестовая сериализация
                    data[str(user_id)] = settings_dict
                except (TypeError, ValueError) as e:
                    print(f"⚠️ Ошибка сериализации настроек пользователя {user_id}: {e}")
                    # Пропускаем проблемные настройки
                    continue

            # Создаем backup старого файла
            if os.path.exists(self.settings_file):
                backup_file = f"{self.settings_file}.backup"
                import shutil
                shutil.copy2(self.settings_file, backup_file)
                print(f"📦 Создан backup: {backup_file}")

            # Сохраняем новые настройки
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"💾 Настройки сохранены для {len(data)} пользователей")

        except Exception as e:
            print(f"❌ Критическая ошибка сохранения настроек: {e}")
            # Пытаемся восстановить из backup
            self._restore_from_backup()

    def _restore_from_backup(self):
        """Восстанавливает настройки из backup"""
        backup_file = f"{self.settings_file}.backup"
        if os.path.exists(backup_file):
            try:
                import shutil
                shutil.copy2(backup_file, self.settings_file)
                print(f"🔄 Восстановлены настройки из backup: {backup_file}")
                self._load_settings()  # Перезагружаем настройки
            except Exception as e:
                print(f"❌ Ошибка восстановления из backup: {e}")
                self._create_default_settings()
        else:
            print("⚠️ Backup не найден, создаем новые настройки")
            self._create_default_settings()

    def get_user_settings(self, user_id: int) -> UserSettings:
        """Получает настройки пользователя"""
        if user_id not in self.user_settings:
            print(f"🆕 Создаем новые настройки для пользователя {user_id}")
            self.user_settings[user_id] = UserSettings()
            self._save_settings()
        return self.user_settings[user_id]

    def set_display_mode(self, user_id: int, display_mode: DisplayMode):
        """Устанавливает режим отображения"""
        settings = self.get_user_settings(user_id)
        settings.display_mode = display_mode
        self.user_settings[user_id] = settings
        self._save_settings()
        print(f"✅ Установлен режим отображения: {display_mode.value} для пользователя {user_id}")

    def set_games_count(self, user_id: int, games_count: GamesCount):
        """Устанавливает количество игр"""
        settings = self.get_user_settings(user_id)
        settings.games_count = games_count
        self.user_settings[user_id] = settings
        self._save_settings()
        print(f"✅ Установлено количество игр: {games_count.value} для пользователя {user_id}")

    def update_pagination(self, user_id: int, pagination: UserPagination):
        """Обновляет пагинацию пользователя"""
        settings = self.get_user_settings(user_id)
        settings.pagination = pagination
        self.user_settings[user_id] = settings
        self._save_settings()
        print(f"✅ Обновлена пагинация для пользователя {user_id}")

    def clear_user_settings(self, user_id: int):
        """Очищает настройки пользователя"""
        if user_id in self.user_settings:
            del self.user_settings[user_id]
            self._save_settings()
            print(f"🧹 Очищены настройки пользователя {user_id}")

    def get_all_users(self) -> List[int]:
        """Возвращает список всех пользователей"""
        return list(self.user_settings.keys())


# Пример использования
if __name__ == "__main__":
    manager = SettingsManager()

    # Тестируем создание настроек
    test_user_id = 12345
    settings = manager.get_user_settings(test_user_id)
    print(f"Настройки пользователя {test_user_id}:")
    print(f"  Display mode: {settings.display_mode}")
    print(f"  Games count: {settings.games_count}")
    print(f"  Pagination: {settings.pagination}")

    # Тестируем изменение настроек
    manager.set_display_mode(test_user_id, DisplayMode.FULL)
    manager.set_games_count(test_user_id, GamesCount.THREE)

    print("✅ Тест настроек завершен успешно!")