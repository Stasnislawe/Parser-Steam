import sys
import os
from sqlalchemy import text

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from project.src.database.config import get_database_config
from project.src.database.db_manager import DatabaseManager


def delete_all_data():
    """Удаляет ВСЕ данные из базы"""
    config = get_database_config()
    db_manager = DatabaseManager(config)

    print("🗑️ Очистка всей базы данных")
    print("=" * 40)

    # Подтверждение
    confirm = input("❓ ВНИМАНИЕ! Это удалит ВСЕ данные из базы. Продолжить? (y/n): ")

    if confirm.lower() != 'y':
        print("❌ Очистка отменена")
        return

    session = db_manager.Session()

    try:
        # Отключаем foreign key constraints для безопасного удаления
        session.execute(text("SET session_replication_role = 'replica';"))

        # Удаляем данные из всех таблиц в правильном порядке
        tables = [
            'game_price_history',
            'game_category_association',
            'game_categories',
            'steam_games'
        ]

        for table in tables:
            try:
                result = session.execute(text(f"DELETE FROM {table};"))
                print(f"✅ Очищена таблица {table}: {result.rowcount} записей")
                session.commit()
            except Exception as e:
                print(f"⚠️ Ошибка очистки {table}: {e}")
                session.rollback()

        # Включаем foreign key constraints обратно
        session.execute(text("SET session_replication_role = 'origin';"))
        session.commit()

        print("\n🎉 База данных полностью очищена!")

    except Exception as e:
        print(f"❌ Ошибка при очистке: {e}")
        session.rollback()
        import traceback
        traceback.print_exc()
    finally:
        session.close()


def check_empty_database():
    """Проверяет, что база пустая"""
    config = get_database_config()
    db_manager = DatabaseManager(config)

    session = db_manager.Session()

    try:
        # Проверяем все таблицы
        tables = ['steam_games', 'game_price_history', 'game_category_association', 'game_categories']

        print("\n🔍 Проверка очистки базы:")
        print("-" * 30)

        total_records = 0
        for table in tables:
            try:
                result = session.execute(text(f"SELECT COUNT(*) FROM {table};"))
                count = result.scalar()
                print(f"   {table}: {count} записей")
                total_records += count
            except:
                print(f"   {table}: таблица не существует")

        if total_records == 0:
            print("✅ База данных полностью пустая!")
        else:
            print(f"⚠️ В базе осталось {total_records} записей")

    except Exception as e:
        print(f"❌ Ошибка проверки: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    delete_all_data()
    check_empty_database()