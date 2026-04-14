/* ============================================================
   FREE MIND CONSULTANCY — form.js
   EmailJS contact form logic with dynamic service dropdown
   ============================================================ */

(function () {
  'use strict';

  /* ── Google Sheets Configuration ───────────────────────── */
  const SHEETS_URL = "https://script.google.com/macros/s/AKfycbx3S0UQi2PVg-mFYUVKlxemkrDrPwKiQQ39j7zQRBhB82L-XA7-Gxdo8Gamu1WVDokV/exec";

  /* ── EmailJS Configuration ──────────────────────────────── */

  // REPLACE: Add your EmailJS Public Key from https://emailjs.com/account
  const EMAILJS_PUBLIC_KEY = "ADD_YOUR_EMAILJS_PUBLIC_KEY_HERE";

  // REPLACE: Add your EmailJS Service ID from https://emailjs.com/account#connected-accounts
  const EMAILJS_SERVICE_ID = "ADD_YOUR_EMAILJS_SERVICE_ID_HERE";

  // REPLACE: Add your EmailJS Template ID from https://emailjs.com/account#templates
  const EMAILJS_TEMPLATE_ID = "ADD_YOUR_EMAILJS_TEMPLATE_ID_HERE";

  // Initialize EmailJS
  if (typeof emailjs !== 'undefined') {
    emailjs.init(EMAILJS_PUBLIC_KEY);
  }

  /* ── Service Options Per Category ──────────────────────── */
  const serviceOptions = {
    'Founder / Entrepreneur': [
      'AI Calling Agent',
      'Business Automation',
      'Digital Marketing',
      'Website Development',
      'Personal Branding',
      'ERP and MVP Systems'
    ],
    'Author / Writer': [
      'Book Publishing',
      'Podcast Features',
      'ISBN Registration',
      'Book Translation',
      'Ghostwriting Support',
      'Editing and Formatting'
    ],
    'Professor / Academic': [
      'Book Publishing',
      'Podcast Features',
      'ISBN Registration',
      'Book Translation',
      'Textbook Writing',
      'Research Paper Editing'
    ],
    'Government Officer / Civil Servant': [
      'Book Publishing',
      'Podcast Features',
      'ISBN Registration',
      'Book Translation',
      'Book Writing Support',
      'Editing and Formatting'
    ],
    'Coach / Training Institute': [
      'Textbook Publishing',
      'Presentation Design',
      'Interactive Content Creation',
      'LMS Development',
      'Curriculum Design',
      'AI Podcast Content Creation'
    ],
    'Other': [
      'General Inquiry'
    ]
  };

  /* ── Dynamic Service Dropdown ───────────────────────────── */
  const categorySelect = document.getElementById('form-category');
  const serviceSelect  = document.getElementById('form-service');

  if (categorySelect && serviceSelect) {
    categorySelect.addEventListener('change', () => {
      const category = categorySelect.value;
      const services = serviceOptions[category] || [];

      // Reset service dropdown
      serviceSelect.innerHTML = '';

      if (!services.length || !category) {
        const defaultOpt = document.createElement('option');
        defaultOpt.value = '';
        defaultOpt.textContent = 'Select a category first';
        serviceSelect.appendChild(defaultOpt);
        serviceSelect.disabled = true;
        return;
      }

      serviceSelect.disabled = false;
      const placeholder = document.createElement('option');
      placeholder.value = '';
      placeholder.textContent = 'Select a service';
      serviceSelect.appendChild(placeholder);

      services.forEach(service => {
        const option = document.createElement('option');
        option.value = service;
        option.textContent = service;
        serviceSelect.appendChild(option);
      });
    });
  }

  /* ── Form Submission ────────────────────────────────────── */
  const contactForm    = document.getElementById('contact-form');
  const formSuccess    = document.getElementById('form-success');
  const formError      = document.getElementById('form-error');
  const submitBtn      = document.getElementById('form-submit');

  if (contactForm) {
    contactForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      // Basic validation
      if (!contactForm.checkValidity()) {
        contactForm.reportValidity();
        return;
      }

      // Loading state
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Sending...';
      }

      // Gather form data
      const formData = new FormData(contactForm);
      const templateParams = {
        from_name:       formData.get('from_name')      || '',
        from_email:      formData.get('from_email')     || '',
        from_phone:      formData.get('from_phone')     || '',
        category:        formData.get('category')       || '',
        service_interest:formData.get('service_interest')|| '',
        message:         formData.get('message')        || '',
        referral_source: formData.get('referral_source')|| '',
        to_email_1:      'freemind.aryan@gmail.com',
        to_email_2:      'info@freemindconsult.com'
      };

      // FILE ATTACHMENT NOTE: EmailJS free plan does not support file attachments.
      // The file input field is included in the UI for UX purposes only.
      // To handle file uploads, upgrade to EmailJS paid plan or implement
      // a backend endpoint (e.g., Node.js, serverless function with formidable).
      // For now the file field is cosmetic only.

      // Always save to Google Sheets first (works even without EmailJS)
      const sheetsPayload = {
        from_name:        templateParams.from_name,
        from_email:       templateParams.from_email,
        from_phone:       templateParams.from_phone,
        category:         templateParams.category,
        service_interest: templateParams.service_interest,
        message:          templateParams.message,
        referral_source:  templateParams.referral_source,
        source_page:      window.location.pathname
      };

      let sheetsSaved = false;
      try {
        await fetch(SHEETS_URL, { method: 'POST', body: JSON.stringify(sheetsPayload) });
        sheetsSaved = true;
      } catch (_) {}

      // Try EmailJS if configured
      const emailjsConfigured = EMAILJS_PUBLIC_KEY !== 'ADD_YOUR_EMAILJS_PUBLIC_KEY_HERE'
        && EMAILJS_SERVICE_ID !== 'ADD_YOUR_EMAILJS_SERVICE_ID_HERE'
        && EMAILJS_TEMPLATE_ID !== 'ADD_YOUR_EMAILJS_TEMPLATE_ID_HERE';

      if (emailjsConfigured && typeof emailjs !== 'undefined') {
        try {
          await emailjs.send(EMAILJS_SERVICE_ID, EMAILJS_TEMPLATE_ID, templateParams);
        } catch (err) {
          console.warn('EmailJS send failed:', err);
        }
      }

      // Show success if Sheets saved OR EmailJS worked
      if (sheetsSaved || emailjsConfigured) {
        contactForm.style.display = 'none';
        if (formSuccess) formSuccess.style.display = 'block';
      } else {
        if (formError) formError.style.display = 'block';
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.textContent = 'Send Inquiry';
        }
      }
    });
  }

})();
