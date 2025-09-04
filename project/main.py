# main.py
import asyncio
import logging
import sys
import os

# Добавляем корневую директорию проекта в путь для импортов
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def main():
    try:
        from project.config.config import config
        from project.src.bot.steam_bot import SteamBot

        if not config.BOT_TOKEN:
            logging.error("BOT_TOKEN не найден в .env файле!")
            return

        logging.info("Создаем Steam бота...")

        # Создаем и запускаем бота
        bot = SteamBot(config.BOT_TOKEN)
        await bot.start()

    except ImportError as e:
        logging.error(f"Ошибка импорта: {e}")
        logging.error("Проверьте структуру проекта и импорты")

    except Exception as e:
        logging.error(f"Неожиданная ошибка: {e}")


if __name__ == "__main__":
    asyncio.run(main())