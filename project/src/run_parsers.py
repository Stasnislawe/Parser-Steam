# run_parsers_final.py
import asyncio
from project.src.parser.steam_parser_finally import SteamParserFinal


async def main():
    print("🎮 Финальный парсер с продолжением и одним драйвером")
    print("=" * 50)

    # Сессия 1: 500 игр
    print("\n🔵 СЕССИЯ 1: 500 игр")
    parser = SteamParserFinal()
    saved, errors = await parser.parse_page_and_save_immediate(
        "https://store.steampowered.com/specials/?l=russian&flavor=contenthub_topsellers",
        500
    )
    print(f"🎯 Сессия 1: {saved} игр сохранено, {errors} ошибок")

    # Закрываем драйвер после сессии
    await parser.close_driver()

    # Пауза
    print("\n⏸️ Пауза 10 мин...")
    await asyncio.sleep(600)

    # Сессия 2: еще 500 игр (продолжит с места остановки)
    print("\n🟢 СЕССИЯ 2: еще 500 игр")
    parser2 = SteamParserFinal()  # Автоматически загрузит прогресс
    saved2, errors2 = await parser2.parse_page_and_save_immediate(
        "https://store.steampowered.com/specials/?l=russian&flavor=contenthub_topsellers",
        500
    )
    print(f"🎯 Сессия 2: {saved2} игр сохранено, {errors2} ошибок")

    # Закрываем драйвер
    await parser2.close_driver()

    print("\n⏸️ Пауза 10 мин...")
    await asyncio.sleep(600)

    # Сессия 3: 500 игр
    print("\n🔵 СЕССИЯ 1: 500 игр")
    parser3 = SteamParserFinal()
    saved, errors = await parser3.parse_page_and_save_immediate(
        "https://store.steampowered.com/specials/?l=russian&flavor=contenthub_topsellers",
        500
    )
    print(f"🎯 Сессия 3: {saved} игр сохранено, {errors} ошибок")

    # Закрываем драйвер после сессии
    await parser3.close_driver()

    print(f"🎉 ВСЕГО: {saved + saved2} игр, {errors + errors2} ошибок")


if __name__ == "__main__":
    asyncio.run(main())