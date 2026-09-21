/**
 * Hermes Brain — GitHub Pages JavaScript
 * Lightweight, vanilla JS for interactions
 */

(function() {
    'use strict';

    // ========================================
    // Tab functionality for Quick Start section
    // ========================================
    function initTabs() {
        const tabButtons = document.querySelectorAll('.tab-btn');
        const tabPanels = document.querySelectorAll('.tab-panel');

        if (!tabButtons.length || !tabPanels.length) return;

        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const targetTab = button.dataset.tab;

                // Update button states
                tabButtons.forEach(btn => {
                    btn.classList.remove('active');
                    btn.setAttribute('aria-selected', 'false');
                });
                button.classList.add('active');
                button.setAttribute('aria-selected', 'true');

                // Update panel visibility
                tabPanels.forEach(panel => {
                    if (panel.dataset.tab === targetTab) {
                        panel.classList.add('active');
                    } else {
                        panel.classList.remove('active');
                    }
                });
            });

            // Keyboard navigation
            button.addEventListener('keydown', (e) => {
                let targetIndex;
                const currentIndex = Array.from(tabButtons).indexOf(button);

                switch (e.key) {
                    case 'ArrowRight':
                        e.preventDefault();
                        targetIndex = (currentIndex + 1) % tabButtons.length;
                        tabButtons[targetIndex].focus();
                        break;
                    case 'ArrowLeft':
                        e.preventDefault();
                        targetIndex = (currentIndex - 1 + tabButtons.length) % tabButtons.length;
                        tabButtons[targetIndex].focus();
                        break;
                    case 'Home':
                        e.preventDefault();
                        tabButtons[0].focus();
                        break;
                    case 'End':
                        e.preventDefault();
                        tabButtons[tabButtons.length - 1].focus();
                        break;
                }
            });
        });
    }

    // ========================================
    // Smooth scroll for anchor links
    // ========================================
    function initSmoothScroll() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function(e) {
                const targetId = this.getAttribute('href');
                if (targetId === '#') return;

                const target = document.querySelector(targetId);
                if (target) {
                    e.preventDefault();
                    const headerHeight = document.querySelector('.nav')?.offsetHeight || 72;
                    const targetPosition = target.getBoundingClientRect().top + window.pageYOffset - headerHeight;

                    window.scrollTo({
                        top: targetPosition,
                        behavior: 'smooth'
                    });

                    // Update URL without scroll jump
                    history.pushState(null, '', targetId);
                }
            });
        });
    }

    // ========================================
    // Intersection Observer for scroll animations
    // ========================================
    function initScrollAnimations() {
        const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        if (prefersReducedMotion) return;

        const observerOptions = {
            root: null,
            rootMargin: '0px 0px -10% 0px',
            threshold: 0.1
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.animationPlayState = 'running';
                    observer.unobserve(entry.target);
                }
            });
        }, observerOptions);

        // Observe elements with animation classes
        const animatedElements = document.querySelectorAll(
            '.feature-card, .prompt-card, .stat, .section-header, .cta'
        );

        animatedElements.forEach(el => {
            el.style.animationPlayState = 'paused';
            observer.observe(el);
        });
    }

    // ========================================
    // Active nav link on scroll
    // ========================================
    function initActiveNav() {
        const sections = document.querySelectorAll('section[id]');
        const navLinks = document.querySelectorAll('.nav-links a[href^="#"]');

        if (!sections.length || !navLinks.length) return;

        const observerOptions = {
            root: null,
            rootMargin: '-20% 0px -60% 0px',
            threshold: 0
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const id = entry.target.getAttribute('id');
                    navLinks.forEach(link => {
                        link.classList.toggle('active', link.getAttribute('href') === `#${id}`);
                    });
                }
            });
        }, observerOptions);

        sections.forEach(section => observer.observe(section));
    }

    // ========================================
    // Copy code blocks
    // ========================================
    function initCopyCode() {
        // Add copy buttons to code blocks
        document.querySelectorAll('pre').forEach(pre => {
            if (pre.querySelector('.copy-btn')) return;

            const btn = document.createElement('button');
            btn.className = 'copy-btn';
            btn.setAttribute('aria-label', 'Copy code');
            btn.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                </svg>
            `;
            btn.style.cssText = `
                position: absolute;
                top: 8px;
                right: 8px;
                padding: 6px;
                background: var(--bg-tertiary);
                border: 1px solid var(--border);
                border-radius: var(--radius-sm);
                color: var(--fg-secondary);
                cursor: pointer;
                opacity: 0;
                transition: opacity var(--transition-fast), color var(--transition-fast), background var(--transition-fast);
                display: flex;
                align-items: center;
                justify-content: center;
            `;

            pre.style.position = 'relative';
            pre.appendChild(btn);

            pre.addEventListener('mouseenter', () => btn.style.opacity = '1');
            pre.addEventListener('mouseleave', () => btn.style.opacity = '0');

            btn.addEventListener('click', async () => {
                const code = pre.querySelector('code')?.textContent || pre.textContent;
                try {
                    await navigator.clipboard.writeText(code);
                    btn.innerHTML = `
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="20 6 9 17 4 12"></polyline>
                        </svg>
                    `;
                    btn.style.color = 'var(--success)';
                    setTimeout(() => {
                        btn.innerHTML = `
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                            </svg>
                        `;
                        btn.style.color = '';
                    }, 1500);
                } catch (err) {
                    console.warn('Copy failed:', err);
                }
            });
        });
    }

    // ========================================
    // Initialize all functionality
    // ========================================
    function init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', init);
            return;
        }

        initTabs();
        initSmoothScroll();
        initScrollAnimations();
        initActiveNav();
        initCopyCode();

        // Log initialization
        console.log('%c🧠 Hermes Brain', 'font-size: 1.5rem; color: #1f6feb; font-weight: 700;', 'GitHub Pages site loaded');
    }

    // Start initialization
    init();

    // Expose for debugging
    window.HermesBrain = {
        initTabs,
        initSmoothScroll,
        initScrollAnimations,
        initActiveNav,
        initCopyCode
    };
})();