document.addEventListener('DOMContentLoaded', () => {
    // ==================== THEME ====================
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = document.getElementById('theme-icon');
    const html = document.documentElement;
    
    const setTheme = (theme) => {
        html.setAttribute('data-bs-theme', theme);
        html.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        if (themeIcon) {
            themeIcon.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-fill';
        }
    };

    setTheme(localStorage.getItem('theme') || 'light');

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            setTheme(html.getAttribute('data-theme') === 'light' ? 'dark' : 'light');
        });
    }

    // ==================== SIDEBAR PIN/HIDE ====================
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarCollapse');
    const pinBtn = document.getElementById('sidebarPin');
    const pinIcon = document.getElementById('pinIcon');
    const body = document.body;

    // States: 'pinned' (always visible), 'hidden' (auto-hide, peek on hover)
    let sidebarState = localStorage.getItem('sidebarPinState') || 'pinned';

    function applySidebarState() {
        if (!sidebar) return;
        sidebar.classList.remove('collapsed', 'hidden');
        body.classList.remove('sidebar-collapsed', 'sidebar-hidden');

        if (sidebarState === 'hidden') {
            sidebar.classList.add('hidden');
            body.classList.add('sidebar-hidden');
            if (pinIcon) pinIcon.className = 'bi bi-pin-angle';
            if (pinBtn) pinBtn.classList.remove('pinned');
        } else {
            if (pinIcon) pinIcon.className = 'bi bi-pin-fill';
            if (pinBtn) pinBtn.classList.add('pinned');
        }
    }

    applySidebarState();

    if (pinBtn) {
        pinBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            sidebarState = sidebarState === 'pinned' ? 'hidden' : 'pinned';
            localStorage.setItem('sidebarPinState', sidebarState);
            applySidebarState();
        });
    }

    // Sidebar toggle button (hamburger) toggles collapsed on desktop, show on mobile
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', () => {
            if (window.innerWidth <= 768) {
                sidebar.classList.toggle('show');
            } else {
                if (sidebarState === 'hidden') {
                    // Un-hide
                    sidebarState = 'pinned';
                    localStorage.setItem('sidebarPinState', 'pinned');
                    applySidebarState();
                } else {
                    sidebar.classList.toggle('collapsed');
                    body.classList.toggle('sidebar-collapsed');
                    localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
                }
            }
        });

        // Restore collapsed state
        if (localStorage.getItem('sidebarCollapsed') === 'true' && sidebarState === 'pinned') {
            sidebar.classList.add('collapsed');
            body.classList.add('sidebar-collapsed');
        }
    }

    // ==================== FAVORITES ====================
    const FAVORITES_KEY = 'sidebarFavorites';
    const favoritesSection = document.getElementById('favoritesSection');
    const favoritesList = document.getElementById('favoritesList');
    const manageFavBtn = document.getElementById('manageFavBtn');
    let editingFavs = false;

    function getFavorites() {
        try {
            return JSON.parse(localStorage.getItem(FAVORITES_KEY)) || [];
        } catch { return []; }
    }

    function saveFavorites(favs) {
        localStorage.setItem(FAVORITES_KEY, JSON.stringify(favs));
    }

    function renderFavorites() {
        const favs = getFavorites();
        if (!favoritesList || !favoritesSection) return;

        if (favs.length === 0) {
            favoritesSection.style.display = 'none';
            return;
        }

        favoritesSection.style.display = '';
        favoritesList.innerHTML = '';

        favs.forEach((fav, idx) => {
            const li = document.createElement('li');
            li.className = 'nav-item';
            
            if (editingFavs) {
                li.innerHTML = `
                    <div class="nav-link text-white d-flex align-items-center" style="cursor:default;">
                        <i class="bi ${fav.icon} me-2"></i>
                        <span class="flex-grow-1">${fav.label}</span>
                        <button class="btn btn-sm text-danger border-0 p-0 fav-remove" data-idx="${idx}" title="Rimuovi">
                            <i class="bi bi-x-circle"></i>
                        </button>
                        ${idx > 0 ? `<button class="btn btn-sm text-white border-0 p-0 ms-1 fav-up" data-idx="${idx}" title="Su">
                            <i class="bi bi-chevron-up" style="font-size:0.7rem;"></i>
                        </button>` : ''}
                        ${idx < favs.length - 1 ? `<button class="btn btn-sm text-white border-0 p-0 ms-1 fav-down" data-idx="${idx}" title="Giu">
                            <i class="bi bi-chevron-down" style="font-size:0.7rem;"></i>
                        </button>` : ''}
                    </div>
                `;
            } else {
                li.innerHTML = `
                    <a class="nav-link text-white" href="${fav.href}">
                        <i class="bi ${fav.icon} me-2"></i> <span>${fav.label}</span>
                    </a>
                `;
            }
            favoritesList.appendChild(li);
        });

        // Bind edit mode buttons
        if (editingFavs) {
            favoritesList.querySelectorAll('.fav-remove').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const favs = getFavorites();
                    favs.splice(parseInt(btn.dataset.idx), 1);
                    saveFavorites(favs);
                    updateStarStates();
                    renderFavorites();
                });
            });
            favoritesList.querySelectorAll('.fav-up').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const favs = getFavorites();
                    const i = parseInt(btn.dataset.idx);
                    [favs[i - 1], favs[i]] = [favs[i], favs[i - 1]];
                    saveFavorites(favs);
                    renderFavorites();
                });
            });
            favoritesList.querySelectorAll('.fav-down').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const favs = getFavorites();
                    const i = parseInt(btn.dataset.idx);
                    [favs[i], favs[i + 1]] = [favs[i + 1], favs[i]];
                    saveFavorites(favs);
                    renderFavorites();
                });
            });
        }
    }

    function updateStarStates() {
        const favs = getFavorites();
        const favIds = favs.map(f => f.id);
        document.querySelectorAll('.nav-item[data-menu-id]').forEach(item => {
            const star = item.querySelector('.fav-star');
            if (!star) return;
            if (favIds.includes(item.dataset.menuId)) {
                star.classList.add('active');
            } else {
                star.classList.remove('active');
            }
        });
    }

    // Star click handler
    document.querySelectorAll('.fav-star').forEach(star => {
        star.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            const item = star.closest('.nav-item');
            const menuId = item.dataset.menuId;
            const menuLabel = item.dataset.menuLabel;
            const menuIcon = item.dataset.menuIcon;
            const href = item.querySelector('a').getAttribute('href');
            
            let favs = getFavorites();
            const existingIdx = favs.findIndex(f => f.id === menuId);

            if (existingIdx >= 0) {
                favs.splice(existingIdx, 1);
            } else {
                favs.push({ id: menuId, label: menuLabel, icon: menuIcon, href: href });
            }

            saveFavorites(favs);
            updateStarStates();
            renderFavorites();
        });
    });

    // Manage favorites button
    if (manageFavBtn) {
        manageFavBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            editingFavs = !editingFavs;
            manageFavBtn.querySelector('i').className = editingFavs ? 'bi bi-check-circle-fill text-success' : 'bi bi-gear-fill';
            manageFavBtn.title = editingFavs ? 'Fine modifica' : 'Gestisci preferiti';
            renderFavorites();
        });
    }

    // Init
    updateStarStates();
    renderFavorites();

    // ==================== FLASH MESSAGES ====================
    document.querySelectorAll('.alert-dismissible').forEach(alert => {
        setTimeout(() => {
            try { new bootstrap.Alert(alert).close(); } catch {}
        }, 5000);
    });

    // ==================== CONFIRM DELETE ====================
    document.body.addEventListener('click', (e) => {
        if (e.target.closest('.btn-delete')) {
            const btn = e.target.closest('.btn-delete');
            if (!confirm(btn.dataset.confirmMessage || 'Are you sure?')) {
                e.preventDefault();
            }
        }
    });
});
