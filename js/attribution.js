/* ============================================================
   FREE MIND CONSULTANCY — attribution.js
   Captures UTM + click-ID marketing attribution on landing,
   persists first-touch and last-touch, and exposes it for
   form.js to attach to lead submissions. No cookies, no
   third-party calls, no CRM — localStorage only.
   ============================================================ */

(function () {
  'use strict';

  var STORAGE_KEY_FIRST = 'fm_attribution_first_touch';
  var STORAGE_KEY_LAST = 'fm_attribution_last_touch';
  var PARAMS = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term', 'gclid', 'fbclid'];

  function readCurrentTouch() {
    var search = new URLSearchParams(window.location.search);
    var hasAnyParam = PARAMS.some(function (p) { return search.has(p); });
    if (!hasAnyParam) return null;

    var touch = {};
    PARAMS.forEach(function (p) {
      if (search.has(p)) touch[p] = search.get(p);
    });
    touch.landing_page = window.location.pathname;
    touch.referrer = document.referrer || '';
    touch.timestamp = new Date().toISOString();
    return touch;
  }

  function safeGet(key) {
    try {
      var raw = window.localStorage.getItem(key);
      return raw ? JSON.parse(raw) : null;
    } catch (_) {
      return null;
    }
  }

  function safeSet(key, value) {
    try {
      window.localStorage.setItem(key, JSON.stringify(value));
    } catch (_) {
      /* localStorage unavailable (private mode, blocked storage) — attribution simply won't persist */
    }
  }

  var currentTouch = readCurrentTouch();

  if (currentTouch) {
    // First-touch: only set once, never overwritten.
    if (!safeGet(STORAGE_KEY_FIRST)) {
      safeSet(STORAGE_KEY_FIRST, currentTouch);
    }
    // Last-touch: always overwritten by the most recent campaign visit.
    safeSet(STORAGE_KEY_LAST, currentTouch);
  }

  // Exposed for form.js — read at submit time, not import time.
  window.FreeMindAttribution = {
    getFirstTouch: function () { return safeGet(STORAGE_KEY_FIRST); },
    getLastTouch: function () { return safeGet(STORAGE_KEY_LAST); }
  };
})();
