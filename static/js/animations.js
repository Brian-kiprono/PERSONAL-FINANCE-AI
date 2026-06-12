// Modern Animations & Effects
(function() {
    'use strict';
    
    // Initialize particles
    function createParticles() {
        const particlesDiv = document.createElement('div');
        particlesDiv.className = 'particles';
        document.body.appendChild(particlesDiv);
        
        for (let i = 0; i < 50; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';
            const size = Math.random() * 3 + 1;
            particle.style.width = `${size}px`;
            particle.style.height = `${size}px`;
            particle.style.left = `${Math.random() * 100}%`;
            particle.style.top = `${Math.random() * 100}%`;
            particle.style.animationDelay = `${Math.random() * 20}s`;
            particle.style.animationDuration = `${15 + Math.random() * 15}s`;
            particlesDiv.appendChild(particle);
        }
    }
    
    // Smooth scroll reveal
    function initScrollReveal() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                    observer.unobserve(entry.target);
                }
            });
        }, observerOptions);
        
        document.querySelectorAll('.glass-card').forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(30px)';
            card.style.transition = `all 0.6s cubic-bezier(0.4, 0, 0.2, 1) ${index * 0.05}s`;
            observer.observe(card);
        });
    }
    
    // Navbar scroll effect
    function initNavbarScroll() {
        const navbar = document.querySelector('.glass-nav');
        if (navbar) {
            window.addEventListener('scroll', () => {
                if (window.scrollY > 50) {
                    navbar.classList.add('scrolled');
                } else {
                    navbar.classList.remove('scrolled');
                }
            });
        }
    }
    
    // Number counter animation
    function animateNumbers() {
        const counters = document.querySelectorAll('.stat-card h2, .analysis-card h4');
        
        counters.forEach(counter => {
            const target = parseFloat(counter.innerText.replace(/[^0-9.-]+/g, ''));
            if (!isNaN(target) && target > 0) {
                let current = 0;
                const duration = 1500;
                const step = target / (duration / 16);
                
                const updateCounter = () => {
                    current += step;
                    if (current >= target) {
                        counter.innerText = counter.innerText.replace(/[0-9.-]+/, target.toFixed(2));
                        return;
                    }
                    counter.innerText = counter.innerText.replace(/[0-9.-]+/, current.toFixed(2));
                    requestAnimationFrame(updateCounter);
                };
                
                updateCounter();
            }
        });
    }
    
    // Hover parallax effect
    function initParallaxCards() {
        const cards = document.querySelectorAll('.glass-card');
        
        cards.forEach(card => {
            card.addEventListener('mousemove', (e) => {
                const rect = card.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                const centerX = rect.width / 2;
                const centerY = rect.height / 2;
                const rotateX = (y - centerY) / 30;
                const rotateY = (centerX - x) / 30;
                
                card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-4px)`;
            });
            
            card.addEventListener('mouseleave', () => {
                card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0)';
            });
        });
    }
    
    // Glow effect on focus
    function initGlowEffects() {
        const inputs = document.querySelectorAll('.glass-input, select.form-control');
        
        inputs.forEach(input => {
            input.addEventListener('focus', () => {
                input.style.boxShadow = '0 0 0 3px rgba(99, 102, 241, 0.2)';
            });
            
            input.addEventListener('blur', () => {
                input.style.boxShadow = 'none';
            });
        });
    }
    
    // Smooth button ripple
    function initButtonRipple() {
        const buttons = document.querySelectorAll('.btn');
        
        buttons.forEach(button => {
            button.addEventListener('click', function(e) {
                const rect = this.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                
                const ripple = document.createElement('span');
                ripple.style.position = 'absolute';
                ripple.style.left = `${x}px`;
                ripple.style.top = `${y}px`;
                ripple.style.width = '0';
                ripple.style.height = '0';
                ripple.style.borderRadius = '50%';
                ripple.style.backgroundColor = 'rgba(255, 255, 255, 0.4)';
                ripple.style.transform = 'translate(-50%, -50%)';
                ripple.style.transition = 'all 0.4s ease-out';
                ripple.style.pointerEvents = 'none';
                
                this.style.position = 'relative';
                this.style.overflow = 'hidden';
                this.appendChild(ripple);
                
                setTimeout(() => {
                    ripple.style.width = '200px';
                    ripple.style.height = '200px';
                    ripple.style.opacity = '0';
                }, 10);
                
                setTimeout(() => ripple.remove(), 400);
            });
        });
    }
    
    // Modern toast with animations
    window.showToast = function(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = 'toast-notification';
        toast.innerHTML = `
            <div style="display: flex; align-items: center; gap: 12px;">
                <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}" 
                   style="color: ${type === 'success' ? '#10b981' : '#ef4444'}; font-size: 1.25rem;"></i>
                <span style="flex: 1;">${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" 
                        style="background: none; border: none; color: #94a3b8; cursor: pointer;">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        toast.style.cssText = `
            position: fixed;
            bottom: 24px;
            right: 24px;
            background: rgba(15, 23, 42, 0.95);
            backdrop-filter: blur(12px);
            padding: 14px 20px;
            border-radius: 16px;
            border-left: 3px solid ${type === 'success' ? '#10b981' : '#ef4444'};
            color: #f1f5f9;
            font-size: 0.875rem;
            z-index: 10000;
            animation: slideInRight 0.3s ease-out;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.2);
            max-width: 400px;
            min-width: 280px;
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'slideOutRight 0.3s ease-in';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    };
    
    // Add slideOut animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideOutRight {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
    
    // Initialize all animations when DOM is ready
    document.addEventListener('DOMContentLoaded', () => {
        createParticles();
        initScrollReveal();
        initNavbarScroll();
        initParallaxCards();
        initGlowEffects();
        initButtonRipple();
        
        setTimeout(animateNumbers, 500);
    });
    
    // Re-initialize animations after AJAX content loads
    window.addEventListener('load', () => {
        initScrollReveal();
    });
})();