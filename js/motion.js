/* ============================================================
   FREE MIND — motion.js
   Global motion engine. Vanilla JS, no dependencies.

   Declarative API (attributes; most are auto-applied below):
     data-motion="fade-up | scale | reveal | slide-left | slide-right"
                              reveal once when entering (LOW/MEDIUM)
     data-motion="words"      headline reveals word-by-word with scroll
     data-motion="scene-out"  hero leaves as the next scene arrives
     data-motion="scene-leave" section recedes as the next one arrives
     data-motion="parallax"   subtle drift (data-par="px", desktop only)
     data-motion="focus"      children dim/scale by distance to centre
     data-motion="progress"   timeline line + steps follow scroll
     data-motion="horizontal" pinned horizontal track (desktop only)
     data-motion-stagger      on a parent: children reveal in sequence

   Everything is stateless (progress is recomputed from the element's
   real position on every scroll frame), so fast scrolling and reverse
   scrolling cannot desynchronise it. Nothing runs unless the user has
   not asked for reduced motion.
   ============================================================ */
(function () {
  'use strict';

  var root = document.documentElement;
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)');
  if (reduce.matches) return;

  var desktop = window.matchMedia('(min-width: 1100px) and (min-height: 600px)');
  var vh = window.innerHeight;
  var navH = 80;

  var scrub = [];       // {el, kind, active, ...}
  var revealIO, activeIO;
  var ticking = false;
  var started = false;

  function q(sel, ctx) { return Array.prototype.slice.call((ctx || document).querySelectorAll(sel)); }
  function clamp(v, a, b) { return v < a ? a : v > b ? b : v; }
  function setVar(el, name, val) {
    var key = '_' + name;
    if (el[key] !== undefined && Math.abs(el[key] - val) < 0.003) return;
    el[key] = val;
    el.style.setProperty(name, (Math.round(val * 1000) / 1000).toString());
  }

  /* ── Tagging ─────────────────────────────────────────────── */
  var LEGACY = ['fade-up', 'fade-in', 'slide-left', 'slide-right'];
  function tag(el, type) {
    if (!el || el.hasAttribute('data-motion')) return;
    if (el.closest('.faqc, .logo-wall-row, .site-nav, .nav-mobile, [data-no-motion]')) return;
    LEGACY.forEach(function (c) { el.classList.remove(c); });
    el.setAttribute('data-motion', type);
  }
  function stagger(parent, type) {
    if (!parent || parent.closest('.faqc, .logo-wall-row, [data-no-motion]')) return;
    Array.prototype.forEach.call(parent.children, function (child, i) {
      tag(child, type || 'fade-up');
      child.style.setProperty('--i', Math.min(i, 7));
    });
  }

  function autoTag() {
    /* Headlines: HIGH — scroll-scrubbed words */
    q('.section-heading').forEach(function (h) { tag(h, 'words'); });
    q('.section-label, .section-subtitle').forEach(function (e) { tag(e, 'fade-up'); });

    /* Card groups: MEDIUM — staggered */
    ['.insights-grid', '.achievements-grid', '.testimonials-grid', '.focus-grid', '.series-grid',
     '.stats-grid', '.blog-grid', '.pm-banner-stats']
      .forEach(function (s) { q(s).forEach(function (p) { stagger(p, 'fade-up'); }); });
    q('.blog-card').forEach(function (c) {
      var p = c.parentElement;
      if (p && !p.__st) { p.__st = 1; stagger(p, 'fade-up'); }
    });
    q('.publishmatch-banner .pm-banner-left, .podcast-banner-left, .koelai-content').forEach(function (e) { tag(e, 'fade-up'); });
    q('.koelai-visual').forEach(function (e) { tag(e, 'parallax'); e.setAttribute('data-par', '34'); });
    q('.contact-info').forEach(function (e) { tag(e, 'slide-left'); });
    q('.contact-form-wrap, .contact-form, #contact-form').forEach(function (e) { tag(e.closest('.contact-grid > *') || e, 'slide-right'); });

    /* HIGH — services: the card nearest the centre is "active" */
    q('.services-grid').forEach(function (g) {
      g.setAttribute('data-motion', 'focus');
      Array.prototype.forEach.call(g.children, function (c) {
        LEGACY.forEach(function (k) { c.classList.remove(k); });
        c.classList.add('m-focus-item');
      });
    });

    /* HIGH — process progress line */
    q('.timeline').forEach(function (t) { t.setAttribute('data-motion', 'progress'); });

    /* HIGH — hero leaves as the next scene takes over */
    q('.hero-content, .hero-visual').forEach(function (e) { LEGACY.forEach(function (c) { e.classList.remove(c); }); });
    q('.hero, .inner-page, .blog-hero, .day-hero, .series-hero').forEach(function (h) {
      if (!h.hasAttribute('data-motion')) h.setAttribute('data-motion', 'scene-out');
    });
    /* sections recede as the next one arrives */
    q('#about, #achievements, #tech-platforms, .section-light:not(.contact-texture)').forEach(function (s) {
      if (!s.hasAttribute('data-motion') && !s.querySelector('.audience-grid') && s.querySelector(':scope > .container')) s.setAttribute('data-motion', 'scene-leave');
    });

    /* HIGH (desktop) — audiences become a pinned horizontal track */
    q('.audience-grid').forEach(function (g) {
      var sec = g.closest('section');
      if (sec) sec.setAttribute('data-motion', 'horizontal');
      g.classList.add('hs-track');
      Array.prototype.forEach.call(g.children, function (c) { LEGACY.forEach(function (k) { c.classList.remove(k); }); });
    });

    /* Inner pages (service / hub / blog / product / day pages) */
    q('main section h2[style], main section .container > h2').forEach(function (h) { tag(h, 'fade-up'); });
    q('main .container > div[style*="display:grid"]').forEach(function (g) { stagger(g, 'fade-up'); });
    q('.day-card').forEach(function (c) { var p = c.parentElement; if (p && !p.__st) { p.__st = 1; stagger(p, 'fade-up'); } });
    q('.cta-box, .checklist-box, .callout, .source-note, .disclaimer-note, .external-resource-box, .example-box, .coming-soon-note')
      .forEach(function (e) { tag(e, 'fade-up'); });
    q('.day-article h2, .blog-post-body h2').forEach(function (h) { tag(h, 'fade-up'); });
    q('article img:not(.hero-visual-img), .blog-post-body img, .day-article img').forEach(function (i) { tag(i, 'reveal'); });

    /* Footer: one calm reveal */
    q('.site-footer .footer-grid, .site-footer .footer-bottom').forEach(function (e) { tag(e, 'fade-up'); });
  }

  /* ── Words split (keeps every word as real text in the DOM) ── */
  function splitWords(el) {
    var count = 0;
    (function walk(node) {
      Array.prototype.slice.call(node.childNodes).forEach(function (n) {
        if (n.nodeType === 3) {
          var parts = n.nodeValue.split(/(\s+)/);
          if (!parts.join('').trim()) return;
          var frag = document.createDocumentFragment();
          parts.forEach(function (p) {
            if (!p) return;
            if (/^\s+$/.test(p)) { frag.appendChild(document.createTextNode(p)); return; }
            var s = document.createElement('span');
            s.className = 'mw'; s.style.setProperty('--i', count++); s.textContent = p;
            frag.appendChild(s);
          });
          n.parentNode.replaceChild(frag, n);
        } else if (n.nodeType === 1 && n.tagName !== 'BR') walk(n);
      });
    })(el);
    el.style.setProperty('--n', count);
  }

  /* ── One-shot reveal ─────────────────────────────────────── */
  function setupReveal() {
    var list = q('[data-motion="fade-up"], [data-motion="scale"], [data-motion="reveal"], [data-motion="slide-left"], [data-motion="slide-right"]');
    revealIO = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        var el = e.target;
        revealIO.unobserve(el);
        el.classList.add('m-in');
        el.classList.remove('m-hide');
        // hand transitions back to the element's own CSS once the reveal is done
        setTimeout(function () { el.classList.remove('m-in'); }, 1900);
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.01 });
    list.forEach(function (el) {
      var r = el.getBoundingClientRect();
      if (r.width === 0 && r.height === 0) return;          // hidden panel: leave alone
      if (r.top > vh * 0.92) { el.classList.add('m-hide'); revealIO.observe(el); }
    });
  }

  /* ── Scroll-driven entries ───────────────────────────────── */
  function register(el, kind, extra) {
    var e = { el: el, kind: kind, active: false };
    if (extra) for (var k in extra) e[k] = extra[k];
    scrub.push(e);
    return e;
  }

  function setupScrub() {
    q('[data-motion="words"]').forEach(function (h) { splitWords(h); register(h, 'words'); });
    q('[data-motion="scene-out"]').forEach(function (s) { register(s, 'scene-out'); });
    q('[data-motion="scene-leave"]').forEach(function (s) { register(s, 'scene-leave'); });
    q('[data-motion="parallax"]').forEach(function (s) { register(s, 'parallax', { par: parseFloat(s.getAttribute('data-par')) || 30 }); });
    q('[data-motion="focus"]').forEach(function (g) { register(g, 'focus'); });
    q('[data-motion="progress"]').forEach(function (t) { register(t, 'progress', { steps: q('.timeline-step', t) }); });
    q('[data-motion="horizontal"]').forEach(function (s) { register(s, 'horizontal', { on: false }); });

    activeIO = new IntersectionObserver(function (entries) {
      entries.forEach(function (ie) {
        for (var i = 0; i < scrub.length; i++) if (scrub[i].el === ie.target) scrub[i].active = ie.isIntersecting;
      });
      requestTick();
    }, { rootMargin: '25% 0px 25% 0px' });
    scrub.forEach(function (e) { activeIO.observe(e.el); });
  }

  /* ── Pinned horizontal track (desktop) ───────────────────── */
  function setupHorizontal() {
    scrub.forEach(function (e) {
      if (e.kind !== 'horizontal') return;
      var sec = e.el, track = sec.querySelector('.hs-track'), box = sec.querySelector(':scope > .container');
      // reset
      sec.classList.remove('hs-on'); sec.style.height = ''; if (box) box.style.removeProperty('--hs-top'); if (track) track.style.removeProperty('--hx');
      e.on = false;
      if (!desktop.matches || !track || !box) return;
      sec.classList.add('hs-on');
      var cs = getComputedStyle(box);
      var avail = box.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
      var dist = track.scrollWidth - avail;
      if (dist < 60) { sec.classList.remove('hs-on'); return; }
      var boxH = box.offsetHeight;
      e.top = Math.max(navH + 8, Math.round((window.innerHeight - boxH) / 2));
      box.style.setProperty('--hs-top', e.top + 'px');
      e.dist = dist; e.avail = avail; e.track = track; e.boxOffset = parseFloat(getComputedStyle(sec).paddingTop) || 0; e.on = true;
      sec.style.height = 'auto';
      sec.style.height = Math.round(sec.offsetHeight + dist) + 'px';
    });
  }

  /* Keyboard focus inside the pinned track: the clipped box must never scroll
     natively (it would double-shift the cards). Reset it and move the page scroll
     to the position where the focused card is fully in view. */
  function onFocusIn(ev) {
    for (var i = 0; i < scrub.length; i++) {
      var e = scrub[i];
      if (e.kind !== 'horizontal' || !e.on || !e.track.contains(ev.target)) continue;
      var box = e.el.firstElementChild;
      if (box.scrollLeft) box.scrollLeft = 0;
      var card = ev.target;
      while (card.parentElement !== e.track) card = card.parentElement;
      var tl = e.track.getBoundingClientRect().left, cr = card.getBoundingClientRect();
      var hx = parseFloat(e.track.style.getPropertyValue('--hx')) || 0;
      var left = cr.left - tl, right = cr.right - tl;
      var want = left < hx ? left : right > hx + e.avail ? right - e.avail : hx;
      want = clamp(want, 0, e.dist);
      var top = e.el.getBoundingClientRect().top + window.pageYOffset + e.boxOffset - e.top + want;
      if (Math.abs(top - window.pageYOffset) > 2) window.scrollTo({ top: top, behavior: 'instant' });
    }
  }

  /* ── The single scroll frame ─────────────────────────────── */
  function update() {
    ticking = false;
    vh = window.innerHeight;
    var dsk = desktop.matches;
    var reads = [], i, e, r;
    for (i = 0; i < scrub.length; i++) {
      e = scrub[i];
      if (!e.active && started) continue;
      reads.push([e, e.el.getBoundingClientRect()]);
    }
    for (i = 0; i < reads.length; i++) {
      e = reads[i][0]; r = reads[i][1];
      if (r.width === 0 && r.height === 0 && e.kind !== 'horizontal') continue;
      switch (e.kind) {
        case 'words':
          setVar(e.el, '--p', clamp((vh * 0.9 - r.top) / (vh * 0.5), 0, 1)); break;
        case 'scene-out':
          setVar(e.el, '--p', clamp(-r.top / (Math.max(r.height, vh * 0.6) * 0.85), 0, 1)); break;
        case 'scene-leave':
          setVar(e.el, '--p', clamp((vh * 0.55 - r.bottom) / (vh * 0.55), 0, 1)); break;
        case 'parallax':
          setVar(e.el, '--p', clamp((vh - r.top) / (vh + r.height), 0, 1));
          if (e.el.style.getPropertyValue('--par') !== (dsk ? e.par + 'px' : '0px')) e.el.style.setProperty('--par', dsk ? e.par + 'px' : '0px');
          break;
        case 'focus':
          var kids = e.el.children, k, ds = [];
          for (k = 0; k < kids.length; k++) {           // all reads first...
            var cr = kids[k].getBoundingClientRect();
            ds.push(cr.height === 0 ? -1 : clamp(Math.abs(cr.top + cr.height / 2 - vh * 0.5) / (vh * 0.62), 0, 1));
          }
          for (k = 0; k < kids.length; k++) if (ds[k] >= 0) setVar(kids[k], '--d', ds[k] * ds[k]);   // ...then writes
          break;
        case 'progress':
          var p = clamp((vh * 0.78 - r.top) / (r.height * 0.9 + 1), 0, 1);
          setVar(e.el, '--p', p);
          for (var s = 0; s < e.steps.length; s++) {
            var on = p >= (s + 0.3) / e.steps.length;
            if (e.steps[s]._on !== on) { e.steps[s]._on = on; e.steps[s].classList.toggle('is-on', on); }
          }
          break;
        case 'horizontal':
          if (!e.on) break;
          var pr = clamp((e.top - (r.top + e.boxOffset)) / e.dist, 0, 1);
          e.track.style.setProperty('--hx', Math.round(pr * e.dist) + 'px');
          break;
      }
    }
    started = true;
  }
  function requestTick() { if (!ticking) { ticking = true; requestAnimationFrame(update); } }

  /* ── Lifecycle ───────────────────────────────────────────── */
  var resizeTimer;
  function onResize() {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function () { vh = window.innerHeight; setupHorizontal(); requestTick(); }, 150);
  }
  function teardown() {
    root.classList.remove('motion-on');
    q('.m-hide, .m-in').forEach(function (el) { el.classList.remove('m-hide', 'm-in'); });
    q('.hs-on').forEach(function (el) { el.classList.remove('hs-on'); el.style.height = ''; });
  }

  function init() {
    var nav = document.querySelector('.site-nav');
    if (nav) navH = nav.getBoundingClientRect().height || 80;
    root.classList.add('motion-on');
    autoTag();
    setupReveal();
    setupScrub();
    setupHorizontal();
    update();                                 // paint correct initial states immediately
    window.addEventListener('scroll', requestTick, { passive: true });
    document.addEventListener('focusin', onFocusIn);
    window.addEventListener('resize', onResize, { passive: true });
    window.addEventListener('orientationchange', onResize, { passive: true });
    window.addEventListener('load', function () { setupHorizontal(); requestTick(); });
    if (desktop.addEventListener) desktop.addEventListener('change', onResize);
    if (reduce.addEventListener) reduce.addEventListener('change', function (ev) { if (ev.matches) teardown(); });
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(function () { setupHorizontal(); requestTick(); });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
