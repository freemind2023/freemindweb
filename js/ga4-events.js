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
  });
})();
