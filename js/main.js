/* ==========================================================================
   SEOUL WATCH - Modern 2025 JavaScript
   ========================================================================== */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all modules
    initCustomCursor();
    initHeader();
    initHeroSlider();
    initMobileMenu();
    initRevealAnimations();
    initMagneticButtons();
    initParallax();
    initSmoothScroll();
    initSearch();
});

/* --------------------------------------------------------------------------
   1. Custom Cursor
   -------------------------------------------------------------------------- */
function initCustomCursor() {
    const cursor = document.getElementById('cursor');
    const cursorDot = document.getElementById('cursorDot');

    if (!cursor || !cursorDot || window.innerWidth <= 1024) return;

    let mouseX = 0;
    let mouseY = 0;
    let cursorX = 0;
    let cursorY = 0;
    let dotX = 0;
    let dotY = 0;

    document.addEventListener('mousemove', (e) => {
        mouseX = e.clientX;
        mouseY = e.clientY;
    });

    // Smooth cursor animation
    function animateCursor() {
        // Cursor ring - slower follow
        const diffX = mouseX - cursorX;
        const diffY = mouseY - cursorY;
        cursorX += diffX * 0.15;
        cursorY += diffY * 0.15;
        cursor.style.left = cursorX + 'px';
        cursor.style.top = cursorY + 'px';

        // Cursor dot - faster follow
        const dotDiffX = mouseX - dotX;
        const dotDiffY = mouseY - dotY;
        dotX += dotDiffX * 0.35;
        dotY += dotDiffY * 0.35;
        cursorDot.style.left = dotX + 'px';
        cursorDot.style.top = dotY + 'px';

        requestAnimationFrame(animateCursor);
    }
    animateCursor();

    // Hover effect on interactive elements
    const hoverElements = document.querySelectorAll('a, button, .product-card, .brand-image');
    hoverElements.forEach(el => {
        el.addEventListener('mouseenter', () => cursor.classList.add('hover'));
        el.addEventListener('mouseleave', () => cursor.classList.remove('hover'));
    });

    // Hide cursor when leaving window
    document.addEventListener('mouseleave', () => {
        cursor.style.opacity = '0';
        cursorDot.style.opacity = '0';
    });

    document.addEventListener('mouseenter', () => {
        cursor.style.opacity = '1';
        cursorDot.style.opacity = '1';
    });
}

/* --------------------------------------------------------------------------
   2. Header Scroll Effect
   -------------------------------------------------------------------------- */
function initHeader() {
    const header = document.getElementById('header');
    if (!header) return;

    let lastScroll = 0;
    let ticking = false;

    function updateHeader() {
        const currentScroll = window.pageYOffset;

        if (currentScroll > 100) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }

        lastScroll = currentScroll;
        ticking = false;
    }

    window.addEventListener('scroll', () => {
        if (!ticking) {
            requestAnimationFrame(updateHeader);
            ticking = true;
        }
    }, { passive: true });

    updateHeader();
}

/* --------------------------------------------------------------------------
   3. Hero Slider with Smooth Transitions
   -------------------------------------------------------------------------- */
function initHeroSlider() {
    const slides = document.querySelectorAll('.hero-slide');
    let currentSlide = 0;
    const slideInterval = 6000;

    if (slides.length === 0) return;

    function nextSlide() {
        slides[currentSlide].classList.remove('active');
        currentSlide = (currentSlide + 1) % slides.length;
        slides[currentSlide].classList.add('active');
    }

    setInterval(nextSlide, slideInterval);
}

/* --------------------------------------------------------------------------
   4. Mobile Menu
   -------------------------------------------------------------------------- */
function initMobileMenu() {
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const navLeft = document.getElementById('navLeft');
    const navRight = document.getElementById('navRight');
    const dropdownItems = document.querySelectorAll('.nav-item.has-dropdown');
    const body = document.body;

    if (!mobileMenuBtn) return;

    mobileMenuBtn.addEventListener('click', function() {
        this.classList.toggle('active');
        if (navLeft) navLeft.classList.toggle('active');
        if (navRight) navRight.classList.toggle('active');
        const isActive = this.classList.contains('active');
        body.style.overflow = isActive ? 'hidden' : '';
    });

    dropdownItems.forEach(item => {
        const link = item.querySelector('.nav-link');
        link.addEventListener('click', function(e) {
            if (window.innerWidth <= 768) {
                e.preventDefault();
                item.classList.toggle('active');
            }
        });
    });

    window.addEventListener('resize', function() {
        if (window.innerWidth > 768) {
            mobileMenuBtn.classList.remove('active');
            if (navLeft) navLeft.classList.remove('active');
            if (navRight) navRight.classList.remove('active');
            body.style.overflow = '';
            dropdownItems.forEach(item => item.classList.remove('active'));
        }
    });
}

/* --------------------------------------------------------------------------
   5. Reveal Animations on Scroll
   -------------------------------------------------------------------------- */
function initRevealAnimations() {
    const revealElements = document.querySelectorAll('.reveal, .reveal-left, .reveal-right');

    if (revealElements.length === 0) return;

    const observerOptions = {
        root: null,
        rootMargin: '-50px',
        threshold: 0.1
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('active');
            }
        });
    }, observerOptions);

    revealElements.forEach(element => {
        observer.observe(element);
    });

    // Brand item text animations
    const brandItems = document.querySelectorAll('.brand-item');
    if (brandItems.length > 0) {
        const brandObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('in-view');
                }
            });
        }, {
            root: null,
            rootMargin: '-100px',
            threshold: 0.2
        });

        brandItems.forEach(item => {
            brandObserver.observe(item);
        });
    }
}

/* --------------------------------------------------------------------------
   6. Magnetic Button Effect
   -------------------------------------------------------------------------- */
function initMagneticButtons() {
    const magneticBtns = document.querySelectorAll('.magnetic-btn');

    if (magneticBtns.length === 0 || window.innerWidth <= 1024) return;

    magneticBtns.forEach(btn => {
        btn.addEventListener('mousemove', function(e) {
            const rect = this.getBoundingClientRect();
            const x = e.clientX - rect.left - rect.width / 2;
            const y = e.clientY - rect.top - rect.height / 2;

            this.style.transform = `translate(${x * 0.3}px, ${y * 0.3}px)`;
        });

        btn.addEventListener('mouseleave', function() {
            this.style.transform = 'translate(0, 0)';
        });
    });
}

/* --------------------------------------------------------------------------
   7. Parallax Effect
   -------------------------------------------------------------------------- */
function initParallax() {
    const parallaxBg = document.querySelector('.about-bg');

    if (!parallaxBg || window.innerWidth <= 768) return;

    let ticking = false;

    function updateParallax() {
        const scrolled = window.pageYOffset;
        const section = parallaxBg.closest('.about-section');

        if (section) {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.offsetHeight;

            if (scrolled + window.innerHeight > sectionTop && scrolled < sectionTop + sectionHeight) {
                const yPos = (scrolled - sectionTop) * 0.3;
                parallaxBg.style.transform = `translateY(${yPos}px)`;
            }
        }

        ticking = false;
    }

    window.addEventListener('scroll', () => {
        if (!ticking) {
            requestAnimationFrame(updateParallax);
            ticking = true;
        }
    }, { passive: true });
}

/* --------------------------------------------------------------------------
   8. Smooth Scroll
   -------------------------------------------------------------------------- */
function initSmoothScroll() {
    const links = document.querySelectorAll('a[href^="#"]');

    links.forEach(link => {
        link.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href === '#') return;

            const target = document.querySelector(href);
            if (target) {
                e.preventDefault();
                const headerHeight = document.getElementById('header').offsetHeight;
                const targetPosition = target.getBoundingClientRect().top + window.pageYOffset - headerHeight;

                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });

                // Close mobile menu if open
                const nav = document.getElementById('nav');
                const mobileMenuBtn = document.getElementById('mobileMenuBtn');
                if (nav && nav.classList.contains('active')) {
                    mobileMenuBtn.classList.remove('active');
                    nav.classList.remove('active');
                    document.body.style.overflow = '';
                }
            }
        });
    });
}

/* --------------------------------------------------------------------------
   9. Counter Animation (for About Section)
   -------------------------------------------------------------------------- */
function initCounterAnimation() {
    const counters = document.querySelectorAll('.about-feature-number');

    if (counters.length === 0) return;

    const observerOptions = {
        threshold: 0.5
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const counter = entry.target;
                const target = parseInt(counter.textContent);
                const suffix = counter.textContent.replace(/[0-9]/g, '');

                let current = 0;
                const increment = target / 50;
                const timer = setInterval(() => {
                    current += increment;
                    if (current >= target) {
                        counter.textContent = target + suffix;
                        clearInterval(timer);
                    } else {
                        counter.textContent = Math.floor(current) + suffix;
                    }
                }, 30);

                observer.unobserve(counter);
            }
        });
    }, observerOptions);

    counters.forEach(counter => observer.observe(counter));
}

/* --------------------------------------------------------------------------
   10. Image Lazy Loading
   -------------------------------------------------------------------------- */
function initLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');

    if (images.length === 0) return;

    const imageObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                img.classList.add('loaded');
                imageObserver.unobserve(img);
            }
        });
    }, {
        rootMargin: '50px'
    });

    images.forEach(img => imageObserver.observe(img));
}

/* --------------------------------------------------------------------------
   11. Tilt Effect for Product Cards
   -------------------------------------------------------------------------- */
function initTiltEffect() {
    const cards = document.querySelectorAll('.product-card');

    if (cards.length === 0 || window.innerWidth <= 1024) return;

    cards.forEach(card => {
        card.addEventListener('mousemove', function(e) {
            const rect = this.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            const centerX = rect.width / 2;
            const centerY = rect.height / 2;

            const rotateX = (y - centerY) / 20;
            const rotateY = (centerX - x) / 20;

            this.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-8px)`;
        });

        card.addEventListener('mouseleave', function() {
            this.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) translateY(0)';
        });
    });
}

/* --------------------------------------------------------------------------
   Utility Functions
   -------------------------------------------------------------------------- */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Initialize additional features
document.addEventListener('DOMContentLoaded', () => {
    initCounterAnimation();
    initLazyLoading();
    initTiltEffect();
});

/* --------------------------------------------------------------------------
   12. Search Functionality
   -------------------------------------------------------------------------- */
function initSearch() {
    const searchBtn = document.querySelector('a[aria-label="Search"]');
    const searchModal = document.getElementById('searchModal');

    if (!searchBtn || !searchModal) return;

    const searchInput = document.getElementById('searchInput');
    const searchResults = document.getElementById('searchResults');
    const searchClose = document.getElementById('searchClose');

    let allProducts = [];
    let searchTimeout = null;

    // Load products data
    async function loadProducts() {
        try {
            // Cache busting with timestamp
            const cacheBuster = `?t=${Date.now()}`;
            let response = await fetch('data/products.json' + cacheBuster);
            if (!response.ok) {
                response = await fetch('/data/products.json' + cacheBuster);
            }
            const data = await response.json();
            allProducts = data.products || [];
        } catch (error) {
            console.error('Error loading products:', error);
        }
    }

    // Open search modal
    searchBtn.addEventListener('click', function(e) {
        e.preventDefault();
        searchModal.classList.add('active');
        document.body.style.overflow = 'hidden';
        setTimeout(() => searchInput.focus(), 100);

        if (allProducts.length === 0) {
            loadProducts();
        }

        renderInitialState();
    });

    // Close search modal
    function closeSearch() {
        searchModal.classList.remove('active');
        document.body.style.overflow = '';
        searchInput.value = '';
    }

    searchClose.addEventListener('click', closeSearch);

    searchModal.addEventListener('click', function(e) {
        if (e.target === searchModal) {
            closeSearch();
        }
    });

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && searchModal.classList.contains('active')) {
            closeSearch();
        }
    });

    // Search input handler
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value.trim();

        if (query.length === 0) {
            renderInitialState();
            return;
        }

        searchTimeout = setTimeout(() => {
            performSearch(query);
        }, 300);
    });

    // Perform search
    function performSearch(query) {
        const queryLower = query.toLowerCase();

        const results = allProducts.filter(product => {
            const name = (product.name || '').toLowerCase();
            const nameEn = (product.nameEn || '').toLowerCase();
            const brand = (product.brand || '').toLowerCase();
            const sku = (product.sku || '').toLowerCase();

            return name.includes(queryLower) ||
                   nameEn.includes(queryLower) ||
                   brand.includes(queryLower) ||
                   sku.includes(queryLower);
        });

        renderResults(results, query);
    }

    // Format price with currency conversion
    function formatPrice(price) {
        if (window.CurrencyConverter) {
            return window.CurrencyConverter.format(price);
        }
        return '₩' + price.toLocaleString('ko-KR');
    }

    // Render initial state with popular searches
    function renderInitialState() {
        searchResults.innerHTML = `
            <div class="search-empty">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <circle cx="11" cy="11" r="8"/>
                    <path d="m21 21-4.35-4.35"/>
                </svg>
                <h3>시계를 검색해보세요</h3>
                <p>브랜드, 모델명, 레퍼런스로 검색할 수 있습니다</p>
            </div>
            <div class="search-popular">
                <h4>인기 검색어</h4>
                <div class="search-popular-tags">
                    <span class="search-popular-tag" data-query="Rolex">Rolex</span>
                    <span class="search-popular-tag" data-query="Cartier">Cartier</span>
                    <span class="search-popular-tag" data-query="Patek Philippe">Patek Philippe</span>
                    <span class="search-popular-tag" data-query="Audemars Piguet">Audemars Piguet</span>
                    <span class="search-popular-tag" data-query="Omega">Omega</span>
                </div>
            </div>
        `;

        // Add click handlers for popular tags
        document.querySelectorAll('.search-popular-tag').forEach(tag => {
            tag.addEventListener('click', function() {
                const query = this.dataset.query;
                searchInput.value = query;
                performSearch(query);
            });
        });
    }

    // Render search results
    function renderResults(results, query) {
        if (results.length === 0) {
            searchResults.innerHTML = `
                <div class="search-empty">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <circle cx="11" cy="11" r="8"/>
                        <path d="m21 21-4.35-4.35"/>
                    </svg>
                    <h3>검색 결과가 없습니다</h3>
                    <p>"${query}"에 대한 결과를 찾을 수 없습니다</p>
                </div>
            `;
            return;
        }

        searchResults.innerHTML = `
            <p class="search-results-info"><strong>${results.length}</strong>개의 상품을 찾았습니다</p>
            <div class="search-results-grid">
                ${results.map(product => `
                    <a href="product.html?id=${product.id}" class="search-result-item">
                        <div class="search-result-image">
                            <img src="${product.image}" alt="${product.name}">
                        </div>
                        <div class="search-result-info">
                            <p class="search-result-brand">${product.brand}</p>
                            <h4 class="search-result-name">${product.name}</h4>
                            <p class="search-result-price">${formatPrice(product.price)}</p>
                        </div>
                    </a>
                `).join('')}
            </div>
        `;
    }
}

/* --------------------------------------------------------------------------
   13. Language / Translation (Google Translate)
   -------------------------------------------------------------------------- */
function changeLanguage(lang) {
    // Update active state in dropdown
    document.querySelectorAll('.lang-option').forEach(opt => {
        opt.classList.remove('active');
        if (opt.textContent.includes(lang === 'ko' ? '한국어' : lang === 'en' ? 'English' : '日本語')) {
            opt.classList.add('active');
        }
    });

    // Set cookie for Google Translate
    if (lang === 'ko') {
        // Remove translation, go back to original
        document.cookie = 'googtrans=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
        document.cookie = 'googtrans=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=.' + window.location.hostname;
        window.location.reload();
    } else {
        const googtrans = '/ko/' + lang;
        document.cookie = 'googtrans=' + googtrans + '; path=/;';
        document.cookie = 'googtrans=' + googtrans + '; path=/; domain=.' + window.location.hostname;
        window.location.reload();
    }
}

// Initialize Google Translate
function initGoogleTranslate() {
    // Check current language from cookie
    const googtrans = document.cookie.split('; ').find(row => row.startsWith('googtrans='));
    if (googtrans) {
        const lang = googtrans.split('=')[1].split('/')[2];
        document.querySelectorAll('.lang-option').forEach(opt => {
            opt.classList.remove('active');
            if ((lang === 'en' && opt.textContent.includes('English')) ||
                (lang === 'ja' && opt.textContent.includes('日本語'))) {
                opt.classList.add('active');
            }
        });
    }
}

// Load Google Translate script
(function() {
    const script = document.createElement('script');
    script.src = '//translate.google.com/translate_a/element.js?cb=googleTranslateElementInit';
    script.async = true;
    document.head.appendChild(script);
})();

function googleTranslateElementInit() {
    new google.translate.TranslateElement({
        pageLanguage: 'ko',
        includedLanguages: 'en,ja,ko',
        autoDisplay: false
    }, 'google_translate_element');

    // Hide the default Google Translate bar
    setTimeout(() => {
        const translateBar = document.querySelector('.goog-te-banner-frame');
        if (translateBar) {
            translateBar.style.display = 'none';
        }
        document.body.style.top = '0px';
        initGoogleTranslate();
    }, 1000);
}

// Make changeLanguage globally accessible
window.changeLanguage = changeLanguage;

/* --------------------------------------------------------------------------
   14. Currency Conversion System
   -------------------------------------------------------------------------- */
const CurrencyConverter = {
    rates: {
        KRW: 1,
        USD: 0.00072,  // 1 KRW = 0.00072 USD (약 1,389원/달러)
        JPY: 0.11      // 1 KRW = 0.11 JPY (약 9.09원/엔)
    },
    symbols: {
        KRW: '₩',
        USD: '$',
        JPY: '¥'
    },
    currentCurrency: 'KRW',
    lastFetch: null,

    // 현재 언어에 따른 화폐 결정
    getCurrencyFromLanguage() {
        const googtrans = document.cookie.split('; ').find(row => row.startsWith('googtrans='));
        if (googtrans) {
            const lang = googtrans.split('=')[1].split('/')[2];
            if (lang === 'en') return 'USD';
            if (lang === 'ja') return 'JPY';
        }
        return 'KRW';
    },

    // 실시간 환율 가져오기 (무료 API 사용)
    async fetchRates() {
        // 1시간마다 환율 업데이트
        const now = Date.now();
        const cached = localStorage.getItem('exchangeRates');
        const cachedTime = localStorage.getItem('exchangeRatesTime');

        if (cached && cachedTime && (now - parseInt(cachedTime)) < 3600000) {
            const rates = JSON.parse(cached);
            this.rates = rates;
            return;
        }

        try {
            // 무료 환율 API 사용
            const response = await fetch('https://api.exchangerate-api.com/v4/latest/KRW');
            if (response.ok) {
                const data = await response.json();
                this.rates = {
                    KRW: 1,
                    USD: data.rates.USD,
                    JPY: data.rates.JPY
                };
                localStorage.setItem('exchangeRates', JSON.stringify(this.rates));
                localStorage.setItem('exchangeRatesTime', now.toString());
                console.log('Exchange rates updated:', this.rates);
            }
        } catch (error) {
            console.log('Using fallback exchange rates');
            // 폴백: 하드코딩된 환율 사용
        }
    },

    // 가격 변환
    convert(priceKRW, targetCurrency = null) {
        const currency = targetCurrency || this.getCurrencyFromLanguage();
        const rate = this.rates[currency] || 1;
        return priceKRW * rate;
    },

    // 가격 포맷팅
    format(priceKRW, targetCurrency = null) {
        const currency = targetCurrency || this.getCurrencyFromLanguage();
        const converted = this.convert(priceKRW, currency);
        const symbol = this.symbols[currency];

        if (currency === 'KRW') {
            return symbol + converted.toLocaleString('ko-KR');
        } else if (currency === 'USD') {
            return symbol + converted.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
        } else if (currency === 'JPY') {
            return symbol + Math.round(converted).toLocaleString('ja-JP');
        }
        return symbol + converted.toLocaleString();
    },

    // 초기화
    async init() {
        this.currentCurrency = this.getCurrencyFromLanguage();
        await this.fetchRates();
    }
};

// Initialize currency converter
CurrencyConverter.init();

// Make globally accessible
window.CurrencyConverter = CurrencyConverter;
