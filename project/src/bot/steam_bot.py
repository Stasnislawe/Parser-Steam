import json
import re

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import F
from aiogram.enums import ParseMode
from project.src.database.db_manager import DatabaseManager
from project.src.database.config import get_database_config
from project.config.settings import SettingsManager, DisplayMode, GamesCount, UserPagination, GameMode
from project.src.bot.keyboards import (
    get_main_keyboard, get_discounts_keyboard, get_pagination_keyboard,
    get_settings_main_keyboard, get_display_settings_keyboard, get_count_settings_keyboard
)
import asyncio
import logging


class SteamBot:
    def __init__(self, token: str):
        # Инициализация бота с токеном
        self.bot = Bot(token=token)
        self.dp = Dispatcher()
        self.logger = logging.getLogger(__name__)

        # Подключение к базе данных
        config = get_database_config()
        self.db_manager = DatabaseManager(config)

        # Менеджер настроек пользователей
        self.settings_manager = SettingsManager()

        # Настройка обработчиков команд
        self.setup_handlers()

    def setup_handlers(self):
        """Настройка всех обработчиков сообщений и callback'ов"""

        # ==================== ОБРАБОТЧИКИ СООБЩЕНИЙ ====================

        # Главное меню - запуск бота или возврат в главное меню
        @self.dp.message(Command("start"))
        @self.dp.message(F.text == "🔙 Главное меню")
        async def main_menu(message: types.Message):
            """Показывает главное меню с приветствием и основной клавиатурой"""
            await message.answer(
                "👋 Добро пожаловать в Steam бот!\n\n"
                "🎮 Здесь вы найдете лучшие скидки из Steam магазина",
                reply_markup=get_main_keyboard()  # Устанавливает основную клавиатуру
            )

        # Раздел скидок - выбор типа отображения игр
        @self.dp.message(F.text == "🎮 Скидки на игры")
        async def discounts_section(message: types.Message):
            """Показывает клавиатуру выбора типа отображения игр"""
            await message.answer(
                "🎮 Выберите тип отображения игр:",
                reply_markup=get_discounts_keyboard()  # Клавиатура с вариантами отображения
            )

        # Показать популярные игры
        @self.dp.message(F.text == "🔥 Самые популярные")
        async def popular_games(message: types.Message):
            """Загружает и показывает самые популярные игры"""
            await self._show_games_by_mode(message, GameMode.POPULAR)

        # Показать игры с самыми высокими скидками
        @self.dp.message(F.text == "💰 Самые высокие скидки")
        async def discounted_games(message: types.Message):
            """Загружает и показывает игры с максимальными скидками"""
            await self._show_games_by_mode(message, GameMode.DISCOUNTED)

        # Пагинация - показать следующую партию игр
        @self.dp.message(F.text == "▶️ Показать дальше")
        async def show_next_batch(message: types.Message):
            """Загружает и показывает следующую группу игр"""
            await self._show_next_batch(message)

        # Открыть настройки
        @self.dp.message(F.text == "⚙️ Настройки")
        async def settings_button(message: types.Message):
            """Показывает главное меню настроек"""
            await self._show_settings(message)

        # Показать справку
        @self.dp.message(F.text == "🆘 Помощь")
        async def help_button(message: types.Message):
            """Показывает справочную информацию о командах бота"""
            help_text = (
                "📖 <b>Помощь по боту:</b>\n\n"
                "🎮 <b>Скидки на игры</b> - Раздел с играми\n"
                "🔥 <b>Самые популярные</b> - Новые игры\n"
                "💰 <b>Самые высокие скидки</b> - Лучшие скидки\n"
                "▶️ <b>Показать дальше</b> - Следующая партия игр\n"
                "⚙️ <b>Настройки</b> - Настройки отображения\n"
                "🔙 <b>Главное меню</b> - Вернуться назад"
            )
            await message.answer(help_text, parse_mode=ParseMode.HTML)

        # ==================== ОБРАБОТЧИКИ CALLBACK'ОВ ====================

        # Главные настройки (формат, количество игр)
        @self.dp.callback_query(F.data.startswith("settings_"))
        async def settings_callback(callback: types.CallbackQuery):
            """Обрабатывает callback'и из главного меню настроек"""
            await self._handle_settings_callback(callback)

        # Настройки отображения (минимальный, стандартный, полный)
        @self.dp.callback_query(F.data.startswith("display_"))
        async def display_callback(callback: types.CallbackQuery):
            """Обрабатывает callback'и для изменения формата отображения"""
            await self._handle_display_callback(callback)

        # Настройки количества игр (1, 2, 3, 6, 12)
        @self.dp.callback_query(F.data.startswith("count_"))
        async def count_callback(callback: types.CallbackQuery):
            """Обрабатывает callback'и для изменения количества показываемых игр"""
            await self._handle_count_callback(callback)

    async def _show_games_by_mode(self, message: types.Message, game_mode: GameMode):
        """
        Загружает и показывает игры в зависимости от выбранного режима
        GameMode.POPULAR - самые популярные игры
        GameMode.DISCOUNTED - игры с самыми высокими скидками
        """
        user_id = message.from_user.id
        settings = self.settings_manager.get_user_settings(user_id)  # Получаем настройки пользователя

        await message.answer("🔄 Загружаю игры...")

        try:
            # Выбор метода получения игр в зависимости от режима
            if game_mode == GameMode.POPULAR:
                games = self.db_manager.get_most_popular_games(limit=settings.games_count.value)
                total_count = self.db_manager.get_total_games_count()
                mode_name = "популярные"
            else:
                games = self.db_manager.get_highest_discount_games(limit=settings.games_count.value)
                total_count = self.db_manager.get_total_discounted_games_count()
                mode_name = "со скидками"

            # Проверка наличия игр
            if not games:
                await message.answer(f"❌ Не найдено {mode_name} игр.")
                return

            # Сохраняем информацию о пагинации для пользователя
            settings.pagination = UserPagination(
                current_games=games,  # Текущий список игр
                current_index=0,  # Текущий индекс (для постраничного вывода)
                all_loaded_games=games,  # Все загруженные игры
                total_count=total_count,  # Общее количество игр в базе
                offset=len(games),  # Смещение для следующей загрузки
                has_more=len(games) < total_count,  # Есть ли еще игры для загрузки
                game_mode=game_mode  # Текущий режим отображения
            )
            self.settings_manager.update_pagination(user_id, settings.pagination)

            # Показываем первую партию игр
            await self._show_current_batch(message, settings)

        except Exception as e:
            self.logger.error(f"Ошибка загрузки игр: {e}")
            await message.answer("❌ Ошибка при загрузке игр")

    async def _show_next_batch(self, message: types.Message):
        """Загружает и показывает следующую партию игр"""
        user_id = message.from_user.id
        settings = self.settings_manager.get_user_settings(user_id)

        # Проверка возможности загрузки следующих игр
        if not settings.pagination or not settings.pagination.has_more:
            await message.answer("📋 Все игры уже показаны!")
            return

        await message.answer("📥 Загружаю следующие игры...")

        try:
            # Загрузка следующих игр в зависимости от режима
            if settings.pagination.game_mode == GameMode.POPULAR:
                new_games = self.db_manager.get_most_popular_games(
                    offset=settings.pagination.offset,  # Смещение для пагинации
                    limit=settings.games_count.value  # Количество игр для загрузки
                )
            else:
                new_games = self.db_manager.get_highest_discount_games(
                    offset=settings.pagination.offset,
                    limit=settings.games_count.value
                )

            # Проверка успешности загрузки
            if not new_games:
                settings.pagination.has_more = False
                self.settings_manager.update_pagination(user_id, settings.pagination)
                await message.answer("❌ Не удалось загрузить дополнительные игры.")
                return

            # Обновление информации о пагинации
            settings.pagination.all_loaded_games.extend(new_games)  # Добавляем новые игры к общему списку
            settings.pagination.offset += len(new_games)  # Увеличиваем смещение
            settings.pagination.has_more = settings.pagination.offset < settings.pagination.total_count  # Проверяем, есть ли еще игры
            self.settings_manager.update_pagination(user_id, settings.pagination)

            # Показываем новые игры
            start_index = len(settings.pagination.all_loaded_games) - len(new_games)
            await self._show_games_batch(message, settings, start_index)

        except Exception as e:
            self.logger.error(f"Ошибка загрузки дополнительных игр: {e}")
            await message.answer("❌ Ошибка при загрузке игр")

    async def _show_current_batch(self, message: types.Message, settings):
        """Показывает текущую партию игр (начиная с первой)"""
        await self._show_games_batch(message, settings, 0)

    async def _show_games_batch(self, message: types.Message, settings, start_index: int):
        """Показывает игры из указанного диапазона с форматированием"""
        games = settings.pagination.all_loaded_games[start_index:]

        if not games:
            await message.answer("❌ Нет игр для показа.")
            return

        # Поочередный вывод каждой игры с задержкой
        for i, game in enumerate(games, start_index + 1):
            response = self._format_game_response(game, settings.display_mode)  # Форматируем информацию об игре
            response += f"\n\n📋 {i}/{settings.pagination.total_count}"  # Добавляем счетчик
            await message.answer(response, parse_mode=ParseMode.HTML)
            await asyncio.sleep(0.3)  # Небольшая задержка между сообщениями

        # Сообщение о статусе загрузки
        if settings.pagination.has_more:
            await message.answer(
                f"✅ Показано {len(games)} игр. Всего: {settings.pagination.total_count}\n"
                "▶️ Нажмите 'Показать дальше' для продолжения",
                reply_markup=get_pagination_keyboard(True)  # Клавиатура с активной кнопкой "Дальше"
            )
        else:
            await message.answer(
                f"✅ Все игры показаны! Всего: {settings.pagination.total_count}",
                reply_markup=get_pagination_keyboard(False)  # Клавиатура с неактивной кнопкой
            )

    def _format_game_response(self, game: dict, display_mode: DisplayMode) -> str:
        """
        Форматирует информацию об игре в красивый текст
        В зависимости от режима отображения показывает разное количество информации
        """
        # Извлечение данных об игре из словаря
        title = game.get('title', 'Без названия')
        current_price = game.get('current_price', '?')
        discount = game.get('discount', '')
        url = game.get('url', '')
        original_price = game.get('original_price', '')
        image_url = game.get('image_url', '')
        description = game.get('description', '')
        categories = game.get('categories', '[]')

        # ДОБАВИМ ОТЛАДОЧНУЮ ПЕЧАТЬ ДЛЯ ПРОВЕРКИ
        print(f"DEBUG: Режим отображения: {display_mode}")
        print(f"DEBUG: DisplayMode.MINIMAL = {DisplayMode.MINIMAL}")
        print(f"DEBUG: display_mode == DisplayMode.MINIMAL: {display_mode == DisplayMode.MINIMAL}")

        # МИНИМАЛЬНЫЙ РЕЖИМ - только самое важное
        if display_mode == DisplayMode.MINIMAL:
            response = f"🎮 <b>{title}</b>\n\n"

            # Цены и скидка
            if original_price and original_price != current_price:
                response += f"💰 <s>{original_price}</s> → <b>{current_price}</b>\n"
                if discount:
                    response += f"🔥 <b>{discount}</b>\n"
            else:
                response += f"💰 <b>{current_price}</b>\n"

            # Добавляем ссылку
            response += f"\n🔗 <a href='{url}'>Купить в Steam</a>"
            return response

        # СТАНДАРТНЫЙ РЕЖИМ - базовая информация
        elif display_mode == DisplayMode.STANDARD:
            response = f"🎮 <b>{title}</b>\n\n"

            # Цены
            if original_price and original_price != current_price:
                response += f"💰 <s>{original_price}</s> → <b>{current_price}</b>\n"
            else:
                response += f"💰 <b>{current_price}</b>\n"

            # Скидка
            if discount:
                response += f"🔥 <b>{discount}</b>\n\n"
            else:
                response += "\n"

            # Изображение и ссылка
            if image_url:
                response += f"🖼️ <a href='{image_url}'>Изображение</a>\n"
            response += f"🔗 <a href='{url}'>Купить в Steam</a>"
            return response

        # ПОЛНЫЙ РЕЖИМ - вся информация
        elif display_mode == DisplayMode.FULL:
            response = f"🎮 <b>{title}</b>\n\n"

            # Цены
            if original_price and original_price != current_price:
                response += f"📊 <b>Цена:</b> <s>{original_price}</s> → <b>{current_price}</b>\n"
            else:
                response += f"📊 <b>Цена:</b> {current_price}\n"

            # Скидка
            if discount:
                response += f"🎯 <b>Скидка:</b> {discount}\n\n"
            else:
                response += "\n"

            # Категории
            categories_text = self._parse_categories(categories)
            if categories_text:
                response += f"🏷️ <b>Категории:</b> {categories_text}\n"

            # Описание
            if description and len(description.strip()) > 10:
                clean_desc = re.sub(r'<[^>]*>', '', description)
                clean_desc = re.sub(r'\s+', ' ', clean_desc).strip()
                short_desc = clean_desc[:150] + "..." if len(clean_desc) > 150 else clean_desc
                response += f"📝 <b>Описание:</b> {short_desc}\n\n"

            # Изображение и ссылка
            if image_url:
                response += f"🖼️ <b>Изображение:</b> <a href='{image_url}'>Посмотреть</a>\n"
            response += f"🔗 <b>Ссылка:</b> <a href='{url}'>Перейти к игре</a>"
            return response

        # fallback - если какой-то неизвестный режим
        return f"🎮 <b>{title}</b>\n💰 <b>{current_price}</b>\n🔗 <a href='{url}'>Купить в Steam</a>"

    def _parse_categories(self, categories_data: str) -> str:
        """
        Парсит категории игр из JSON строки
        Возвращает строку с первыми 3 категориями
        """
        if not categories_data or categories_data == '[]':
            return ""

        try:
            # Попытка парсинга JSON
            categories_list = json.loads(categories_data)
            if isinstance(categories_list, list) and categories_list:
                # Берем первые 3 категории и объединяем в строку
                return ', '.join(str(cat) for cat in categories_list[:3])
        except (json.JSONDecodeError, TypeError):
            # Если не JSON, пытаемся обработать как обычную строку
            try:
                clean_categories = categories_data.strip('[]"\'')  # Очистка от лишних символов
                if clean_categories:
                    categories = [cat.strip() for cat in clean_categories.split(',')]
                    return ', '.join(categories[:3])
            except:
                pass

        return ""

    async def _show_settings(self, message: types.Message):
        """Показывает главное меню настроек с текущими значениями"""
        user_id = message.from_user.id
        settings = self.settings_manager.get_user_settings(user_id)

        # Формирование текста с текущими настройками
        text = (
            "⚙️ <b>Главное меню настроек</b>\n\n"
            f"🎨 <b>Формат:</b> {self._get_display_mode_name(settings.display_mode)}\n"
            f"🔢 <b>Количество игр:</b> {settings.games_count.value}\n\n"
            "Выбери что хочешь настроить:"
        )

        await message.answer(
            text,
            reply_markup=get_settings_main_keyboard(),  # Клавиатура основных настроек
            parse_mode=ParseMode.HTML
        )

    def get_settings_main_keyboard(self):
        """Создает inline-клавиатуру для главного меню настроек"""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🎨 Формат отображения", callback_data="settings_display")],
                [InlineKeyboardButton(text="🔢 Количество игр", callback_data="settings_count")],
                [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="settings_back")]
            ]
        )

    def get_display_settings_keyboard(self):
        """Создает inline-клавиатуру для настроек формата отображения"""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📱 Минимальный", callback_data="display_minimal")],
                [InlineKeyboardButton(text="📊 Стандартный", callback_data="display_standard")],
                [InlineKeyboardButton(text="📋 Полный", callback_data="display_full")],
                [InlineKeyboardButton(text="🔙 Назад к настройкам", callback_data="settings_back_main")]
            ]
        )

    def get_count_settings_keyboard(self):
        """Создает inline-клавиатуру для настроек количества игр"""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="1 игра", callback_data="count_1")],
                [InlineKeyboardButton(text="2 игры", callback_data="count_2")],
                [InlineKeyboardButton(text="3 игры", callback_data="count_3")],
                [InlineKeyboardButton(text="6 игр", callback_data="count_6")],
                [InlineKeyboardButton(text="12 игр", callback_data="count_12")],
                [InlineKeyboardButton(text="🔙 Назад к настройкам", callback_data="settings_back_main")]
            ]
        )

    async def _handle_settings_callback(self, callback: types.CallbackQuery):
        """Обрабатывает callback'и из главного меню настроек"""
        action = callback.data

        # Закрытие настроек
        if action == "settings_back":
            await callback.message.delete()
            await callback.answer("Настройки закрыты")
            return

        # Возврат в главное меню настроек
        if action == "settings_back_main":
            await self._show_main_settings(callback)
            return

        user_id = callback.from_user.id

        # Обработка выбора раздела настроек
        if action == "settings_display":
            await self._show_display_settings(callback)
        elif action == "settings_count":
            await self._show_count_settings(callback)

    async def _handle_display_callback(self, callback: types.CallbackQuery):
        """Обрабатывает callback'и для изменения формата отображения"""
        action = callback.data.split("_")[1]  # Извлекаем тип формата (minimal/standard/full)
        user_id = callback.from_user.id

        # Установка выбранного формата отображения
        if action == "minimal":
            self.settings_manager.set_display_mode(user_id, DisplayMode.MINIMAL)
            mode_name = "Минимальный"
            mode_desc = "Только название и скидка"
        elif action == "standard":
            self.settings_manager.set_display_mode(user_id, DisplayMode.STANDARD)
            mode_name = "Стандартный"
            mode_desc = "Название, скидка, изображение, ссылка"
        elif action == "full":
            self.settings_manager.set_display_mode(user_id, DisplayMode.FULL)
            mode_name = "Полный"
            mode_desc = "Вся информация с оформлением"
        else:
            await callback.answer("Неизвестное действие")
            return

        # Подтверждение изменения и возврат в меню настроек
        await callback.message.edit_text(
            f"✅ <b>Формат изменен</b>\n\n"
            f"📱 <b>Режим:</b> {mode_name}\n"
            f"📝 <b>Описание:</b> {mode_desc}\n\n"
            "Выбери что хочешь настроить:",
            reply_markup=get_settings_main_keyboard(),
            parse_mode=ParseMode.HTML
        )
        await callback.answer()

    async def _handle_count_callback(self, callback: types.CallbackQuery):
        """Обрабатывает callback'и для изменения количества показываемых игр"""
        count_str = callback.data.split("_")[1]  # Извлекаем количество
        user_id = callback.from_user.id

        try:
            count = int(count_str)
            games_count = GamesCount(count)
            self.settings_manager.set_games_count(user_id, games_count)  # Сохраняем настройку

            # Подтверждение изменения
            await callback.message.edit_text(
                f"✅ <b>Количество игр изменено</b>\n\n"
                f"🔢 Теперь буду показывать: <b>{count} игр</b>\n\n"
                "Выбери что хочешь настроить:",
                reply_markup=get_settings_main_keyboard(),
                parse_mode=ParseMode.HTML
            )
            await callback.answer()

        except ValueError:
            await callback.answer("Неверное количество")

    async def _show_main_settings(self, callback: types.CallbackQuery):
        """Показывает главное меню настроек (для callback'ов)"""
        user_id = callback.from_user.id
        settings = self.settings_manager.get_user_settings(user_id)

        text = (
            "⚙️ <b>Главное меню настроек</b>\n\n"
            f"🎨 <b>Формат:</b> {self._get_display_mode_name(settings.display_mode)}\n"
            f"🔢 <b>Количество игр:</b> {settings.games_count.value}\n\n"
            "Выбери что хочешь настроить:"
        )

        await callback.message.edit_text(
            text,
            reply_markup=get_settings_main_keyboard(),
            parse_mode=ParseMode.HTML
        )

    async def _show_display_settings(self, callback: types.CallbackQuery):
        """Показывает меню настроек формата отображения"""
        user_id = callback.from_user.id
        settings = self.settings_manager.get_user_settings(user_id)

        text = (
            "🎨 <b>Настройки формата отображения</b>\n\n"
            f"Текущий режим: <b>{self._get_display_mode_name(settings.display_mode)}</b>\n\n"
            "📱 <b>Минимальный</b> - только название и скидка\n"
            "📊 <b>Стандартный</b> - название, скидка, изображение, ссылка\n"
            "📋 <b>Полный</b> - вся информация с оформлением\n\n"
            "Выбери новый формат:"
        )

        await callback.message.edit_text(
            text,
            reply_markup=self.get_display_settings_keyboard(),
            parse_mode=ParseMode.HTML
        )

    async def _show_count_settings(self, callback: types.CallbackQuery):
        """Показывает меню настроек количества игр"""
        user_id = callback.from_user.id
        settings = self.settings_manager.get_user_settings(user_id)

        text = (
            "🔢 <b>Настройки количества игр</b>\n\n"
            f"Текущее количество: <b>{settings.games_count.value} игр</b>\n\n"
            "Выбери сколько игр показывать при запросе скидок:"
        )

        await callback.message.edit_text(
            text,
            reply_markup=self.get_count_settings_keyboard(),
            parse_mode=ParseMode.HTML
        )

    def _get_display_mode_name(self, mode: DisplayMode) -> str:
        """Возвращает читаемое название режима отображения"""
        names = {
            DisplayMode.MINIMAL: "📱 Минимальный",
            DisplayMode.STANDARD: "📊 Стандартный",
            DisplayMode.FULL: "📋 Полный"
        }
        return names.get(mode, "📊 Стандартный")

    async def start(self):
        """Запуск бота и начало обработки сообщений"""
        try:
            self.logger.info("Бот запускается...")
            await self.dp.start_polling(self.bot)  # Запуск бесконечного цикла опроса
        except Exception as e:
            self.logger.error(f"Ошибка при запуске бота: {e}")
        finally:
            await self.bot.session.close()  # Корректное закрытие сессии