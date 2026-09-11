#!/usr/bin/env node
/**
 * Free Mind Consultancy — pre-deployment site validation.
 *
 * Zero dependencies (Node built-ins only: fs, path). Covers the
 * repo-wide/cross-file checks that scripts/optimizer/validation_engine.py
 * (in marketing_department/seo_agent) does NOT cover — that tool validates
 * one HTML file's structure/schema/accessibility at a time; this script
 * checks things that only make sense across the whole site: broken internal
 * links, broken local assets, sitemap well-formedness, robots.txt presence,
 * credential-shaped strings, JSON-LD parse errors, and GA4 install
 * consistency.
 *
 * Run before every meaningful deployment:
 *   node scripts/validate-site.js
 *
 * Exit code 0 = safe to deploy. Exit code 1 = a check failed, read the
 * output above the FAIL line before pushing.
 */

const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
process.chdir(ROOT);

let failures = 0;
function ok(label, detail) { console.log(`  [OK]   ${label}${detail ? ' — ' + detail : ''}`); }
function fail(label, detail) { console.log(`  [FAIL] ${label}${detail ? ' — ' + detail : ''}`); failures++; }

function walk(dir, out) {
  for (const f of fs.readdirSync(dir)) {
    if (f.startsWith('.') || f === 'node_modules' || f === 'scripts') continue;
    const p = path.join(dir, f);
    const st = fs.statSync(p);
    if (st.isDirectory()) walk(p, out);
    else out.push(p);
  }
}

const allFiles = [];
walk('.', allFiles);
const htmlFiles = allFiles.filter(f => f.endsWith('.html'));
const allRel = new Set(allFiles.map(f => '/' + f.replace(/^\.[\\/]/, '').replace(/\\/g, '/')));

console.log(`\nFree Mind Consultancy — site validation (${htmlFiles.length} HTML files)\n`);

// 1. HTML structure + JSON-LD parsing
let tagErrors = 0, jsonLdErrors = 0;
for (const f of htmlFiles) {
  const html = fs.readFileSync(f, 'utf8');
  for (const t of ['html', 'head', 'body']) {
    const open = (html.match(new RegExp('<' + t + '[ >]', 'g')) || []).length;
    const close = (html.match(new RegExp('</' + t + '>', 'g')) || []).length;
    if (open === 0 || open !== close) { console.log(`    ${f}: <${t}> open=${open} close=${close}`); tagErrors++; }
  }
  const ldRe = /<script type="application\/ld\+json">([\s\S]*?)<\/script>/g;
  let m;
  while ((m = ldRe.exec(html))) {
    try { JSON.parse(m[1]); } catch (e) { console.log(`    ${f}: JSON-LD error — ${e.message}`); jsonLdErrors++; }
  }
}
if (tagErrors === 0) ok('HTML tag structure', `${htmlFiles.length} files`); else fail('HTML tag structure', `${tagErrors} problems`);
if (jsonLdErrors === 0) ok('JSON-LD parsing', `${htmlFiles.length} files`); else fail('JSON-LD parsing', `${jsonLdErrors} errors`);

// 2. Internal links + local assets
function stripScripts(html) { return html.replace(/<script[\s\S]*?<\/script>/g, ''); }
function pageExists(cleanUrl) {
  let p = cleanUrl.replace(/\/+$/, '') || '/';
  if (p === '/') return allRel.has('/index.html');
  if (allRel.has(p)) return true;
  if (allRel.has(p + '.html')) return true;
  if (allRel.has(p + '/index.html')) return true;
  return false;
}
let brokenAssets = [], brokenLinks = [];
for (const f of htmlFiles) {
  const html = stripScripts(fs.readFileSync(f, 'utf8'));
  const dir = path.dirname(f);
  let m;
  const assetRe = /(?:src|href)="([^"]+)"/g;
  while ((m = assetRe.exec(html))) {
    let ref = m[1];
    if (/^https?:|^mailto:|^tel:|^#|^javascript:|^data:|^\/_vercel\//.test(ref)) continue;
    const clean = ref.split('#')[0].split('?')[0];
    if (!clean || clean === '/') continue;
    let resolved = clean.startsWith('/') ? '.' + clean : path.join(dir, clean);
    resolved = resolved.replace(/\\/g, '/');
    if (/\.(css|js|png|jpg|jpeg|svg|gif|webp|ico|pdf|xml|txt|json|woff2?)$/i.test(resolved) && !fs.existsSync(resolved)) {
      brokenAssets.push(`${f} -> ${ref}`);
    }
  }
  const aRe = /<a\b[^>]*href="([^"]+)"/g;
  while ((m = aRe.exec(html))) {
    let href = m[1];
    if (/^https?:|^mailto:|^tel:|^#|^javascript:/.test(href)) continue;
    if (/\.(css|js|png|jpg|jpeg|svg|gif|webp|ico|pdf|xml|txt|json|woff2?)$/i.test(href)) continue;
    const clean = href.split('#')[0].split('?')[0];
    if (!clean) continue;
    const target = clean.startsWith('/') ? clean : path.posix.normalize('/' + dir.replace(/\\/g, '/') + '/' + clean);
    if (!pageExists(target)) brokenLinks.push(`${f} -> ${href} (resolved: ${target})`);
  }
}
if (brokenAssets.length === 0) ok('Local asset references'); else { fail('Local asset references', `${brokenAssets.length} broken`); brokenAssets.forEach(x => console.log('    ' + x)); }
if (brokenLinks.length === 0) ok('Internal page links'); else { fail('Internal page links', `${brokenLinks.length} broken`); brokenLinks.forEach(x => console.log('    ' + x)); }

// 3. Alt text
let missingAlt = 0;
for (const f of htmlFiles) {
  const imgs = fs.readFileSync(f, 'utf8').match(/<img\b[^>]*>/g) || [];
  missingAlt += imgs.filter(i => !/\balt=/.test(i)).length;
}
if (missingAlt === 0) ok('Image alt attributes'); else fail('Image alt attributes', `${missingAlt} missing`);

// 4. sitemap.xml
if (fs.existsSync('sitemap.xml')) {
  const xml = fs.readFileSync('sitemap.xml', 'utf8');
  const opens = (xml.match(/<url>/g) || []).length;
  const closes = (xml.match(/<\/url>/g) || []).length;
  const locs = (xml.match(/<loc>/g) || []).length;
  if (opens === closes && opens === locs && opens > 0) ok('sitemap.xml', `${opens} URLs, well-formed`);
  else fail('sitemap.xml', `url tags: ${opens}/${closes}, loc: ${locs}`);
} else fail('sitemap.xml', 'missing');

// 5. robots.txt
if (fs.existsSync('robots.txt')) {
  const robots = fs.readFileSync('robots.txt', 'utf8');
  if (/Sitemap:/i.test(robots) && /User-agent:\s*\*/i.test(robots)) ok('robots.txt', 'present, has sitemap directive');
  else fail('robots.txt', 'missing sitemap directive or wildcard user-agent');
} else fail('robots.txt', 'missing');

// 6. llms.txt
if (fs.existsSync('llms.txt')) ok('llms.txt', 'present');
else fail('llms.txt', 'missing');

// 7. Security headers (vercel.json)
if (fs.existsSync('vercel.json')) {
  const vc = JSON.parse(fs.readFileSync('vercel.json', 'utf8'));
  const required = ['X-Content-Type-Options', 'X-Frame-Options', 'Referrer-Policy', 'Permissions-Policy', 'Strict-Transport-Security'];
  const present = (vc.headers?.[0]?.headers || []).map(h => h.key);
  const missing = required.filter(h => !present.includes(h));
  if (missing.length === 0) ok('vercel.json security headers', `${required.length}/${required.length} present`);
  else fail('vercel.json security headers', `missing: ${missing.join(', ')}`);
} else fail('vercel.json', 'missing');

// 8. Credential-shaped strings
const secretPattern = /AIza[0-9A-Za-z_-]{20,}|sk-[a-zA-Z0-9]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----/;
let secretHits = [];
for (const f of allFiles) {
  if (!/\.(html|js|json|txt)$/i.test(f)) continue;
  const content = fs.readFileSync(f, 'utf8');
  if (secretPattern.test(content)) secretHits.push(f);
}
if (secretHits.length === 0) ok('Credential-shaped strings', 'none found');
else fail('Credential-shaped strings', secretHits.join(', '));

// 9. GA4 install consistency
const ids = new Set();
let dupeInstalls = [];
for (const f of htmlFiles) {
  const html = fs.readFileSync(f, 'utf8');
  (html.match(/G-[A-Z0-9]{6,12}/g) || []).forEach(id => ids.add(id));
  const configCount = (html.match(/gtag\('config'/g) || []).length;
  if (configCount > 1) dupeInstalls.push(f);
}
if (ids.size <= 1 && dupeInstalls.length === 0) ok('GA4 install consistency', `1 measurement ID, 0 duplicate installs`);
else fail('GA4 install consistency', `IDs found: ${[...ids].join(',')}, duplicate installs: ${dupeInstalls.join(',')}`);

console.log(`\n${failures === 0 ? 'ALL CHECKS PASSED — safe to deploy.' : failures + ' CHECK(S) FAILED — review before deploying.'}\n`);
process.exit(failures === 0 ? 0 : 1);
