from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def get_main_keyboard():
    """Главная клавиатура"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎮 Скидки на игры")],
            [KeyboardButton(text="⚙️ Настройки"), KeyboardButton(text="🆘 Помощь")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие..."
    )


def get_discounts_keyboard():
    """Клавиатура раздела скидок"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔥 Самые популярные"), KeyboardButton(text="💰 Самые высокие скидки")],
            [KeyboardButton(text="▶️ Показать дальше"), KeyboardButton(text="🔙 Главное меню")]
        ],
        resize_keyboard=True
    )


def get_pagination_keyboard(has_more: bool = True):
    """Клавиатура пагинации"""
    keyboard = [
        [KeyboardButton(text="▶️ Показать дальше")],
        [KeyboardButton(text="🎮 Скидки на игры"), KeyboardButton(text="🔙 Главное меню")]
    ]
    if not has_more:
        keyboard[0][0] = KeyboardButton(text="📋 Все игры показаны")

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_settings_main_keyboard():
    """Главная клавиатура настроек"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎨 Формат отображения", callback_data="settings_display")],
            [InlineKeyboardButton(text="🔢 Количество игр", callback_data="settings_count")],
            [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="settings_back")]
        ]
    )


def get_display_settings_keyboard():
    """Клавиатура для настроек отображения"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📱 Минимальный", callback_data="display_minimal")],
            [InlineKeyboardButton(text="📊 Стандартный", callback_data="display_standard")],
            [InlineKeyboardButton(text="📋 Полный", callback_data="display_full")],
            [InlineKeyboardButton(text="🔙 Назад к настройкам", callback_data="settings_back_main")]
        ]
    )


def get_count_settings_keyboard():
    """Клавиатура для настроек количества игр"""
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