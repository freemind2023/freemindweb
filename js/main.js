/* ============================================================
   FREE MIND CONSULTANCY — main.js
   Navigation, scroll, counters, typewriter, FAQ, tabs,
   dark mode, back-to-top, mobile menu, page loader
   ============================================================ */

(function () {
  'use strict';

  /* ── 1. Page Loader ─────────────────────────────────────── */
  const loader = document.getElementById('page-loader');
  const loaderText = loader && loader.querySelector('.loader-text');

  if (loader && loaderText) {
    loaderText.classList.add('loader-text-animate');

    setTimeout(() => {
      loader.classList.add('loader-overlay-out');
      setTimeout(() => {
        loader.remove();
      }, 300);
    }, 1200);
  }

  /* ── 2. Dark Mode ───────────────────────────────────────── */
  const THEME_KEY = 'freemind-theme';
  const themeToggle = document.getElementById('theme-toggle');
  const mobileThemeToggle = document.getElementById('mobile-theme-toggle');

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    const label = theme === 'dark' ? 'Light' : 'Dark';
    if (themeToggle) themeToggle.textContent = label;
    if (mobileThemeToggle) mobileThemeToggle.textContent = label + ' Mode';
  }

  // Apply stored preference on load
  const stored = localStorage.getItem(THEME_KEY) || 'dark';
  applyTheme(stored);

  function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    const next = current === 'dark' ? 'light' : 'dark';
    localStorage.setItem(THEME_KEY, next);
    applyTheme(next);
  }

  if (themeToggle) themeToggle.addEventListener('click', toggleTheme);
  if (mobileThemeToggle) mobileThemeToggle.addEventListener('click', toggleTheme);

  /* ── 3. Sticky Navigation ───────────────────────────────── */
  const nav = document.querySelector('.site-nav');

  function handleScroll() {
    if (!nav) return;
    if (window.scrollY > 80) {
      nav.classList.add('scrolled');
    } else {
      nav.classList.remove('scrolled');
    }
    handleBackToTop();
  }

  window.addEventListener('scroll', handleScroll, { passive: true });

  /* ── 4. Mobile Hamburger Menu ───────────────────────────── */
  const hamburger    = document.getElementById('nav-hamburger');
  const mobileNav    = document.getElementById('nav-mobile');
  const categoryBtns = document.querySelectorAll('.mobile-category-btn');

  if (hamburger && mobileNav) {
    hamburger.addEventListener('click', () => {
      const isOpen = mobileNav.classList.toggle('open');
      hamburger.classList.toggle('active', isOpen);
      hamburger.setAttribute('aria-expanded', isOpen.toString());
    });

    // Close on outside click
    document.addEventListener('click', (e) => {
      if (!nav.contains(e.target) && !mobileNav.contains(e.target)) {
        mobileNav.classList.remove('open');
        hamburger.classList.remove('active');
        hamburger.setAttribute('aria-expanded', 'false');
      }
    });

    // Close nav when a link is clicked (but allow a short delay for tab switching)
    mobileNav.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => {
        setTimeout(() => {
          mobileNav.classList.remove('open');
          hamburger.classList.remove('active');
          hamburger.setAttribute('aria-expanded', 'false');
        }, 100);
      });
    });
  }

  // Mobile accordion categories — toggle sub-links open/close
  categoryBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation(); // prevent outside-click handler from firing
      const subLinks = btn.nextElementSibling;
      if (!subLinks) return;
      const isOpen = subLinks.classList.toggle('open');
      btn.classList.toggle('active', isOpen);
      btn.setAttribute('aria-expanded', isOpen.toString());
    });
  });

  /* ── 5. Typewriter Effect ───────────────────────────────── */
  const typewriterEl = document.getElementById('typewriter-word');
  const words = ['Change', 'Founders', 'Authors', 'Professors', 'Officers', 'Coaches'];
  let wordIndex = 0;
  let charIndex = 0;
  let isDeleting = false;
  const TYPING_SPEED  = 80;
  const DELETE_SPEED  = 40;
  const PAUSE_BEFORE_DELETE = 2000;

  function typeWriter() {
    if (!typewriterEl) return;

    const currentWord = words[wordIndex];

    if (!isDeleting) {
      typewriterEl.textContent = currentWord.slice(0, charIndex + 1);
      charIndex++;

      if (charIndex === currentWord.length) {
        isDeleting = true;
        setTimeout(typeWriter, PAUSE_BEFORE_DELETE);
        return;
      }
      setTimeout(typeWriter, TYPING_SPEED);
    } else {
      typewriterEl.textContent = currentWord.slice(0, charIndex - 1);
      charIndex--;

      if (charIndex === 0) {
        isDeleting = false;
        wordIndex = (wordIndex + 1) % words.length;
        setTimeout(typeWriter, TYPING_SPEED);
        return;
      }
      setTimeout(typeWriter, DELETE_SPEED);
    }
  }

  // Start typewriter after page loader
  setTimeout(typeWriter, 1400);

  /* ── 6. Scroll Reveal (IntersectionObserver) ────────────── */
  const revealEls = document.querySelectorAll('.fade-up, .fade-in, .slide-left, .slide-right');

  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('revealed');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15 });

    revealEls.forEach(el => observer.observe(el));
  } else {
    // Fallback: reveal all immediately
    revealEls.forEach(el => el.classList.add('revealed'));
  }

  /* ── 7. Animated Count-Up Numbers ──────────────────────── */
  const stats = document.querySelectorAll('[data-count]');

  function easeOutCubic(t) {
    return 1 - Math.pow(1 - t, 3);
  }

  function animateCount(el) {
    const target   = parseInt(el.getAttribute('data-count'), 10);
    const suffix   = el.getAttribute('data-suffix') || '';
    const duration = 2000;
    const start    = performance.now();

    function step(now) {
      const elapsed  = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased    = easeOutCubic(progress);
      const current  = Math.floor(eased * target);
      el.textContent = current + suffix;
      if (progress < 1) requestAnimationFrame(step);
    }

    requestAnimationFrame(step);
  }

  if ('IntersectionObserver' in window && stats.length) {
    const statsObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          animateCount(entry.target);
          statsObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.5 });

    stats.forEach(el => statsObserver.observe(el));
  }

  /* ── 8. Services Tabs ───────────────────────────────────── */
  const tabBtns   = document.querySelectorAll('.tab-btn');
  const tabPanels = document.querySelectorAll('.tab-panel');

  function activateTab(tabId) {
    tabBtns.forEach(btn => {
      btn.classList.toggle('active', btn.getAttribute('data-tab') === tabId);
      btn.setAttribute('aria-selected', btn.getAttribute('data-tab') === tabId ? 'true' : 'false');
    });
    tabPanels.forEach(panel => {
      const isActive = panel.getAttribute('data-panel') === tabId;
      panel.classList.toggle('active', isActive);
    });
  }

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      activateTab(btn.getAttribute('data-tab'));
    });
  });

  // Activate tab from URL hash or link
  function activateTabFromHash() {
    const hash = window.location.hash;
    if (hash && hash.includes('tab=')) {
      const tabId = hash.split('tab=')[1];
      activateTab(tabId);
      const servicesSection = document.getElementById('services');
      if (servicesSection) {
        setTimeout(() => {
          servicesSection.scrollIntoView({ behavior: 'smooth' });
        }, 100);
      }
    }
  }

  window.addEventListener('hashchange', activateTabFromHash);
  activateTabFromHash();

  // Audience card links to pre-activate a tab
  document.querySelectorAll('[data-tab-target]').forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const tabId = link.getAttribute('data-tab-target');
      activateTab(tabId);
      const servicesSection = document.getElementById('services');
      if (servicesSection) {
        servicesSection.scrollIntoView({ behavior: 'smooth' });
      }
    });
  });

  /* ── 9. Service Card "Learn More" Expand ────────────────── */
  document.querySelectorAll('.service-learn-more').forEach(btn => {
    btn.addEventListener('click', () => {
      const card    = btn.closest('.service-card');
      const details = card && card.querySelector('.service-details');
      if (!details) return;

      const isOpen = details.classList.toggle('open');
      btn.textContent = isOpen ? 'Show Less' : 'Learn More';
    });
  });

  /* ── 10. FAQ Accordion ──────────────────────────────────── */
  document.querySelectorAll('.faq-question').forEach(btn => {
    btn.addEventListener('click', () => {
      const item   = btn.closest('.faq-item');
      const answer = item && item.querySelector('.faq-answer');
      if (!item || !answer) return;

      const isOpen = item.classList.toggle('open');
      btn.setAttribute('aria-expanded', isOpen.toString());
    });
  });

  /* ── 11. Back to Top ────────────────────────────────────── */
  const backToTopBtn = document.getElementById('back-to-top');

  function handleBackToTop() {
    if (!backToTopBtn) return;
    if (window.scrollY > 400) {
      backToTopBtn.classList.add('visible');
    } else {
      backToTopBtn.classList.remove('visible');
    }
  }

  if (backToTopBtn) {
    backToTopBtn.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  /* ── 12. Stagger Reveal Children ───────────────────────── */
  // Add delay classes to stagger child reveal animations
  document.querySelectorAll('.stagger-children').forEach(parent => {
    const children = parent.children;
    Array.from(children).forEach((child, i) => {
      child.style.animationDelay = (i * 100) + 'ms';
    });
  });

  /* ── 13. Witty Tagline Underline Draw ──────────────────── */
  const witLine3 = document.querySelector('.wit-line-3');
  if (witLine3) {
    setTimeout(() => {
      witLine3.classList.add('line-animate');
    }, 3300); // fires after wit-line-3 animation completes
  }

  /* ── 14. Touch / Click Ripple Effect ───────────────────── */
  function spawnRipple(x, y) {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';

    // Outer ring
    const ring = document.createElement('div');
    ring.className = 'touch-ripple';
    ring.style.left = x + 'px';
    ring.style.top  = y + 'px';
    document.body.appendChild(ring);

    // Inner dot burst
    const dot = document.createElement('div');
    dot.className = 'touch-ripple-dot';
    dot.style.left = x + 'px';
    dot.style.top  = y + 'px';
    document.body.appendChild(dot);

    // Secondary larger ring (delayed)
    const ring2 = document.createElement('div');
    ring2.className = 'touch-ripple touch-ripple-2';
    ring2.style.left = x + 'px';
    ring2.style.top  = y + 'px';
    document.body.appendChild(ring2);

    // Cleanup after animation
    setTimeout(() => {
      ring.remove();
      dot.remove();
      ring2.remove();
    }, 900);
  }

  // Touch events (mobile)
  document.addEventListener('touchstart', (e) => {
    const touch = e.touches[0];
    spawnRipple(touch.clientX, touch.clientY);
  }, { passive: true });

  // Click events (desktop)
  document.addEventListener('click', (e) => {
    // Skip if it's a button/link to avoid double-fire confusion
    if (e.target.closest('button, a, input, select, textarea')) return;
    spawnRipple(e.clientX, e.clientY);
  });

  /* ── Initial scroll state ───────────────────────────────── */
  handleScroll();

})();
