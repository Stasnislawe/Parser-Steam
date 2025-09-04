from datetime import datetime
from typing import Optional
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class SteamGame(Base):
    """
    Модель для хранения информации об играх Steam со скидками
    """
    __tablename__ = 'steam_games'

    # Основные поля
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    app_id = sa.Column(sa.Integer, nullable=False, unique=True)  # ID игры в Steam
    title = sa.Column(sa.String(255), nullable=False, index=True)  # Название игры
    clean_title = sa.Column(sa.String(255), nullable=False, index=True)  # Очищенное название

    # Ценовая информация
    current_price = sa.Column(sa.String(50), nullable=False)  # Текущая цена
    original_price = sa.Column(sa.String(50), nullable=False)  # Оригинальная цена
    discount_percent = sa.Column(sa.Integer, nullable=False)  # Процент скидки
    discount_amount = sa.Column(sa.String(50))  # Сумма скидки в валюте

    # Ссылки
    url = sa.Column(sa.String(500), nullable=False, unique=True)  # URL игры
    image_url = sa.Column(sa.Text)  # URL основного изображения
    capsule_image = sa.Column(sa.Text)  # URL капсульного изображения

    # Рейтинги и отзывы
    review_rating = sa.Column(sa.String(100))  # Рейтинг отзывов
    review_count = sa.Column(sa.String(100))  # Количество отзывов
    positive_reviews = sa.Column(sa.Integer)  # Количество положительных отзывов
    total_reviews = sa.Column(sa.Integer)  # Общее количество отзывов
    review_score = sa.Column(sa.Integer)  # Оценка от 0 до 100

    # Категории и теги
    categories = sa.Column(sa.Text)  # JSON список категорий
    tags = sa.Column(sa.Text)  # JSON список тегов
    genres = sa.Column(sa.Text)  # JSON список жанров

    # Описание и детали
    description = sa.Column(sa.Text)  # Описание игры
    short_description = sa.Column(sa.Text)  # Короткое описание
    release_date = sa.Column(sa.String(100))  # Дата выхода
    developer = sa.Column(sa.String(200)) # Разработчик

    publisher = sa.Column(sa.String(200)) # Издатель

    # Системные требования
    min_requirements = sa.Column(sa.Text)  # Минимальные требования
    rec_requirements = sa.Column(sa.Text)  # Рекомендуемые требования

    # Мета-информация
    is_free = sa.Column(sa.Boolean, default=False)  # Бесплатная ли игра
    is_discounted = sa.Column(sa.Boolean, default=True)  # Есть ли скидка сейчас
    is_early_access = sa.Column(sa.Boolean, default=False)  # Ранний доступ

    # Временные метки
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)  # Когда добавлена запись
    updated_at = sa.Column(sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Когда обновлена
    last_checked = sa.Column(sa.DateTime, default=datetime.utcnow)  # Когда последний раз проверялась
    discount_start = sa.Column(sa.DateTime)  # Когда началась скидка
    discount_end = sa.Column(sa.DateTime)  # Когда закончится скидка

    # Дополнительные поля
    steam_rating = sa.Column(sa.String(50))  # Рейтинг Steam
    metacritic_score = sa.Column(sa.Integer)  # Оценка Metacritic
    supported_languages = sa.Column(sa.Text)  # JSON список языков
    platforms = sa.Column(sa.Text)  # JSON список платформ
    features = sa.Column(sa.Text)  # JSON список features (Multiplayer, etc.)

    # Для аналитики
    popularity_score = sa.Column(sa.Float)  # Оценка популярности
    weight = sa.Column(sa.Float, default=1.0)  # Вес для рекомендаций

    # Индексы для быстрого поиска
    __table_args__ = (
        sa.Index('idx_discount', 'discount_percent'),
        sa.Index('idx_price', 'current_price'),
        sa.Index('idx_reviews', 'review_score'),
        sa.Index('idx_created', 'created_at'),
        sa.Index('idx_updated', 'updated_at'),
        sa.Index('idx_is_discounted', 'is_discounted'),
    )

    def __repr__(self):
        return f"<SteamGame(id={self.id}, title='{self.title}', discount={self.discount_percent}%)>"


class GamePriceHistory(Base):
    """
    Модель для отслеживания истории цен игр
    """
    __tablename__ = 'game_price_history'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    app_id = sa.Column(sa.Integer, nullable=False, index=True)
    game_id = sa.Column(sa.Integer, sa.ForeignKey('steam_games.id'), index=True)

    current_price = sa.Column(sa.String(50), nullable=False)
    original_price = sa.Column(sa.String(50), nullable=False)
    discount_percent = sa.Column(sa.Integer, nullable=False)

    recorded_at = sa.Column(sa.DateTime, default=datetime.utcnow)

    # Индексы
    __table_args__ = (
        sa.Index('idx_price_history', 'app_id', 'recorded_at'),
    )


class GameCategory(Base):
    """
    Модель для категорий игр (нормализованная)
    """
    __tablename__ = 'game_categories'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    name = sa.Column(sa.String(100), nullable=False, unique=True)
    slug = sa.Column(sa.String(100), nullable=False, unique=True)

    def __repr__(self):
        return f"<GameCategory(id={self.id}, name='{self.name}')>"


class GameCategoryAssociation(Base):
    """
    Связь многие-ко-многим между играми и категориями
    """
    __tablename__ = 'game_category_association'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    game_id = sa.Column(sa.Integer, sa.ForeignKey('steam_games.id'), nullable=False)
    category_id = sa.Column(sa.Integer, sa.ForeignKey('game_categories.id'), nullable=False)

    __table_args__ = (
        sa.UniqueConstraint('game_id', 'category_id', name='uq_game_category'),
    )


# Утилитные функции для работы с базой
def create_tables(engine):
    """Создает все таблицы в базе данных"""
    Base.metadata.create_all(engine)
    print("✅ Таблицы созданы успешно!")


def get_session(engine):
    """Возвращает сессию для работы с базой"""
    Session = sessionmaker(bind=engine)
    return Session()


def extract_app_id_from_url(url: str) -> Optional[int]:
    """
    Извлекает app_id из URL игры Steam
    Пример: https://store.steampowered.com/app/123456/Game_Name/ -> 123456
    """
    try:
        import re
        match = re.search(r'/app/(\d+)/', url)
        if match:
            return int(match.group(1))
    except:
        pass
    return None


def parse_price(price_str: str) -> tuple:
    """
    Парсит строку цены в числовое значение
    Возвращает: (цена_в_рублях, валюта)
    """
    try:
        if not price_str:
            return 0.0, 'RUB'

        # Убираем пробелы и символы валюты
        clean_price = price_str.replace(' ', '').replace('руб', '').replace('₽', '').replace('р.', '')

        # Заменяем запятую на точку
        clean_price = clean_price.replace(',', '.')

        return float(clean_price), 'RUB'
    except:
        return 0.0, 'RUB'


def parse_discount_percent(discount_str: str) -> int:
    """
    Парсит строку скидки в процент
    Пример: "-50%" -> 50
    """
    try:
        if not discount_str:
            return 0

        # Извлекаем числа из строки
        import re
        match = re.search(r'(\d+)', discount_str)
        if match:
            return int(match.group(1))
    except:
        pass
    return 0


@staticmethod
def extract_app_id_from_url(url: str) -> Optional[int]:
    """
    Извлекает app_id из URL игры Steam
    Пример: https://store.steampowered.com/app/123456/Game_Name/ -> 123456
    """
    try:
        import re
        match = re.search(r'/app/(\d+)/', url)
        if match:
            return int(match.group(1))
    except:
        pass
    return None


@staticmethod
def parse_price(price_str: str) -> tuple:
    """
    Парсит строку цены в числовое значение
    Возвращает: (цена_в_рублях, валюта)
    """
    try:
        if not price_str:
            return 0.0, 'RUB'

        # Убираем пробелы и символы валюты
        clean_price = price_str.replace(' ', '').replace('руб', '').replace('₽', '').replace('р.', '')

        # Заменяем запятую на точку
        clean_price = clean_price.replace(',', '.')

        return float(clean_price), 'RUB'
    except:
        return 0.0, 'RUB'


@staticmethod
def parse_discount_percent(discount_str: str) -> int:
    """
    Парсит строку скидки в процент
    Пример: "-50%" -> 50
    """
    try:
        if not discount_str:
            return 0

        # Извлекаем числа из строки
        import re
        match = re.search(r'(\d+)', discount_str)
        if match:
            return int(match.group(1))
    except:
        pass
    return 0


# Пример использования
if __name__ == "__main__":
    # Создаем движок базы данных (SQLite для примера)
    engine = sa.create_engine('sqlite:///steam_games.db', echo=True)

    # Создаем таблицы
    create_tables(engine)

    # Пример создания сессии
    session = get_session(engine)

    print("🎮 Модель базы данных готова!")
    print("📊 Таблицы:")
    print("   - steam_games (основная таблица с играми)")
    print("   - game_price_history (история цен)")
    print("   - game_categories (категории)")
    print("   - game_category_association (связи игр с категориями)")

