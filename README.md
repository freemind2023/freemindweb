# Free Mind Consultancy — Website

**Tagline:** Consulting for Change  
**Tech Stack:** Plain HTML5, CSS3, Vanilla JavaScript — no frameworks, no build tools.  
**Deployable to:** Netlify, Vercel, or any static host.

---

## 1. Project Overview

This is the complete production-ready website for Free Mind Consultancy. It includes:
- A fully animated homepage with hero typewriter effect, neural network particles, scroll reveals, and count-up stats
- 30 services organized across 5 tabbed categories
- A contact form powered by EmailJS (requires API key setup — see below)
- Dark mode with localStorage persistence
- SEO-optimized with JSON-LD structured data, Open Graph, and Twitter Card tags
- Privacy Policy, Terms of Service, and Disclaimer pages
- robots.txt and sitemap.xml

---

## 2. File Structure

```
freemind-website/
  index.html          — Main homepage (all sections)
  privacy.html        — Privacy Policy page
  terms.html          — Terms of Service page
  disclaimer.html     — Disclaimer page
  robots.txt          — Search engine crawl instructions
  sitemap.xml         — XML sitemap for search indexing
  README.md           — This file

  images/
    logo.png          — Brand logo (replace with your actual logo)
    og-image.jpg      — Open Graph social share image (replace with 1200x630px image)
    spotify.png       — Spotify podcast badge
    amazon-music.png  — Amazon Music podcast badge

  css/
    style.css         — All layout, typography, and component styles
    animations.css    — Keyframes and animation trigger classes
    darkmode.css      — Dark mode color overrides via [data-theme="dark"]

  js/
    main.js           — Navigation, dark mode, typewriter, scroll reveal, FAQ, tabs, count-up
    particles.js      — Neural network canvas animation for hero section
    form.js           — EmailJS contact form logic with dynamic service dropdown
```

---

## 3. How to Set Up EmailJS (Step by Step)

**Step 1:** Go to [https://emailjs.com](https://emailjs.com) and create a free account.

**Step 2:** Add a new Email Service and connect your Gmail or email provider.  
Go to: Email Services → Add New Service → Select Gmail (or other) → Authenticate.

**Step 3:** Create a new Email Template.  
Go to: Email Templates → Create New Template.  
- Set the subject line to: `New Inquiry - {{category}} - {{from_name}}`
- Set the To field to: `{{to_email_1}}, {{to_email_2}}`
- In the body, include all these variables:
  - `{{from_name}}` — Client's full name
  - `{{from_email}}` — Client's email
  - `{{from_phone}}` — Client's phone
  - `{{category}}` — Professional category
  - `{{service_interest}}` — Service selected
  - `{{message}}` — Client's message
  - `{{referral_source}}` — How they heard about you

**Step 4:** Copy your credentials:
- Public Key → Account → General
- Service ID → Email Services → your service ID
- Template ID → Email Templates → your template ID

**Step 5:** Open `js/form.js` and replace these three values:
```javascript
const EMAILJS_PUBLIC_KEY = "YOUR_ACTUAL_PUBLIC_KEY";
const EMAILJS_SERVICE_ID = "YOUR_ACTUAL_SERVICE_ID";
const EMAILJS_TEMPLATE_ID = "YOUR_ACTUAL_TEMPLATE_ID";
```

**Step 6:** Test by submitting the contact form on your live site.

**Note on file attachments:** EmailJS free plan does not support file attachments.  
The file input field is visible in the form for UX purposes only.  
To enable actual file sending, upgrade to EmailJS paid plan or implement a backend endpoint.

---

## 4. How to Add Your Logo

1. Replace `images/logo.png` with your actual logo file.
2. Keep the filename `logo.png` exactly.
3. Recommended: 200px wide, transparent or white background, black logo mark.
4. The footer automatically inverts the logo to white using CSS `filter: brightness(0) invert(1)`.
5. If your logo is already white, remove that CSS rule from `style.css` (`.footer-logo img`).

---

## 5. How to Replace the Open Graph Image

1. Create a 1200x630px branded image (your logo + tagline on white or black background).
2. Save it as `images/og-image.jpg`.
3. This image appears when your URL is shared on social media (LinkedIn, Twitter, WhatsApp, etc.).

---

## 6. How to Update Social Media Links

Search for `REPLACE:` comments in `index.html` — these mark every placeholder link.

The links already set from your briefing:
- Instagram: `https://www.instagram.com/freemind_consultancy/`
- Twitter/X: `https://x.com/free_mind_2023`
- Threads: `https://www.threads.net/@freemind_consultancy`
- Facebook: `https://www.facebook.com/home.php`
- WhatsApp: `https://wa.me/918208316509`

Update LinkedIn, Reddit, Quora, and Pinterest to your specific profile page URLs.

---

## 7. How to Update the Domain URL

Search for `freemindconsultancy.com` across all HTML files and `sitemap.xml`.  
Replace with your actual domain once confirmed (e.g., `www.freemindconsultancy.in` or similar).

---

## 8. How to Deploy to Netlify (Step by Step)

**Step 1:** Go to [https://netlify.com](https://netlify.com) and create a free account.

**Step 2:** From the Netlify dashboard, click "Add new site" → "Deploy manually".

**Step 3:** Drag and drop the entire `freemind-website/` folder onto the upload area.

**Step 4:** Your site is live. Netlify provides a free URL like `random-name.netlify.app`.

**Step 5:** To add a custom domain:  
Go to Site Settings → Domain Management → Add custom domain.  
Follow DNS instructions to point your domain registrar to Netlify's nameservers.

**Step 6:** Netlify automatically provisions a free SSL certificate (HTTPS).

---

## 9. How to Update Content

All text content is in the HTML files. Edit directly in any text editor.

**To change a color sitewide:**  
Open `css/style.css` and edit the CSS custom property at the top of the file.  
Example: change `--color-bg: #FAFAFA` to change the page background everywhere.

**To change dark mode colors:**  
Edit `css/darkmode.css` — these are the overrides applied when dark mode is active.

**To add or remove FAQ items:**  
Copy one `<div class="faq-item">` block in `index.html` and edit the question/answer text.

**To add or remove services:**  
Each tab panel contains 6 service cards. Copy a `<article class="service-card">` block and edit.

---

## 10. Podcast Links

Already configured:
- Spotify: `https://open.spotify.com/show/0R3UF2riquLqRFIRboth2Z`
- Amazon Music: `https://music.amazon.in/podcasts/df2aad0e-a278-4f16-9ff3-c77d8c4daedc/free-talk`

These appear in the Contact section's left column.

---

## 11. Contact for Technical Support

Email: [info@freemindconsult.com](mailto:info@freemindconsult.com)  
Website: [www.freemindconsultancy.com](https://www.freemindconsultancy.com)
