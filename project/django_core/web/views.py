from django.views.generic import TemplateView
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models import Q
from .models import SteamGames
import re


def parse_price(price_str):
    """Парсинг цен с запятыми и разными форматами"""
    if not price_str:
        return 0.0

    price_str = str(price_str).strip()
    price_str = price_str.replace(',', '.')  # Заменяем запятые на точки

    # Удаляем все символы кроме цифр и точки
    clean_price = re.sub(r'[^\d.]', '', price_str)

    # Удаляем лишние точки (оставляем только первую)
    parts = clean_price.split('.')
    if len(parts) > 1:
        clean_price = parts[0] + '.' + ''.join(parts[1:])

    try:
        return float(clean_price) if clean_price else 0.0
    except ValueError:
        return 0.0


class GameListView(TemplateView):
    template_name = 'games/game_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        games = self.get_filtered_queryset()

        paginator = Paginator(games, 12)
        page_number = self.request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        context.update({
            'games': page_obj,
            'title': 'Игры со скидками',
            'has_next': page_obj.has_next(),
            'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
        })
        return context

    def get_filtered_queryset(self):
        search = self.request.GET.get('search', '')
        sort = self.request.GET.get('sort', 'default')

        queryset = SteamGames.objects.filter(is_discounted=True)

        # Поиск
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(clean_title__icontains=search) |
                Q(description__icontains=search) |
                Q(short_description__icontains=search)
            )

        # Для сортировки по ценам - используем Python сортировку
        # Для остальных случаев - сортируем в БД
        if sort == 'discount_high':
            queryset = queryset.order_by('-discount_percent')
        elif sort == 'discount_low':
            queryset = queryset.order_by('discount_percent')
        elif sort == 'rating_high':
            queryset = queryset.order_by('-review_score', '-positive_reviews')
        elif sort == 'rating_low':
            queryset = queryset.order_by('review_score', 'positive_reviews')
        # Для 'price_low', 'price_high', 'popularity', 'default' - сортировка в Python

        return queryset


def load_more_games(request):
    page = int(request.GET.get('page', 1))
    search = request.GET.get('search', '')
    sort = request.GET.get('sort', 'default')

    # Получаем базовый queryset
    games = SteamGames.objects.filter(is_discounted=True)

    # Поиск
    if search:
        games = games.filter(
            Q(title__icontains=search) |
            Q(clean_title__icontains=search) |
            Q(description__icontains=search) |
            Q(short_description__icontains=search)
        )

    # Конвертируем в список для сложной сортировки
    games_list = list(games)

    if sort == 'price_low':
        games_list.sort(key=lambda x: parse_price(x.current_price))
    elif sort == 'price_high':
        games_list.sort(key=lambda x: parse_price(x.current_price), reverse=True)
    elif sort == 'popularity':
        # Не сортируем, оставляем исходный порядок
        pass
    elif sort == 'default':
        # По умолчанию - тоже порядок из БД
        pass
    else:
        # Для остальных сортировок уже отсортировано в БД
        pass

    # Пагинация
    paginator = Paginator(games_list, 12)
    try:
        page_obj = paginator.get_page(page)
    except:
        return JsonResponse({'games': [], 'has_next': False})

    games_data = []
    for game in page_obj:
        games_data.append({
            'title': game.title,
            'current_price': game.current_price,
            'original_price': game.original_price,
            'discount_percent': game.discount_percent,
            'image_url': game.image_url,
            'review_rating': game.review_rating,
            'review_count': game.review_count,
            'short_description': game.short_description or (game.description[:150] + '...' if game.description else ''),
            'description': game.description,
            'url': game.url,
            'release_date': game.release_date,
        })

    return JsonResponse({
        'games': games_data,
        'has_next': page_obj.has_next(),
        'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
    })