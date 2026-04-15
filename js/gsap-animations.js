/* ============================================================
   FREE MIND CONSULTANCY — gsap-animations.js
   GSAP + ScrollTrigger animations — all sections
   Respects prefers-reduced-motion. Never alters content.
   ============================================================ */

(function () {
  'use strict';

  // Bail early if GSAP not loaded or user prefers reduced motion
  if (typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') return;
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  gsap.registerPlugin(ScrollTrigger);

  /* ── Helpers ─────────────────────────────────────────────── */

  // Shorthand: create a scrollTrigger-driven fromTo
  function reveal(targets, vars, triggerEl, start) {
    return gsap.from(targets, {
      scrollTrigger: {
        trigger: triggerEl || targets,
        start: start || 'top 82%',
        once: true,
      },
      ...vars,
    });
  }

  // Stagger reveal for a group of children
  function staggerReveal(targets, vars, triggerEl, start) {
    return gsap.from(targets, {
      scrollTrigger: {
        trigger: triggerEl || (targets[0] && targets[0].parentElement) || targets,
        start: start || 'top 80%',
        once: true,
      },
      ...vars,
    });
  }

  // ── Wait for page loader to finish ──────────────────────────
  // main.js removes loader after ~1200ms
  const LOADER_DELAY = 1.35;

  /* ============================================================
     1. NAV — stagger items in from top on load
  ============================================================ */
  const navLinks = gsap.utils.toArray('.nav-links > a, .nav-links > .nav-dropdown-trigger');
  if (navLinks.length) {
    gsap.from(navLinks, {
      y: -18,
      opacity: 0,
      stagger: 0.07,
      duration: 0.55,
      delay: LOADER_DELAY,
      ease: 'power3.out',
      clearProps: 'transform,opacity',
    });
    gsap.from('.nav-right .btn, .nav-right .theme-toggle', {
      y: -18,
      opacity: 0,
      stagger: 0.08,
      duration: 0.55,
      delay: LOADER_DELAY + 0.2,
      ease: 'power3.out',
      clearProps: 'transform,opacity',
    });
  }

  /* ============================================================
     2. HERO — sequenced timeline after loader
  ============================================================ */
  const heroTl = gsap.timeline({ delay: LOADER_DELAY });

  // Logo circle: scale + fade
  if (document.querySelector('.hero-logo-circle')) {
    heroTl.from('.hero-logo-circle', {
      scale: 0.55,
      opacity: 0,
      duration: 0.9,
      ease: 'back.out(1.6)',
    });
  }

  // Tagline lines stagger up
  const witLines = gsap.utils.toArray('.wit-line-1, .wit-line-2, .wit-line-3');
  if (witLines.length) {
    heroTl.from(witLines, {
      y: 48,
      opacity: 0,
      stagger: 0.12,
      duration: 0.65,
      ease: 'power3.out',
      clearProps: 'transform,opacity',
    }, '-=0.5');
  }

  // CTA buttons
  const heroCTAs = gsap.utils.toArray('.hero-ctas .btn');
  if (heroCTAs.length) {
    heroTl.from(heroCTAs, {
      y: 24,
      opacity: 0,
      stagger: 0.12,
      duration: 0.55,
      ease: 'power2.out',
      clearProps: 'transform,opacity',
    }, '-=0.3');
  }

  // Scroll hint
  if (document.querySelector('.hero-scroll-hint')) {
    heroTl.from('.hero-scroll-hint', {
      opacity: 0,
      y: 10,
      duration: 0.5,
      ease: 'power1.out',
    }, '-=0.15');
  }

  /* ============================================================
     3. SECTION LABELS — clip-path slide in from left
  ============================================================ */
  gsap.utils.toArray('.section-label').forEach(label => {
    gsap.from(label, {
      scrollTrigger: { trigger: label, start: 'top 88%', once: true },
      clipPath: 'inset(0% 100% 0% 0%)',
      opacity: 0,
      duration: 0.6,
      ease: 'power2.inOut',
      clearProps: 'clip-path,opacity',
    });
  });

  /* ============================================================
     4. SECTION HEADINGS — translate + fade per heading
  ============================================================ */
  gsap.utils.toArray('.section-heading').forEach(heading => {
    gsap.from(heading, {
      scrollTrigger: { trigger: heading, start: 'top 85%', once: true },
      y: 40,
      opacity: 0,
      duration: 0.75,
      ease: 'power3.out',
      clearProps: 'transform,opacity',
    });
  });

  /* ============================================================
     5. PODCAST BANNER
  ============================================================ */
  if (document.querySelector('.podcast-banner')) {
    gsap.from('.podcast-banner', {
      scrollTrigger: { trigger: '.podcast-banner', start: 'top 85%', once: true },
      y: 50,
      opacity: 0,
      duration: 0.8,
      ease: 'power3.out',
    });
  }

  /* ============================================================
     6. STATS BAR — each item scales up + blurs in
  ============================================================ */
  const statItems = gsap.utils.toArray('.stat-item, .stats-grid > *');
  if (statItems.length) {
    staggerReveal(statItems, {
      y: 40,
      opacity: 0,
      scale: 0.88,
      filter: 'blur(6px)',
      stagger: { amount: 0.5, ease: 'power1.in' },
      duration: 0.7,
      ease: 'power3.out',
      clearProps: 'transform,opacity,filter',
    }, statItems[0].closest('section') || statItems[0].parentElement);
  }

  /* ============================================================
     7. KOELAI SECTION — content block reveal
  ============================================================ */
  if (document.querySelector('.koelai-content')) {
    gsap.from('.koelai-content', {
      scrollTrigger: { trigger: '.koelai-section', start: 'top 75%', once: true },
      x: 60,
      opacity: 0,
      duration: 0.9,
      ease: 'power3.out',
      clearProps: 'transform,opacity',
    });
    gsap.from('.koelai-visual', {
      scrollTrigger: { trigger: '.koelai-section', start: 'top 75%', once: true },
      x: -60,
      opacity: 0,
      duration: 0.9,
      ease: 'power3.out',
      clearProps: 'transform,opacity',
    });
  }

  // Koelai feature list items stagger
  const koelaiFeatures = gsap.utils.toArray('.koelai-feature, .koelai-features li, .koelai-list li');
  if (koelaiFeatures.length) {
    staggerReveal(koelaiFeatures, {
      x: 20,
      opacity: 0,
      stagger: 0.08,
      duration: 0.5,
      ease: 'power2.out',
      clearProps: 'transform,opacity',
    }, '.koelai-section', 'top 70%');
  }

  /* ============================================================
     8. PUBLISHMATCH BANNER — stats stagger
  ============================================================ */
  const pmStats = gsap.utils.toArray('.pm-banner-stats > *, .pm-stat');
  if (pmStats.length) {
    staggerReveal(pmStats, {
      y: 30,
      opacity: 0,
      scale: 0.9,
      stagger: 0.12,
      duration: 0.6,
      ease: 'back.out(1.4)',
      clearProps: 'transform,opacity',
    }, '.publishmatch-banner', 'top 75%');
  }

  if (document.querySelector('.pm-banner-left')) {
    gsap.from('.pm-banner-left', {
      scrollTrigger: { trigger: '.publishmatch-banner', start: 'top 78%', once: true },
      x: -50,
      opacity: 0,
      duration: 0.85,
      ease: 'power3.out',
      clearProps: 'transform,opacity',
    });
  }

  /* ============================================================
     9. ABOUT SECTION
  ============================================================ */
  if (document.querySelector('.about-grid')) {
    gsap.from('.about-text', {
      scrollTrigger: { trigger: '.about-grid', start: 'top 78%', once: true },
      x: -50,
      opacity: 0,
      duration: 0.85,
      ease: 'power3.out',
      clearProps: 'transform,opacity',
    });

    const aboutRight = document.querySelector('.about-visual, .about-image, .about-grid > div:last-child');
    if (aboutRight) {
      gsap.from(aboutRight, {
        scrollTrigger: { trigger: '.about-grid', start: 'top 78%', once: true },
        x: 50,
        opacity: 0,
        duration: 0.85,
        ease: 'power3.out',
        clearProps: 'transform,opacity',
      });
    }

    // About values/points stagger
    const aboutPoints = gsap.utils.toArray('.about-value, .about-point, .about-highlight, .value-item');
    if (aboutPoints.length) {
      staggerReveal(aboutPoints, {
        y: 20,
        opacity: 0,
        stagger: 0.1,
        duration: 0.5,
        ease: 'power2.out',
        clearProps: 'transform,opacity',
      }, '.about-grid', 'top 72%');
    }
  }

  /* ============================================================
     10. AUDIENCE CARDS
  ============================================================ */
  const audienceCards = gsap.utils.toArray('.audience-card');
  if (audienceCards.length) {
    staggerReveal(audienceCards, {
      y: 55,
      opacity: 0,
      scale: 0.94,
      stagger: { amount: 0.55, ease: 'power1.inOut' },
      duration: 0.65,
      ease: 'power3.out',
      clearProps: 'transform,opacity',
    }, '.audience-grid, .audience-cards', 'top 78%');
  }

  /* ============================================================
     11. SERVICES — tab buttons + active panel cards
  ============================================================ */
  const tabBtns = gsap.utils.toArray('.tab-btn');
  if (tabBtns.length) {
    staggerReveal(tabBtns, {
      y: 20,
      opacity: 0,
      stagger: 0.06,
      duration: 0.45,
      ease: 'power2.out',
      clearProps: 'transform,opacity',
    }, '.tabs-nav, .tab-buttons', 'top 85%');
  }

  // Animate service cards when they first become visible in active tab
  function animateActiveTabCards() {
    const activePanel = document.querySelector('.tab-panel.active');
    if (!activePanel) return;
    const cards = gsap.utils.toArray('.tab-panel.active .service-card');
    if (!cards.length) return;
    gsap.from(cards, {
      y: 35,
      opacity: 0,
      scale: 0.96,
      stagger: { amount: 0.5, from: 'start' },
      duration: 0.55,
      ease: 'power3.out',
      clearProps: 'transform,opacity',
    });
  }

  // Fire on page load for the default active tab
  ScrollTrigger.create({
    trigger: '#services',
    start: 'top 80%',
    once: true,
    onEnter: animateActiveTabCards,
  });

  // Re-animate when tab switches
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      setTimeout(animateActiveTabCards, 50);
    });
  });

  /* ============================================================
     12. PROCESS STEPS — sequential slide from left
  ============================================================ */
  const processSteps = gsap.utils.toArray('.step, .process-step, .steps-grid > *');
  if (processSteps.length) {
    staggerReveal(processSteps, {
      x: -45,
      opacity: 0,
      stagger: { amount: 0.6, ease: 'power1.in' },
      duration: 0.65,
      ease: 'power3.out',
      clearProps: 'transform,opacity',
    }, processSteps[0].closest('section') || '.steps-grid', 'top 78%');
  }

  /* ============================================================
     13. ACHIEVEMENTS — scale + fade stagger
  ============================================================ */
  const achieveItems = gsap.utils.toArray('.achievement-item, .achievements-grid > *');
  if (achieveItems.length) {
    staggerReveal(achieveItems, {
      scale: 0.8,
      opacity: 0,
      y: 30,
      stagger: { amount: 0.5, from: 'center' },
      duration: 0.65,
      ease: 'back.out(1.5)',
      clearProps: 'transform,opacity',
    }, achieveItems[0].closest('section') || '.achievements-grid', 'top 78%');
  }

  /* ============================================================
     14. TESTIMONIALS — stagger with slight rotation
  ============================================================ */
  const testimonialCards = gsap.utils.toArray('.testimonial-card, .testimonials-grid > *');
  if (testimonialCards.length) {
    staggerReveal(testimonialCards, {
      y: 50,
      opacity: 0,
      rotation: 1.5,
      stagger: 0.15,
      duration: 0.7,
      ease: 'power3.out',
      clearProps: 'transform,opacity',
    }, testimonialCards[0].closest('section'), 'top 80%');
  }

  /* ============================================================
     15. FAQ — cascade reveal
  ============================================================ */
  const faqItems = gsap.utils.toArray('.faq-item');
  if (faqItems.length) {
    staggerReveal(faqItems, {
      y: 28,
      opacity: 0,
      stagger: 0.07,
      duration: 0.5,
      ease: 'power2.out',
      clearProps: 'transform,opacity',
    }, '#faq', 'top 80%');
  }

  /* ============================================================
     16. CONTACT — form groups stagger up
  ============================================================ */
  const formGroups = gsap.utils.toArray('#contact-form .form-group, #contact-form .form-row');
  if (formGroups.length) {
    staggerReveal(formGroups, {
      y: 25,
      opacity: 0,
      stagger: 0.06,
      duration: 0.48,
      ease: 'power2.out',
      clearProps: 'transform,opacity',
    }, '#contact-form', 'top 80%');
  }

  // Contact left column
  if (document.querySelector('.contact-info, .contact-left')) {
    gsap.from('.contact-info, .contact-left', {
      scrollTrigger: { trigger: '#contact', start: 'top 78%', once: true },
      x: -40,
      opacity: 0,
      duration: 0.8,
      ease: 'power3.out',
      clearProps: 'transform,opacity',
    });
  }

  /* ============================================================
     17. FOOTER — fade in sections
  ============================================================ */
  const footerCols = gsap.utils.toArray('.footer-grid > div, .footer-grid > *');
  if (footerCols.length) {
    staggerReveal(footerCols, {
      y: 30,
      opacity: 0,
      stagger: 0.1,
      duration: 0.6,
      ease: 'power2.out',
      clearProps: 'transform,opacity',
    }, '.site-footer', 'top 90%');
  }

  /* ============================================================
     18. MAGNETIC HOVER — primary buttons (desktop only)
  ============================================================ */
  if (window.innerWidth > 768) {
    document.querySelectorAll('.btn-primary').forEach(btn => {
      btn.addEventListener('mousemove', (e) => {
        const rect = btn.getBoundingClientRect();
        const x = e.clientX - rect.left - rect.width / 2;
        const y = e.clientY - rect.top - rect.height / 2;
        gsap.to(btn, {
          x: x * 0.28,
          y: y * 0.28,
          duration: 0.35,
          ease: 'power2.out',
        });
      });
      btn.addEventListener('mouseleave', () => {
        gsap.to(btn, {
          x: 0,
          y: 0,
          duration: 0.6,
          ease: 'elastic.out(1, 0.55)',
        });
      });
    });

    // Subtle magnetic on nav CTA specifically
    const navCta = document.querySelector('.nav-cta');
    if (navCta) {
      navCta.addEventListener('mousemove', (e) => {
        const rect = navCta.getBoundingClientRect();
        const x = e.clientX - rect.left - rect.width / 2;
        const y = e.clientY - rect.top - rect.height / 2;
        gsap.to(navCta, { x: x * 0.2, y: y * 0.2, duration: 0.3, ease: 'power2.out' });
      });
      navCta.addEventListener('mouseleave', () => {
        gsap.to(navCta, { x: 0, y: 0, duration: 0.5, ease: 'elastic.out(1, 0.5)' });
      });
    }
  }

  /* ============================================================
     19. HORIZONTAL PARALLAX — stats bar text at different speed
  ============================================================ */
  if (document.querySelector('.stats-bar')) {
    gsap.to('.stats-bar .stats-grid', {
      scrollTrigger: {
        trigger: '.stats-bar',
        start: 'top bottom',
        end: 'bottom top',
        scrub: 1.5,
      },
      y: -18,
      ease: 'none',
    });
  }

  /* ============================================================
     20. SCROLL-LINKED HERO RULE fade
  ============================================================ */
  if (document.querySelector('.hero-rule')) {
    gsap.to('.hero-rule', {
      scrollTrigger: {
        trigger: '.hero',
        start: 'top top',
        end: 'bottom top',
        scrub: true,
      },
      scaleX: 0,
      opacity: 0,
      ease: 'none',
    });
  }

  /* ============================================================
     21. BLOG CARDS (blog/index.html)
  ============================================================ */
  const blogCards = gsap.utils.toArray('.blog-card');
  if (blogCards.length) {
    staggerReveal(blogCards, {
      y: 45,
      opacity: 0,
      scale: 0.95,
      stagger: { amount: 0.7, ease: 'power1.inOut' },
      duration: 0.6,
      ease: 'power3.out',
      clearProps: 'transform,opacity',
    }, '#blog-grid', 'top 82%');
  }

  /* ============================================================
     22. SERVICE PAGE CARDS (services/*.html)
  ============================================================ */
  const servicePageCards = gsap.utils.toArray('.service-page-card, .services-list > *, .service-item');
  if (servicePageCards.length) {
    staggerReveal(servicePageCards, {
      y: 40,
      opacity: 0,
      stagger: 0.1,
      duration: 0.6,
      ease: 'power3.out',
      clearProps: 'transform,opacity',
    }, servicePageCards[0].parentElement, 'top 80%');
  }

  /* ============================================================
     23. BLOG POST BODY — paragraphs and headings cascade
  ============================================================ */
  const blogBody = document.querySelector('.blog-post-body');
  if (blogBody) {
    const blogEls = gsap.utils.toArray('.blog-post-body h2, .blog-post-body h3, .blog-post-body .callout, .blog-post-body .cta-box, .blog-post-body .faq-item, .blog-post-body .blog-step, .blog-post-body table');
    blogEls.forEach(el => {
      gsap.from(el, {
        scrollTrigger: { trigger: el, start: 'top 88%', once: true },
        y: 30,
        opacity: 0,
        duration: 0.55,
        ease: 'power2.out',
        clearProps: 'transform,opacity',
      });
    });
  }

  /* ============================================================
     24. KOELAI PRODUCT PAGE
  ============================================================ */
  const koelaiUseCases = gsap.utils.toArray('.use-case-card, .koelai-use-case');
  if (koelaiUseCases.length) {
    staggerReveal(koelaiUseCases, {
      y: 35,
      opacity: 0,
      scale: 0.93,
      stagger: { amount: 0.6, from: 'start' },
      duration: 0.55,
      ease: 'back.out(1.3)',
      clearProps: 'transform,opacity',
    }, koelaiUseCases[0].parentElement, 'top 80%');
  }

  /* ============================================================
     25. REFRESH SCROLL TRIGGER after all setup
  ============================================================ */
  ScrollTrigger.refresh();

})();
