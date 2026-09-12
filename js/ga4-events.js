(function () {
  'use strict';
  if (typeof gtag !== 'function') return;

  document.addEventListener('click', function (e) {
    var link = e.target.closest('a[href]');
    if (!link) return;
    var href = link.getAttribute('href') || '';

    if (href.indexOf('wa.me') !== -1) {
      gtag('event', 'contact', {
        event_category: 'WhatsApp',
        event_label: window.location.pathname,
        method: 'whatsapp'
      });
      if (typeof fbq === 'function') fbq('track', 'Contact', { method: 'whatsapp' });
    }

    if (href.indexOf('tel:') === 0) {
      gtag('event', 'contact', {
        event_category: 'Phone Call',
        event_label: href.replace('tel:', ''),
        method: 'phone'
      });
      if (typeof fbq === 'function') fbq('track', 'Contact', { method: 'phone' });
    }

    if (href.indexOf('mailto:') === 0) {
      gtag('event', 'contact', {
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
      gtag('event', 'service_cta_click', {
        event_category: 'CTA',
        cta_text: (link.textContent || '').trim(),
        placement: placement,
        page_path: window.location.pathname
      });
    }
  });
})();
