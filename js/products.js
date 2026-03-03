/**
 * Seoul Watch - Product Loader
 * Dynamically loads and displays products based on category
 */

class ProductLoader {
    constructor() {
        this.products = [];
        this.loaded = false;
        this.currentPage = 1;
        this.itemsPerPage = 12;
        this.filteredProducts = [];
    }

    async load() {
        if (this.loaded) return this.products;

        try {
            // Cache busting with timestamp
            const cacheBuster = `?t=${Date.now()}`;
            // Try relative path first, then absolute
            let response = await fetch('data/products.json' + cacheBuster);
            if (!response.ok) {
                response = await fetch('/seoulwatch/data/products.json' + cacheBuster);
            }
            const data = await response.json();
            this.products = data.products;
            this.loaded = true;
            return this.products;
        } catch (error) {
            console.error('Error loading products:', error);
            return [];
        }
    }

    formatPrice(price) {
        return '₩' + price.toLocaleString('ko-KR');
    }

    filterByCategory(category) {
        // Archives 페이지: status가 "archive"인 상품만 표시
        if (category === 'archives') {
            return this.products.filter(product => product.status === 'archive');
        }
        return this.products.filter(product => product.category.includes(category));
    }

    createProductCard(product, delay = 1) {
        const soldBadge = product.status === 'archive'
            ? '<span class="archive-badge sold">SOLD</span>'
            : '';

        return `
            <div class="product-card reveal" data-delay="${delay}">
                <a href="product.html?id=${product.id}" class="product-link">
                    <div class="product-image">
                        ${soldBadge}
                        <img src="${product.image}" alt="${product.name}">
                    </div>
                    <div class="product-info">
                        <span class="product-brand">${product.brand}</span>
                        <h3 class="product-name">${product.name}</h3>
                        <span class="product-price">${this.formatPrice(product.price)}</span>
                    </div>
                </a>
                <button class="quick-view" onclick="event.preventDefault(); quickView('${product.id}')">
                    <svg viewBox="0 0 24 24" fill="none" stroke-width="1.5">
                        <path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                        <path d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                    </svg>
                </button>
            </div>
        `;
    }

    async renderProducts(containerSelector, category, limit = 0, usePagination = false) {
        await this.load();

        const container = document.querySelector(containerSelector);
        if (!container) return;

        this.filteredProducts = category === 'all'
            ? this.products
            : this.filterByCategory(category);

        // Apply limit if specified (no pagination)
        if (limit > 0) {
            const limitedProducts = this.filteredProducts.slice(0, limit);
            this.renderProductCards(container, limitedProducts);
            return;
        }

        // Use pagination
        if (usePagination) {
            this.renderPage(container);
            this.renderPagination();
        } else {
            this.renderProductCards(container, this.filteredProducts);
        }

        // Update product count
        const countEl = document.querySelector('.listing-results strong');
        if (countEl) {
            countEl.textContent = this.filteredProducts.length;
        }
    }

    renderProductCards(container, products) {
        if (products.length === 0) {
            container.innerHTML = '<p class="no-products">현재 등록된 상품이 없습니다.</p>';
            return;
        }

        const html = products.map((product, index) => {
            const delay = (index % 3) + 1;
            return this.createProductCard(product, delay);
        }).join('');

        container.innerHTML = html;

        // Re-initialize reveal animations
        if (typeof initRevealAnimations === 'function') {
            initRevealAnimations();
        }
    }

    renderPage(container) {
        const totalPages = Math.ceil(this.filteredProducts.length / this.itemsPerPage);
        this.currentPage = Math.min(this.currentPage, totalPages) || 1;

        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = startIndex + this.itemsPerPage;
        const pageProducts = this.filteredProducts.slice(startIndex, endIndex);

        this.renderProductCards(container, pageProducts);
    }

    renderPagination() {
        const paginationContainer = document.querySelector('.pagination');
        if (!paginationContainer) return;

        const totalPages = Math.ceil(this.filteredProducts.length / this.itemsPerPage);
        if (totalPages <= 1) {
            paginationContainer.innerHTML = '';
            return;
        }

        let html = '';

        // Previous button
        html += `<button class="pagination-btn pagination-prev ${this.currentPage === 1 ? 'disabled' : ''}"
                    ${this.currentPage === 1 ? 'disabled' : ''} data-page="${this.currentPage - 1}">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M15 18l-6-6 6-6"/>
                    </svg>
                </button>`;

        // Page numbers
        const maxVisiblePages = 5;
        let startPage = Math.max(1, this.currentPage - Math.floor(maxVisiblePages / 2));
        let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);

        if (endPage - startPage + 1 < maxVisiblePages) {
            startPage = Math.max(1, endPage - maxVisiblePages + 1);
        }

        if (startPage > 1) {
            html += `<button class="pagination-btn" data-page="1">1</button>`;
            if (startPage > 2) {
                html += `<span class="pagination-ellipsis">...</span>`;
            }
        }

        for (let i = startPage; i <= endPage; i++) {
            html += `<button class="pagination-btn ${i === this.currentPage ? 'active' : ''}" data-page="${i}">${i}</button>`;
        }

        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                html += `<span class="pagination-ellipsis">...</span>`;
            }
            html += `<button class="pagination-btn" data-page="${totalPages}">${totalPages}</button>`;
        }

        // Next button
        html += `<button class="pagination-btn pagination-next ${this.currentPage === totalPages ? 'disabled' : ''}"
                    ${this.currentPage === totalPages ? 'disabled' : ''} data-page="${this.currentPage + 1}">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M9 18l6-6-6-6"/>
                    </svg>
                </button>`;

        paginationContainer.innerHTML = html;

        // Add click handlers
        paginationContainer.querySelectorAll('.pagination-btn:not(.disabled)').forEach(btn => {
            btn.addEventListener('click', () => {
                this.goToPage(parseInt(btn.dataset.page));
            });
        });
    }

    goToPage(page) {
        const totalPages = Math.ceil(this.filteredProducts.length / this.itemsPerPage);
        if (page < 1 || page > totalPages) return;

        this.currentPage = page;
        const container = document.querySelector('.product-grid');
        if (container) {
            this.renderPage(container);
            this.renderPagination();

            // Scroll to top of product grid
            container.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }
}

// Quick view function
function quickView(productId) {
    window.location.href = `product.html?id=${productId}`;
}

// Global instance
const productLoader = new ProductLoader();

// Auto-initialize based on page data attribute
document.addEventListener('DOMContentLoaded', () => {
    // Handle product-grid with pagination
    const productGrid = document.querySelector('.product-grid[data-category]');
    if (productGrid) {
        const category = productGrid.dataset.category;
        const usePagination = productGrid.dataset.pagination === 'true';
        productLoader.renderProducts('.product-grid', category, 0, usePagination);
    }

    // Handle bento-grid (homepage) - limit to 12 newest products
    const bentoGrid = document.querySelector('.bento-grid[data-category]');
    if (bentoGrid) {
        const category = bentoGrid.dataset.category;
        const limit = parseInt(bentoGrid.dataset.limit) || 12;
        productLoader.renderProducts('.bento-grid', category, limit);
    }
});
