import asyncio
import logging
import sys
import os
import time
import re
from typing import List, Dict, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, current_dir)

from project.src.database.db_manager import DatabaseManager
from project.src.database.config import get_database_config
from project.src.utils.progress_manager import save_progress, load_progress


class SteamParserFinal:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        config = get_database_config()
        self.db_manager = DatabaseManager(config)
        self.processed_urls = set()
        self.driver = None

        # Загружаем прогресс
        self.last_page_url, parsed_urls_set, self.total_parsed = load_progress()

        # Объединяем обработанные URL из прогресса
        if parsed_urls_set:
            self.processed_urls.update(parsed_urls_set)

    async def init_driver(self):
        """Инициализация одного драйвера с правильными настройки"""
        if self.driver:
            return

        firefox_options = Options()
        firefox_options.add_argument("--headless")
        firefox_options.add_argument("--no-sandbox")
        firefox_options.add_argument("--disable-dev-shm-usage")
        firefox_options.add_argument("--window-size=1920,1080")

        self.driver = webdriver.Firefox(options=firefox_options)
        print("✅ Драйвер инициализирован")

    async def close_driver(self):
        """Закрывает драйвер"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            print("✅ Драйвер закрыт")

    async def parse_page_and_save_immediate(self, url: str, max_games: int = 500):
        """Парсит страницу с использованием одного драйвера и асинхронно обрабатывает игры"""
        await self.init_driver()
        saved = 0
        errors = 0

        try:
            # Загружаем последнюю страницу или начинаем сначала
            if self.last_page_url:
                print(f"🔁 Продолжаем с: {self.last_page_url}")
                self.driver.get(self.last_page_url)
            else:
                print("🚀 Начинаем с первой страницы")
                self.driver.get(url)

            time.sleep(5)

            games_count = 0
            click_count = 0
            max_clicks = 100
            page_number = 1

            while games_count < max_games and click_count < max_clicks:
                print(f"\n📄 Страница {page_number}, собрано игр: {games_count}/{max_games}")

                # Парсим игры с текущей страницы
                current_games = self._find_game_blocks()
                filtered_games = self._filter_unique_games(current_games)

                if not filtered_games:
                    print("⚠️ На странице не найдено игр")
                    break

                # Обрабатываем игры на текущей странице
                for game in filtered_games:
                    if games_count >= max_games:
                        break

                    game_url = game.get('url')
                    if game_url and game_url not in self.processed_urls:
                        print(f"🎮 Обрабатываем игру: {game.get('title', 'Unknown')}")

                        # Обрабатываем игру
                        success = await self.process_single_game_async(game, game_url)

                        if success:
                            saved += 1
                            self.total_parsed += 1
                            self.processed_urls.add(game_url)
                            print(
                                f"✅ [{self.total_parsed}] {game.get('title', 'Unknown')} - {game.get('current_price', '?')}")
                        else:
                            errors += 1

                        games_count += 1

                # Сохраняем прогресс после каждой страницы (сохраняем URL страницы)
                self.last_page_url = self.driver.current_url
                save_progress(self.last_page_url, list(self.processed_urls))
                print(f"💾 Прогресс: {saved}/{max_games} игр сохранено, всего: {self.total_parsed}")

                # Загружаем следующую страницу
                if games_count < max_games:
                    if await self._load_next_page():
                        click_count += 1
                        page_number += 1
                        print(f"🔽 Загружаем следующую страницу... ({click_count}/{max_clicks})")
                        time.sleep(3)
                    else:
                        print("⏹️ Кнопка 'Показать больше' не найдена - достигнут конец")
                        break

            return saved, errors

        except Exception as e:
            print(f"❌ Критическая ошибка: {e}")
            import traceback
            traceback.print_exc()
            return saved, errors
        finally:
            # Сохраняем финальный прогресс
            save_progress(self.last_page_url, list(self.processed_urls))

    async def process_single_game_async(self, game: Dict, game_url: str) -> bool:
        """Асинхронно обрабатывает одну игру (без создания нового драйвера)"""
        try:
            # Сохраняем текущий URL страницы с играми
            current_page_url = self.driver.current_url

            # Переходим на страницу игры для парсинга деталей
            self.driver.get(game_url)
            time.sleep(2)  # Ждем загрузки

            # Парсим детальную информацию
            details = self.parse_game_details(game_url)
            if details:
                game.update(details)

            # Проверяем обязательные поля
            if not self._validate_game_data(game):
                print(f"❌ Пропускаем игру с неполными данными: {game.get('title')}")
                # Возвращаемся на страницу с играми
                self.driver.get(current_page_url)
                time.sleep(1)
                return False

            # Сохраняем в базу
            result = await self.db_manager.save_game_async(game)

            # Возвращаемся на страницу с играми
            self.driver.get(current_page_url)
            time.sleep(1)

            return result is not None

        except Exception as e:
            print(f"❌ Ошибка обработки игры {game_url}: {e}")
            # Пытаемся вернуться на страницу с играми при ошибке
            try:
                self.driver.get(self.last_page_url)
                time.sleep(1)
            except:
                pass
            return False

    def _validate_game_data(self, game_data: Dict) -> bool:
        """Проверяет, что у игры есть все необходимые данные"""
        required_fields = ['title', 'current_price', 'url']
        return all(field in game_data and game_data[field] for field in required_fields)

    def _find_game_blocks(self) -> List[Dict]:
        """Ищет блоки с играми - РАБОЧАЯ ВЕРСИЯ"""
        games = []

        try:
            # Ищем все ссылки на игры
            game_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/app/')]")

            for link in game_links:
                try:
                    url = link.get_attribute('href')
                    if not url or 'steampowered.com/app/' not in url:
                        continue

                    # Пропускаем ссылки на отзывы и другие не-игры
                    if any(x in url for x in ['/reviews', '/news', '/discussions', '/workshop']):
                        continue

                    # Находим родительский контейнер игры
                    container = self._find_game_container(link)
                    if not container:
                        continue

                    game = self._parse_game_block(container, url)
                    if game and game['title'] != "Неизвестно":
                        games.append(game)

                except Exception as e:
                    print(f"⚠️ Ошибка обработки ссылки: {e}")
                    continue

        except Exception as e:
            print(f"❌ Ошибка поиска игровых блоков: {e}")

        return games

    def _find_game_container(self, element):
        """Находит контейнер игры"""
        try:
            # Поднимаемся на 3 уровня вверх чтобы найти основной контейнер
            container = element
            for _ in range(3):
                try:
                    container = container.find_element(By.XPATH, "./..")
                    # Проверяем, есть ли в контейнере цены и другая информация об игре
                    text = container.text.lower()
                    if any(x in text for x in ['руб', '₽', 'р.', '$', '€', '%']):
                        return container
                except:
                    break
        except:
            pass
        return None

    def _parse_game_block(self, container, url) -> Dict:
        """Парсит блок игры"""
        try:
            # Извлекаем название
            title = self._extract_title(container)

            # Пропускаем если это не игра (отзывы и т.д.)
            if any(x in title.lower() for x in ['отзыв', 'review', 'обзор', 'discussion', 'новость']):
                return None

            # Извлекаем цены и скидку
            price_data = self._extract_prices(container)

            # Извлекаем изображение
            image_url = self._extract_image(container)

            # Очищаем название от лишних символов
            clean_title = self._clean_game_title(title)

            return {
                'title': clean_title,
                'current_price': price_data.get('current_price', ''),
                'original_price': price_data.get('original_price', ''),
                'discount': price_data.get('discount', ''),
                'url': url.split('?')[0],  # Убираем параметры
                'image_url': image_url,
                'timestamp': time.time()
            }

        except Exception as e:
            print(f"⚠️ Ошибка парсинга блока игры: {e}")
            return None

    def _filter_unique_games(self, games: List[Dict]) -> List[Dict]:
        """Фильтрует уникальные игры по названию и URL"""
        filtered_games = []
        seen_titles = set()
        seen_urls = set()

        for game in games:
            # Пропускаем если нет названия или цены
            if not game['title'] or not game['current_price']:
                continue

            # Пропускаем не-игры
            title_lower = game['title'].lower()
            if any(x in title_lower for x in ['отзыв', 'review', 'обзор', 'discussion', 'новость', 'news']):
                continue

            # Создаем ключ для уникальности
            title_key = game['title'].lower().strip()
            url_key = game['url']

            # Пропускаем дубликаты
            if title_key in seen_titles or url_key in seen_urls:
                continue

            seen_titles.add(title_key)
            seen_urls.add(url_key)
            filtered_games.append(game)

        return filtered_games

    def parse_game_details(self, game_url: str) -> Dict:
        """Парсит детальную информацию об игре"""
        if not self.driver:
            return {}

        try:
            # Парсим детали
            details = {
                'categories': self._extract_categories(),
                'review_rating': self._extract_review_rating(),
                'review_count': self._extract_review_count(),
                'image_url': self._extract_main_image(),
                'description': self._extract_description()
            }

            return details

        except Exception as e:
            print(f"❌ Ошибка парсинга деталей: {e}")
            return {}

    def _extract_title(self, element):
        """Извлекает название игры"""
        try:
            # Ищем в заголовках
            for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                titles = element.find_elements(By.TAG_NAME, tag)
                for title in titles:
                    text = title.text.strip()
                    if text and len(text) > 3 and not any(x in text.lower() for x in ['отзыв', 'review']):
                        return text

            # Ищем в div с классами содержащими title
            title_elements = element.find_elements(
                By.XPATH, ".//*[contains(@class, 'Title') or contains(@class, 'title')]"
            )
            for elem in title_elements:
                text = elem.text.strip()
                if text and len(text) > 3 and not any(x in text.lower() for x in ['отзыв', 'review']):
                    return text

            # Ищем текст ссылки
            links = element.find_elements(By.XPATH, ".//a[contains(@href, '/app/')]")
            for link in links:
                text = link.text.strip()
                if text and len(text) > 3 and not any(x in text.lower() for x in ['отзыв', 'review']):
                    return text

        except:
            pass
        return "Неизвестно"

    def _extract_prices(self, element):
        """Извлекает цены и скидку"""
        try:
            text = element.text

            # Ищем скидку
            discount = ""
            discount_match = re.search(r'-\d+%', text)
            if discount_match:
                discount = discount_match.group(0)

            # Ищем цены в рублях
            prices = []
            price_patterns = [
                r'\d+[\s\.,]?\d*\s*руб',
                r'\d+[\s\.,]?\d*\s*₽',
                r'\d+[\s\.,]?\d*\s*р\.',
            ]

            for pattern in price_patterns:
                matches = re.findall(pattern, text)
                prices.extend(matches)

            current_price = prices[-1] if prices else ""
            original_price = prices[0] if len(prices) > 1 else ""

            return {
                'current_price': current_price,
                'original_price': original_price,
                'discount': discount
            }

        except:
            return {}

    def _extract_image(self, element):
        """Извлекает URL изображения"""
        try:
            images = element.find_elements(By.TAG_NAME, "img")
            for img in images:
                src = img.get_attribute('src')
                if src and ('header.jpg' in src or 'capsule' in src or 'steamstatic.com' in src):
                    return src
        except:
            pass
        return ""

    def _extract_description(self) -> str:
        """Извлекает описание игры"""
        try:
            # Ищем описание в различных элементах
            desc_selectors = [
                "//div[contains(@class, 'game_description')]",
                "//div[contains(@class, 'description')]",
                "//div[contains(@class, 'game_review_description')]",
                "//div[contains(@data-featuretarget, 'description')]",
                "//meta[contains(@property, 'og:description')]"
            ]

            for selector in desc_selectors:
                try:
                    if selector.startswith("//meta"):
                        element = self.driver.find_element(By.XPATH, selector)
                        desc = element.get_attribute('content')
                    else:
                        element = self.driver.find_element(By.XPATH, selector)
                        desc = element.text

                    if desc and len(desc) > 10:
                        # Очищаем и обрезаем описание
                        clean_desc = re.sub(r'\s+', ' ', desc).strip()
                        return clean_desc[:300] + "..." if len(clean_desc) > 300 else clean_desc

                except:
                    continue

        except Exception as e:
            print(f"⚠️ Ошибка извлечения описания: {e}")

        return ""

    def _extract_categories(self):
        """Извлекает категории игры"""
        try:
            categories = []
            category_elements = self.driver.find_elements(
                By.XPATH, "//div[contains(@class, 'game_category')]//a"
            )
            for elem in category_elements:
                category = elem.text.strip()
                if category:
                    categories.append(category)
            return categories
        except:
            return []

    def _extract_review_rating(self):
        """Извлекает рейтинг отзывов"""
        try:
            rating_elem = self.driver.find_element(
                By.XPATH, "//meta[contains(@itemprop, 'ratingValue')]"
            )
            return rating_elem.get_attribute('content')
        except:
            return ""

    def _extract_review_count(self):
        """Извлекает количество отзывов"""
        try:
            count_elem = self.driver.find_element(
                By.XPATH, "//meta[contains(@itemprop, 'reviewCount')]"
            )
            return count_elem.get_attribute('content')
        except:
            return ""

    def _extract_main_image(self):
        """Извлекает главное изображение"""
        try:
            img_elem = self.driver.find_element(
                By.XPATH, "//meta[contains(@property, 'og:image')]"
            )
            return img_elem.get_attribute('content')
        except:
            return ""

    def _clean_game_title(self, title: str) -> str:
        """Очищает название игры от лишних символов"""
        if not title:
            return title

        # Убираем лишние пробелы и переносы строк
        clean_title = re.sub(r'\s+', ' ', title).strip()

        # Убираем специфичные для Steam префиксы/суффиксы если есть
        clean_title = re.sub(r'(™|®|©|[-–—]\s*$)', '', clean_title).strip()

        return clean_title

    async def _load_next_page(self) -> bool:
        """Загружает следующую страницу - улучшенный поиск кнопки"""
        try:
            # Пробуем разные варианты поиска кнопки
            button_selectors = [
                "//button[contains(text(), 'Показать больше')]",
                "//button[contains(text(), 'Show more')]",
                "//button[contains(@class, 'show_more')]",
                "//a[contains(text(), 'Показать больше')]",
                "//a[contains(text(), 'Show more')]",
                "//div[contains(@class, 'show_more')]//button",
                "//div[contains(@class, 'load_more')]//button"
            ]

            for selector in button_selectors:
                try:
                    button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    if button.is_displayed():
                        button.click()
                        time.sleep(3)
                        print(f"✅ Найдена и нажата кнопка: {selector}")
                        return True
                except:
                    continue

            # Если не нашли кнопку, проверяем есть ли параметр offset в URL
            current_url = self.driver.current_url
            if 'offset=' in current_url:
                # Пробуем увеличить offset вручную
                match = re.search(r'offset=(\d+)', current_url)
                if match:
                    current_offset = int(match.group(1))
                    new_offset = current_offset + 12
                    new_url = re.sub(r'offset=\d+', f'offset={new_offset}', current_url)
                    self.driver.get(new_url)
                    time.sleep(3)
                    print(f"🔗 Перешли на следующую страницу: offset={new_offset}")
                    return True

            print("❌ Не удалось найти кнопку 'Показать больше'")
            return False

        except Exception as e:
            print(f"❌ Ошибка при загрузке следующей страницы: {e}")
            return False


async def main():
    logging.basicConfig(level=logging.INFO)

    parser = SteamParserFinal()

    print("🎮 Финальный парсер с одним драйвером и асинхронной обработкой")
    print("=" * 60)

    saved, errors = await parser.parse_page_and_save_immediate(
        url="https://store.steampowered.com/specials/?l=russian&flavor=contenthub_topsellers",
        max_games=500
    )

    print(f"\n🎯 Итоговый результат:")
    print(f"   ✅ Успешно сохранено: {saved} игр")
    print(f"   ❌ Ошибок: {errors}")
    print(f"   📊 Эффективность: {(saved / (saved + errors)) * 100:.1f}%" if (saved + errors) > 0 else "N/A")

    # Закрываем драйвер в конце
    await parser.close_driver()


if __name__ == "__main__":
    asyncio.run(main())