import json
import os


def save_progress(last_page_url: str, parsed_urls: list):
    """Сохраняет прогресс: последнюю страницу и URLs"""
    progress = {
        'last_page_url': last_page_url,
        'parsed_urls': parsed_urls,
        'total_parsed': len(parsed_urls)
    }
    with open('progress.json', 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False)
    print(f"💾 Прогресс сохранен: {len(parsed_urls)} игр, последняя страница: {last_page_url}")


def load_progress():
    """Загружает прогресс"""
    if not os.path.exists('progress.json'):
        return None, set(), 0

    with open('progress.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get('last_page_url'), set(data.get('parsed_urls', [])), data.get('total_parsed', 0)


def clear_progress():
    """Очищает прогресс"""
    if os.path.exists('progress.json'):
        os.remove('progress.json')
    print("🧹 Прогресс очищен")