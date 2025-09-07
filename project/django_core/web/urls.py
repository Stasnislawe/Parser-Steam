from django.urls import path, include
from .views import GameListView, load_more_games

urlpatterns = [
    path('', GameListView.as_view(), name='game_list'),
    path('load-more/', load_more_games, name='load_more_games'),
]