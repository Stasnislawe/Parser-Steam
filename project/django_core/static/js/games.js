// games.js - с фильтрацией и сортировкой
let currentPage = GAME_CONFIG.nextPage;
let isLoading = false;
let hasMore = GAME_CONFIG.hasNext;
let currentFilters = {
    search: '',
    sort: 'default'
};

// Функции для бокового меню
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('overlay');
    sidebar.classList.toggle('sidebar-open');
    overlay.classList.toggle('overlay-open');
}

function applyFilters() {
    const searchValue = document.getElementById('searchInput').value.trim();
    const sortValue = document.getElementById('sortSelect').value;

    currentFilters = {
        search: searchValue,
        sort: sortValue
    };

    // Очищаем контейнер и загружаем заново с фильтрами
    const gamesContainer = document.querySelector('.games-container');
    gamesContainer.innerHTML = '';

    currentPage = 1;
    hasMore = true;
    isLoading = false;

    loadMoreGames();
    toggleSidebar();
}

function resetFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('sortSelect').value = 'default';

    currentFilters = {
        search: '',
        sort: 'default'
    };

    // Очищаем и загружаем заново
    const gamesContainer = document.querySelector('.games-container');
    gamesContainer.innerHTML = '';

    currentPage = 1;
    hasMore = true;
    isLoading = false;

    loadMoreGames();
    toggleSidebar();
}

function loadMoreGames() {
    if (isLoading || !hasMore) return;

    isLoading = true;
    const loadingDiv = document.getElementById('loading');
    if (loadingDiv) {
        loadingDiv.style.display = 'block';
    }

    // Добавляем параметры фильтрации
    const params = new URLSearchParams({
        page: currentPage,
        search: currentFilters.search,
        sort: currentFilters.sort
    });

    fetch(`${GAME_CONFIG.loadMoreUrl}?${params}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.games && data.games.length > 0) {
                const gamesContainer = document.querySelector('.games-container');

                data.games.forEach(game => {
                    const gameCard = createGameCard(game);
                    gamesContainer.appendChild(gameCard);
                });

                hasMore = data.has_next;
                currentPage = data.next_page || currentPage + 1;
            } else {
                hasMore = false;
            }

            isLoading = false;
            if (loadingDiv) {
                loadingDiv.style.display = 'none';
            }

            if (!hasMore && loadingDiv) {
                loadingDiv.innerHTML = '<p class="text-gray-400">Все игры загружены!</p>';
                loadingDiv.style.display = 'block';
            }
        })
        .catch(error => {
            console.error('Error loading games:', error);
            isLoading = false;
            const loadingDiv = document.getElementById('loading');
            if (loadingDiv) {
                loadingDiv.style.display = 'none';
            }
        });
}

function createGameCard(game) {
    const gameCard = document.createElement('div');
    gameCard.className = 'game-card bg-dark-100 rounded-lg shadow-lg overflow-hidden hover:shadow-xl transition-shadow duration-300';

    let imageHtml = '';
    if (game.image_url) {
        imageHtml = `<img src="${game.image_url}" alt="${game.title}"
                     class="game-image w-full h-48 object-cover"
                     onerror="this.src='https://via.placeholder.com/300x200/1a202c/2d3748?text=No+Image'">`;
    } else {
        imageHtml = `<div class="w-full h-48 bg-dark-300 flex items-center justify-center">
                        <span class="text-gray-400">No Image</span>
                     </div>`;
    }

    let pricesHtml = `<span class="current-price text-green-400 font-bold text-xl">${game.current_price || ''}</span>`;
    if (game.original_price && game.original_price !== game.current_price) {
        pricesHtml += `<span class="original-price text-gray-400 line-through text-sm">${game.original_price}</span>`;
    }
    if (game.discount_percent) {
        pricesHtml += `<span class="discount bg-red-600 text-white px-2 py-1 rounded text-xs font-bold">-${game.discount_percent}%</span>`;
    }

    let ratingHtml = '';
    if (game.review_rating) {
        ratingHtml = `<div class="game-rating flex items-center gap-2 mb-3">
            <span class="text-yellow-400">⭐</span>
            <span class="text-white text-sm">${game.review_rating}</span>
            ${game.review_count ? `<span class="text-gray-400 text-sm">(${game.review_count})</span>` : ''}
        </div>`;
    }

    let descriptionHtml = '';
    if (game.short_description) {
        descriptionHtml = `<p class="game-description text-gray-300 text-sm mb-4 line-clamp-3">${game.short_description}</p>`;
    } else if (game.description) {
        const shortDesc = game.description.length > 150 ? game.description.substring(0, 150) + '...' : game.description;
        descriptionHtml = `<p class="game-description text-gray-300 text-sm mb-4 line-clamp-3">${shortDesc}</p>`;
    }

    let releaseDateHtml = '';
    if (game.release_date) {
        releaseDateHtml = `<span class="text-gray-400 text-xs">${game.release_date}</span>`;
    }

    gameCard.innerHTML = `
        ${imageHtml}
        <div class="p-4">
            <h3 class="game-title text-lg font-bold text-white mb-3 line-clamp-2">${game.title}</h3>
            <div class="game-prices flex items-center gap-2 mb-3">${pricesHtml}</div>
            ${ratingHtml}
            ${descriptionHtml}
            <div class="flex justify-between items-center">
                <a href="${game.url}" target="_blank"
                   class="steam-btn bg-[#1b2838] hover:bg-[#2a475e] text-white px-4 py-2 rounded font-bold transition-colors duration-200 text-sm">
                    Купить в Steam
                </a>
                ${releaseDateHtml}
            </div>
        </div>
    `;

    return gameCard;
}

// Инициализация
document.addEventListener('DOMContentLoaded', function() {
    // Бесконечная прокрутка
    let scrollTimeout;
    window.addEventListener('scroll', function() {
        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(function() {
            const scrollPosition = window.innerHeight + window.scrollY;
            const pageHeight = document.body.offsetHeight;

            if (scrollPosition >= pageHeight - 1000 && !isLoading && hasMore) {
                loadMoreGames();
            }
        }, 100);
    });

    // Поиск при нажатии Enter
    document.getElementById('searchInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            applyFilters();
        }
    });
});