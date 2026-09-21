/* FAQ cards — category tabs + one-active-card-per-category interaction.
   Progressive enhancement: without JS every question and answer stays visible. */
(function () {
  'use strict';
  var root = document.getElementById('faq-cards');
  if (!root) return;

  var panels = Array.prototype.slice.call(root.querySelectorAll('.faqc-panel'));
  if (!panels.length) return;
  var desktop = window.matchMedia('(min-width: 1000px)');
  var tabs = [];
  var selected = 0;

  root.classList.add('is-enhanced');

  /* ── Category tabs, built from each panel's heading ─────── */
  var tablist = document.createElement('div');
  tablist.className = 'faqc-tabs';
  tablist.setAttribute('role', 'tablist');
  tablist.setAttribute('aria-label', 'FAQ categories');

  panels.forEach(function (panel, i) {
    var tab = document.createElement('button');
    tab.type = 'button';
    tab.className = 'faqc-tab';
    tab.id = 'faqc-tab-' + i;
    tab.setAttribute('role', 'tab');
    tab.setAttribute('aria-controls', panel.id);
    tab.innerHTML = panel.querySelector('.faqc-title').innerHTML;
    tab.addEventListener('click', function () { selectTab(i, false); });
    tab.addEventListener('keydown', function (e) {
      var n = panels.length, to = -1;
      if (e.key === 'ArrowRight') to = (i + 1) % n;
      else if (e.key === 'ArrowLeft') to = (i - 1 + n) % n;
      else if (e.key === 'Home') to = 0;
      else if (e.key === 'End') to = n - 1;
      if (to > -1) { e.preventDefault(); selectTab(to, true); }
    });
    tablist.appendChild(tab);
    tabs.push(tab);
    panel.setAttribute('role', 'tabpanel');
    panel.setAttribute('aria-labelledby', tab.id);
  });
  root.insertBefore(tablist, panels[0]);

  function selectTab(i, focus) {
    selected = i;
    tabs.forEach(function (t, k) {
      var on = k === i;
      t.setAttribute('aria-selected', on ? 'true' : 'false');
      t.tabIndex = on ? 0 : -1;
      panels[k].hidden = !on;
    });
    if (focus) tabs[i].focus();
    // keep the chosen chip visible inside the horizontally scrollable tab row
    if (tabs[i].scrollIntoView && !desktop.matches) {
      var r = tablist.getBoundingClientRect(), t = tabs[i].getBoundingClientRect();
      if (t.left < r.left || t.right > r.right) {
        tablist.scrollLeft += (t.left + t.width / 2) - (r.left + r.width / 2);
      }
    }
  }

  /* ── Cards: single active card per category ─────────────── */
  panels.forEach(function (panel) {
    var cards = Array.prototype.slice.call(panel.querySelectorAll('.faqc-card'));
    panel._cards = cards;
    cards.forEach(function (card, idx) {
      card.querySelector('.faqc-btn').addEventListener('click', function () {
        var isActive = card.classList.contains('is-active');
        // desktop always keeps one card open; mobile lets the open one collapse
        setActive(panel, isActive && !desktop.matches ? -1 : idx);
      });
    });
  });

  function setActive(panel, idx) {
    panel._cards.forEach(function (card, k) {
      var on = k === idx;
      card.classList.toggle('is-active', on);
      card.querySelector('.faqc-btn').setAttribute('aria-expanded', on ? 'true' : 'false');
    });
  }

  function syncToViewport() {
    panels.forEach(function (panel) {
      var hasActive = panel._cards.some(function (c) { return c.classList.contains('is-active'); });
      if (desktop.matches && !hasActive) setActive(panel, 0);
    });
  }

  if (desktop.addEventListener) desktop.addEventListener('change', syncToViewport);
  else if (desktop.addListener) desktop.addListener(syncToViewport);

  panels.forEach(function (panel) { setActive(panel, desktop.matches ? 0 : -1); });
  selectTab(0, false);
})();
