"""
Скрипт для инициализации базы данных PostgreSQL
"""
import sys
import os
from sqlalchemy import text

# Добавляем текущую директорию в путь Python
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from project.src.database.db_manager import DatabaseManager
from project.src.database.config import get_database_config


def main():
    print("🚀 Инициализация базы данных PostgreSQL...")

    # Получаем конфигурацию
    config = get_database_config()
    print(f"📊 Настройки подключения:")
    print(f"   Host: {config.host}:{config.port}")
    print(f"   Database: {config.database}")
    print(f"   Username: {config.username}")

    # Проверяем пароль
    if not config.password:
        config.password = input("🔑 Введите пароль для PostgreSQL: ")

    # Инициализируем менеджер с новой конфигурацией
    db_manager = DatabaseManager(config)

    try:
        # Создаем таблицы
        db_manager.init_database()
        print("✅ Таблицы успешно созданы в PostgreSQL!")

        # Тестовое подключение с явным указанием text()
        session = db_manager.Session()
        result = session.execute(text("SELECT version()"))
        version = result.scalar()
        session.close()
        print(f"✅ Подключение к базе данных успешно! PostgreSQL version: {version}")

    except Exception as e:
        print(f"❌ Ошибка при инициализации базы данных: {e}")
        print("\n🔧 Проверь:")
        print("   - Запущен ли PostgreSQL сервер")
        print("   - Правильность имени пользователя и пароля")
        print("   - Существует ли база данных 'steam_pars' в pgAdmin")
        print("   - Разрешения пользователя на создание таблиц")


if __name__ == "__main__":
    main()