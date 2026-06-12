// Ultra-Responsive Navigation & Interactions
(function() {
    'use strict';
    
    // Mobile Navigation Elements
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const mobileNav = document.getElementById('mobileNav');
    const mobileNavClose = document.getElementById('mobileNavClose');
    const mobileOverlay = document.getElementById('mobileMenuOverlay');
    const mainNav = document.getElementById('mainNav');
    
    // Touch start position for swipe detection
    let touchStartX = 0;
    let touchEndX = 0;
    
    // Open Mobile Menu
    function openMobileMenu() {
        mobileNav.classList.add('active');
        mobileOverlay.classList.add('active');
        document.body.style.overflow = 'hidden';
        document.body.style.position = 'fixed';
        document.body.style.width = '100%';
    }
    
    // Close Mobile Menu
    function closeMobileMenu() {
        mobileNav.classList.remove('active');
        mobileOverlay.classList.remove('active');
        document.body.style.overflow = '';
        document.body.style.position = '';
        document.body.style.width = '';
    }
    
    // Event Listeners for Mobile Menu
    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', openMobileMenu);
    }
    
    if (mobileNavClose) {
        mobileNavClose.addEventListener('click', closeMobileMenu);
    }
    
    if (mobileOverlay) {
        mobileOverlay.addEventListener('click', closeMobileMenu);
    }
    
    // Swipe to close on mobile
    if (mobileNav) {
        mobileNav.addEventListener('touchstart', (e) => {
            touchStartX = e.changedTouches[0].screenX;
        });
        
        mobileNav.addEventListener('touchend', (e) => {
            touchEndX = e.changedTouches[0].screenX;
            if (touchEndX - touchStartX > 50) {
                closeMobileMenu();
            }
        });
    }
    
    // Close menu on escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && mobileNav.classList.contains('active')) {
            closeMobileMenu();
        }
    });
    
    // Back to Top Button
    const backToTop = document.getElementById('backToTop');
    
    window.addEventListener('scroll', () => {
        if (window.scrollY > 300) {
            backToTop.classList.add('visible');
        } else {
            backToTop.classList.remove('visible');
        }
    });
    
    if (backToTop) {
        backToTop.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }
    
    // Responsive Chart Resizing
    let resizeTimer;
    window.addEventListener('resize', () => {
        // Debounce resize events
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
            // Redraw charts if they exist
            if (window.spendingChart) {
                window.spendingChart.resize();
            }
            if (window.pieChart) {
                window.pieChart.resize();
            }
            // Trigger any custom resize events
            window.dispatchEvent(new CustomEvent('responsiveResize'));
        }, 250);
    });
    
    // Active link highlighting
    function setActiveNavLink() {
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.nav-link, .mobile-nav-item a');
        
        navLinks.forEach(link => {
            const linkPath = link.getAttribute('href');
            if (linkPath && currentPath.includes(linkPath) && linkPath !== '/') {
                link.classList.add('active');
            } else if (currentPath === '/' && linkPath === '/dashboard') {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });
    }
    
    setActiveNavLink();
    
    // Dynamic font sizing based on viewport
    function adjustFontSizes() {
        const width = window.innerWidth;
        const root = document.documentElement;
        
        if (width < 576) {
            root.style.fontSize = '14px';
        } else if (width < 768) {
            root.style.fontSize = '15px';
        } else {
            root.style.fontSize = '16px';
        }
    }
    
    adjustFontSizes();
    window.addEventListener('resize', adjustFontSizes);
    
    // Touch-friendly hover effects removal on mobile
    if ('ontouchstart' in window) {
        document.body.classList.add('touch-device');
    }
    
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const target = this.getAttribute('href');
            if (target !== '#') {
                e.preventDefault();
                const element = document.querySelector(target);
                if (element) {
                    element.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });
    
    // Lazy load images
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.add('loaded');
                observer.unobserve(img);
            }
        });
    });
    
    document.querySelectorAll('img[data-src]').forEach(img => {
        imageObserver.observe(img);
    });
    
    // Prevent body scroll when modal is open on mobile
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.addEventListener('show.bs.modal', () => {
            if (window.innerWidth < 768) {
                document.body.style.overflow = 'hidden';
            }
        });
        
        modal.addEventListener('hide.bs.modal', () => {
            document.body.style.overflow = '';
        });
    });
    
    // Swipe detection for cards on mobile
    let startX, startY;
    const cards = document.querySelectorAll('.glass-card');
    
    cards.forEach(card => {
        card.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
        });
        
        card.addEventListener('touchmove', (e) => {
            if (!startX || !startY) return;
            
            const diffX = e.touches[0].clientX - startX;
            const diffY = e.touches[0].clientY - startY;
            
            if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > 10) {
                // Horizontal swipe - prevent default to avoid conflict
                e.preventDefault();
            }
        });
    });
    
    // Add viewport detection classes
    function updateViewportClasses() {
        const width = window.innerWidth;
        document.body.classList.remove('viewport-xs', 'viewport-sm', 'viewport-md', 'viewport-lg', 'viewport-xl');
        
        if (width < 576) {
            document.body.classList.add('viewport-xs');
        } else if (width < 768) {
            document.body.classList.add('viewport-sm');
        } else if (width < 992) {
            document.body.classList.add('viewport-md');
        } else if (width < 1200) {
            document.body.classList.add('viewport-lg');
        } else {
            document.body.classList.add('viewport-xl');
        }
    }
    
    updateViewportClasses();
    window.addEventListener('resize', updateViewportClasses);
    
    // Performance: Debounce scroll events
    let ticking = false;
    window.addEventListener('scroll', () => {
        if (!ticking) {
            requestAnimationFrame(() => {
                // Handle scroll-based animations
                ticking = false;
            });
            ticking = true;
        }
    });
})();

// Toast notification for mobile
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast-notification mobile-toast`;
    toast.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-triangle'}"></i>
        <span>${message}</span>
    `;
    
    // Adjust position for mobile
    const isMobile = window.innerWidth < 768;
    toast.style.cssText = `
        position: fixed;
        bottom: ${isMobile ? '70px' : '24px'};
        right: ${isMobile ? '16px' : '24px'};
        left: ${isMobile ? '16px' : 'auto'};
        background: rgba(30, 30, 46, 0.95);
        backdrop-filter: blur(12px);
        padding: ${isMobile ? '12px 16px' : '12px 20px'};
        border-radius: 10px;
        border-left: 3px solid ${type === 'success' ? '#10b981' : '#ef4444'};
        color: #fff;
        font-size: ${isMobile ? '0.8rem' : '0.85rem'};
        z-index: 10000;
        animation: slideInRight 0.3s ease;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        max-width: ${isMobile ? 'calc(100% - 32px)' : '400px'};
        text-align: center;
    `;
    
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

window.showToast = showToast;