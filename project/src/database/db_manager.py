import json
import re
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy import create_engine, text, select, desc, func
from sqlalchemy.orm import sessionmaker
import asyncio
from concurrent.futures import ThreadPoolExecutor
from .models import Base, SteamGame, GamePriceHistory, create_tables, get_session
from .config import get_database_config


class DatabaseManager:
    """Менеджер для работы с базой данных Steam игр"""

    def __init__(self, config=None):
        self.config = config or get_database_config()
        self.engine = create_engine(
            self.config.connection_string,
            pool_size=self.config.pool_size,
            max_overflow=self.config.max_overflow,
            echo=self.config.echo
        )
        self.Session = sessionmaker(bind=self.engine)

    def init_database(self):
        """Инициализирует базу данных (создает таблицы)"""
        create_tables(self.engine)

    # ДОБАВЛЯЕМ НЕДОСТАЮЩИЕ МЕТОДЫ:
    def extract_app_id_from_url(self, url: str) -> Optional[int]:
        """
        Извлекает app_id из URL игры Steam
        Пример: https://store.steampowered.com/app/123456/Game_Name/ -> 123456
        """
        try:
            match = re.search(r'/app/(\d+)/', url)
            if match:
                return int(match.group(1))
        except:
            pass
        return None

    def parse_price(self, price_str: str) -> tuple:
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

    def parse_discount_percent(self, discount_str: str) -> int:
        """
        Парсит строку скидки в процент
        Пример: "-50%" -> 50
        """
        try:
            if not discount_str:
                return 0

            # Извлекаем числа из строки
            match = re.search(r'(\d+)', discount_str)
            if match:
                return int(match.group(1))
        except:
            pass
        return 0

    def save_game(self, game_data: Dict) -> Optional[SteamGame]:
        """Сохраняет игру в базу данных"""
        session = self.Session()
        try:
            print(f"💾 Пытаемся сохранить: {game_data.get('title')}")

            # Извлекаем app_id из URL
            app_id = self.extract_app_id_from_url(game_data.get('url', ''))
            print(f"   App ID: {app_id}")

            # Проверяем, существует ли игра уже
            existing_game = None
            if app_id:
                existing_game = session.query(SteamGame).filter(SteamGame.app_id == app_id).first()
            else:
                existing_game = session.query(SteamGame).filter(SteamGame.url == game_data['url']).first()

            if existing_game:
                print(f"   🎯 Игра уже существует, обновляем...")
                game = self._update_existing_game(existing_game, game_data)
            else:
                print(f"   🆕 Новая игра, создаем...")
                game = self._create_new_game(game_data, app_id)

            session.add(game)
            session.commit()

            print(f"   ✅ Успешно сохранено! ID: {game.id}")

            # Сохраняем истории цен
            self._save_price_history(game, session)

            return game

        except Exception as e:
            session.rollback()
            print(f"❌ Ошибка сохранения игры {game_data.get('title')}: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            session.close()

    def _create_new_game(self, game_data: Dict, app_id: Optional[int]) -> SteamGame:
        """Создает новую запись об игре"""
        current_price, currency = self.parse_price(game_data.get('current_price', ''))
        original_price, _ = self.parse_price(game_data.get('original_price', ''))
        discount_percent = self.parse_discount_percent(game_data.get('discount', ''))

        return SteamGame(
            app_id=app_id,
            title=game_data.get('title', ''),
            clean_title=game_data.get('title', '').lower().strip(),
            current_price=game_data.get('current_price', ''),
            original_price=game_data.get('original_price', ''),
            discount_percent=discount_percent,
            discount_amount=self._calculate_discount_amount(game_data),
            url=game_data.get('url', ''),
            image_url=game_data.get('image_url', ''),
            review_rating=game_data.get('review_rating', ''),
            review_count=game_data.get('review_count', ''),
            categories=json.dumps(game_data.get('categories', [])),
            description=game_data.get('description', ''),
            release_date=game_data.get('release_date', ''),
            is_discounted=discount_percent > 0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            last_checked=datetime.utcnow()
        )

    def _calculate_discount_amount(self, game_data: Dict) -> str:
        """Вычисляет сумму скидки"""
        try:
            current_price, _ = self.parse_price(game_data.get('current_price', ''))
            original_price, _ = self.parse_price(game_data.get('original_price', ''))

            if current_price and original_price and original_price > current_price:
                discount_amount = original_price - current_price
                return f"{discount_amount:.0f} руб"
        except:
            pass
        return ""

    def _update_existing_game(self, game: SteamGame, game_data: Dict) -> SteamGame:
        """Обновляет существующую запись об игре"""
        discount_percent = self.parse_discount_percent(game_data.get('discount', ''))

        game.current_price = game_data.get('current_price', game.current_price)
        game.original_price = game_data.get('original_price', game.original_price)
        game.description = game_data.get('description', game.description)
        game.discount_percent = discount_percent
        game.discount_amount = self._calculate_discount_amount(game_data)
        game.review_rating = game_data.get('review_rating', game.review_rating)
        game.review_count = game_data.get('review_count', game.review_count)
        game.categories = json.dumps(game_data.get('categories', []))
        game.image_url = game_data.get('image_url', game.image_url)
        game.updated_at = datetime.utcnow()
        game.last_checked = datetime.utcnow()
        game.is_discounted = discount_percent > 0

        return game

    async def save_game_async(self, game_data: Dict) -> Optional[SteamGame]:
        """Асинхронно сохраняет игру в базу данных"""
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(executor, self.save_game, game_data)

    async def save_games_batch_async(self, games_data: List[Dict]) -> List[Optional[SteamGame]]:
        """Асинхронно сохраняет пачку игр"""
        tasks = [self.save_game_async(game) for game in games_data]
        return await asyncio.gather(*tasks, return_exceptions=True)

    def _save_price_history(self, game: SteamGame, session):
        """Сохраняет историю цен игры"""
        try:
            # Проверяем, изменилась ли цена
            last_history = session.query(GamePriceHistory).filter(
                GamePriceHistory.app_id == game.app_id
            ).order_by(GamePriceHistory.recorded_at.desc()).first()

            if not last_history or last_history.current_price != game.current_price:
                price_history = GamePriceHistory(
                    app_id=game.app_id,
                    game_id=game.id,
                    current_price=game.current_price,
                    original_price=game.original_price,
                    discount_percent=game.discount_percent,
                    recorded_at=datetime.utcnow()
                )
                session.add(price_history)
                session.commit()
        except Exception as e:
            print(f"⚠️ Ошибка сохранения истории цен: {e}")

    def get_discounted_games(self, min_discount: int = 0) -> List[SteamGame]:
        """Возвращает игры со скидкой"""
        session = self.Session()
        try:
            return session.query(SteamGame).filter(
                SteamGame.is_discounted == True,
                SteamGame.discount_percent >= min_discount
            ).order_by(SteamGame.discount_percent.desc()).all()
        finally:
            session.close()

    def get_games_batch(self, offset: int = 0, limit: int = 12) -> List[Dict]:
        """Получает пачку игр из базы с пагинацией"""
        session = self.Session()
        try:
            result = session.query(SteamGame).order_by(
                desc(SteamGame.created_at)
            ).offset(offset).limit(limit).all()

            return [self._game_to_dict(game) for game in result]
        except Exception as e:
            print(f"Ошибка получения игр из БД: {e}")
            return []
        finally:
            session.close()

    def get_total_games_count(self) -> int:
        """Возвращает общее количество игр в базе"""
        session = self.Session()
        try:
            return session.query(SteamGame).count()
        except Exception as e:
            print(f"Ошибка подсчета игр: {e}")
            return 0
        finally:
            session.close()

    def search_games(self, query: str, limit: int = 20) -> List[Dict]:
        """Поиск игр по названию"""
        session = self.Session()
        try:
            result = session.query(SteamGame).filter(
                SteamGame.title.ilike(f"%{query}%")
            ).order_by(desc(SteamGame.created_at)).limit(limit).all()  # Используем created_at

            return [self._game_to_dict(game) for game in result]
        except Exception as e:
            print(f"Ошибка поиска игр: {e}")
            return []
        finally:
            session.close()

    def get_games_by_discount(self, min_discount: int = 0, limit: int = 20) -> List[Dict]:
        """Получает игры с минимальной скидкой"""
        session = self.Session()
        try:
            result = session.query(SteamGame).filter(
                SteamGame.discount_percent >= min_discount
            ).order_by(desc(SteamGame.discount_percent)).limit(limit).all()

            return [self._game_to_dict(game) for game in result]
        except Exception as e:
            print(f"Ошибка получения игр по скидке: {e}")
            return []
        finally:
            session.close()

    def _game_to_dict(self, game: SteamGame) -> Dict:
        """Конвертирует объект Game в словарь"""
        # Преобразуем datetime в строки
        created_at_str = game.created_at.isoformat() if game.created_at else None
        updated_at_str = game.updated_at.isoformat() if game.updated_at else None
        last_checked_str = game.last_checked.isoformat() if game.last_checked else None

        return {
            'id': game.id,
            'title': game.title,
            'current_price': game.current_price,
            'original_price': game.original_price,
            'discount': f"-{game.discount_percent}%" if game.discount_percent > 0 else "",
            'url': game.url,
            'image_url': game.image_url,
            'categories': game.categories,
            'review_rating': game.review_rating,
            'review_count': game.review_count,
            'description': game.description,
            'timestamp': created_at_str  # Используем строковое представление
        }

    # Асинхронные версии методов
    async def get_games_batch_async(self, offset: int = 0, limit: int = 12) -> List[Dict]:
        """Асинхронно получает пачку игр из базы"""
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(executor, self.get_games_batch, offset, limit)

    async def get_total_games_count_async(self) -> int:
        """Асинхронно возвращает общее количество игр"""
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(executor, self.get_total_games_count)

    async def search_games_async(self, query: str, limit: int = 20) -> List[Dict]:
        """Асинхронно ищет игры по названию"""
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(executor, self.search_games, query, limit)

    async def get_games_by_discount_async(self, min_discount: int = 0, limit: int = 20) -> List[Dict]:
        """Асинхронно получает игры со скидкой"""
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(executor, self.get_games_by_discount, min_discount, limit)

    def get_game_by_url(self, url: str) -> Optional[SteamGame]:
        """Находит игру по URL"""
        session = self.Session()
        try:
            return session.query(SteamGame).filter(SteamGame.url == url).first()
        finally:
            session.close()

    def get_most_popular_games(self, offset: int = 0, limit: int = 12) -> List[Dict]:
        """Получает самые популярные игры (по дате добавления)"""
        session = self.Session()
        try:
            result = session.query(SteamGame).order_by(
                desc(SteamGame.created_at)
            ).offset(offset).limit(limit).all()

            return [self._game_to_dict(game) for game in result]
        except Exception as e:
            print(f"Ошибка получения популярных игр: {e}")
            return []
        finally:
            session.close()

    def get_highest_discount_games(self, offset: int = 0, limit: int = 12) -> List[Dict]:
        """Получает игры с самыми высокими скидками"""
        session = self.Session()
        try:
            result = session.query(SteamGame).filter(
                SteamGame.discount_percent > 0
            ).order_by(
                desc(SteamGame.discount_percent)
            ).offset(offset).limit(limit).all()

            return [self._game_to_dict(game) for game in result]
        except Exception as e:
            print(f"Ошибка получения игр со скидками: {e}")
            return []
        finally:
            session.close()

    def get_total_discounted_games_count(self) -> int:
        """Возвращает количество игр со скидкой"""
        session = self.Session()
        try:
            return session.query(SteamGame).filter(
                SteamGame.discount_percent > 0
            ).count()
        except Exception as e:
            print(f"Ошибка подсчета игр со скидками: {e}")
            return 0
        finally:
            session.close()


# Синглтон для глобального доступа к менеджеру БД
db_manager = DatabaseManager()