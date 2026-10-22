(function () {
  'use strict';

  // Fires the browser pixel event and the matching server-side CAPI call
  // with the same eventId, so Meta can dedup the two.
  function trackContact(method) {
    var eventId = (window.crypto && window.crypto.randomUUID) ? window.crypto.randomUUID() : 'fm-' + Date.now() + '-' + Math.random().toString(36).slice(2, 8);
    if (typeof fbq === 'function') fbq('track', 'Contact', { method: method }, { eventID: eventId });
    fetch('/api/capi-event', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ eventName: 'Contact', eventId: eventId, eventSourceUrl: window.location.href })
    }).catch(function () {});
  }

  document.addEventListener('click', function (e) {
    var link = e.target.closest('a[href]');
    if (!link) return;
    var href = link.getAttribute('href') || '';

    if (href.indexOf('wa.me') !== -1) {
      if (typeof gtag === 'function') gtag('event', 'contact', {
        event_category: 'WhatsApp',
        event_label: window.location.pathname,
        method: 'whatsapp'
      });
      trackContact('whatsapp');
    }

    if (href.indexOf('tel:') === 0) {
      if (typeof gtag === 'function') gtag('event', 'contact', {
        event_category: 'Phone Call',
        event_label: href.replace('tel:', ''),
        method: 'phone'
      });
      trackContact('phone');
    }

    if (href.indexOf('mailto:') === 0) {
      if (typeof gtag === 'function') gtag('event', 'contact', {
        event_category: 'Email',
        event_label: href.replace('mailto:', ''),
        method: 'email'
      });
    }

    // "Book Free Consultation" style CTAs that route to the homepage contact
    // form — a click here is intent, not yet a lead (generate_lead already
    // fires separately on actual form submission in js/form.js).
    if (link.classList.contains('btn-primary') && href.indexOf('#contact') !== -1) {
      var placement = link.closest('header') ? 'nav' : (link.closest('section[id]') || {}).id || 'body';
      if (typeof gtag === 'function') gtag('event', 'service_cta_click', {
        event_category: 'CTA',
        cta_text: (link.textContent || '').trim(),
        placement: placement,
        page_path: window.location.pathname
      });
      trackContact('consultation_cta');
    }
  });
})();
