#!/usr/bin/env node
// One verification pass over a built brand-core page, headless.
//
// Usage:
//   node check_page.mjs <page.html> <outDir>
//
// Checks, at desktop 1280 (light) and phone 390 (dark):
//   - console errors and page errors
//   - horizontal overflow (document scrollWidth vs viewport; elements past the right edge, ignoring
//     the intentionally scrollable .tablewrap, .track and the section nav)
//   - broken or placeholder images (naturalWidth 0, or the 1x1 placeholder build_page.py leaves)
//   - interactions: second filter chip hides other sources; lightbox opens, ArrowRight advances,
//     Escape closes; carousel "next" advances; contrast checker computes a ratio
// Writes screenshots of every section (desktop) and the first sections (phone) to <outDir>, and
// alt-*.jpg sheets showing every image next to its alt text: open them and check each alt against
// its picture before publishing (wrong alts survive every other check).
//
// The page may be a fragment (Artifact body) or a full document (--standalone build); fragments are
// wrapped like the Artifact host does. scroll-behavior is forced to auto: under smooth scrolling,
// screenshots taken right after scrollIntoView can come out blank.
//
// Requirements: Node 18+, `playwright` resolvable from the current working directory
// (PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm i playwright) and Google Chrome. PW_CHANNEL="" uses Playwright's Chromium.
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

async function loadPlaywright() {
  for (const base of [path.join(process.cwd(), 'noop.js'), import.meta.url]) {
    try { return createRequire(base)('playwright'); } catch { /* try next */ }
  }
  console.error('playwright not found. In your working directory run: PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm i playwright');
  process.exit(2);
}

const [file, outDir] = process.argv.slice(2);
if (!file || !outDir) { console.error('usage: node check_page.mjs <page.html> <outDir>'); process.exit(1); }
fs.mkdirSync(outDir, { recursive: true });
const src = fs.readFileSync(file, 'utf8');
const html = /^\s*<!doctype/i.test(src)
  ? src
  : '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"></head><body>' + src + '</body></html>';
const NO_SMOOTH = 'html{scroll-behavior:auto!important}';

const { chromium } = await loadPlaywright();
const channel = process.env.PW_CHANNEL ?? 'chrome';
const browser = await chromium.launch({ ...(channel ? { channel } : {}), headless: true });
let failures = 0;
let images = [];

for (const [name, vp, scheme] of [['desk', { width: 1280, height: 900 }, 'light'], ['phone', { width: 390, height: 844 }, 'dark']]) {
  const ctx = await browser.newContext({ viewport: vp, colorScheme: scheme });
  const page = await ctx.newPage();
  const errs = [];
  page.on('pageerror', (e) => errs.push('pageerror: ' + e.message));
  page.on('console', (m) => { if (m.type() === 'error') errs.push('console: ' + m.text().slice(0, 160)); });
  await page.setContent(html, { waitUntil: 'load', timeout: 60000 });
  await page.addStyleTag({ content: NO_SMOOTH });
  await page.waitForTimeout(800);

  const r = await page.evaluate(() => {
    const over = [...document.querySelectorAll('body *')]
      .filter((e) => { const b = e.getBoundingClientRect(); return b.width && b.right > innerWidth + 1 && !e.closest('.tablewrap, .track, .stopbar nav, [hidden]'); })
      .slice(0, 6).map((e) => `${e.tagName.toLowerCase()}.${e.className} in #${(e.closest('section') || {}).id || '-'}`);
    const imgs = [...document.querySelectorAll('img')].filter((i) => i.id !== 'lb-img');
    const broken = imgs.filter((i) => i.src && (i.naturalWidth === 0 || (i.naturalWidth === 1 && i.naturalHeight === 1))).length;
    return {
      scrollWidth: document.documentElement.scrollWidth, viewport: innerWidth, overflow: over,
      images: imgs.length, broken, posts: document.querySelectorAll('.post').length, pairs: document.querySelectorAll('.pair').length,
      swatches: document.querySelectorAll('.sw').length, ramps: document.querySelectorAll('.ramp').length,
      decisions: document.querySelectorAll('#decisions-list .d').length, chips: document.querySelectorAll('.chipbtn').length,
      dstatus: (document.querySelector('#dstatus') || {}).textContent || '',
    };
  });

  const it = {};
  const chips = page.locator('.chipbtn');
  if (await chips.count() > 1) {
    await chips.nth(1).click();
    it.filter = await page.evaluate(() => {
      const figs = [...document.querySelectorAll('#formats .ref[data-src]')];
      const f = document.querySelector('.chipbtn[aria-pressed="true"]').dataset.f;
      return { chip: f, visible: figs.filter((x) => !x.hidden).length, wrongVisible: figs.filter((x) => !x.hidden && x.dataset.src !== f).length };
    });
    if (it.filter.wrongVisible) failures++;
    await chips.nth(0).click();
  }
  const ph = page.locator('button.ph:has(img)');
  if (await ph.count()) {
    await ph.first().scrollIntoViewIfNeeded();
    await ph.first().click();
    const a = await page.evaluate(() => ({ open: !document.querySelector('#lb').hidden, count: document.querySelector('#lb-count').textContent }));
    await page.keyboard.press('ArrowRight');
    const b = await page.evaluate(() => document.querySelector('#lb-count').textContent);
    await page.keyboard.press('Escape');
    const closed = await page.evaluate(() => document.querySelector('#lb').hidden);
    it.lightbox = { ...a, afterArrow: b, closed };
    if (!a.open || !closed) failures++;
  }
  const next = page.locator('.post [data-dir="1"]');
  if (await next.count()) {
    await next.first().scrollIntoViewIfNeeded();
    await next.first().click();
    await page.waitForTimeout(700);
    it.carousel = await page.evaluate(() => document.querySelector('.post .count').textContent);
  }
  if (await page.locator('#cc-fg option').count() > 1) {
    const vals = await page.$$eval('#cc-fg option', (os) => os.map((o) => o.value));
    await page.selectOption('#cc-fg', vals[0]);
    await page.selectOption('#cc-bg', vals[vals.length - 1]);
    it.contrast = await page.evaluate(() => `${document.querySelector('#cc-fg').value} on ${document.querySelector('#cc-bg').value}: ${document.querySelector('#cc-ratio').textContent}`);
  }

  if (errs.length || r.overflow.length || r.scrollWidth > r.viewport || r.broken) failures++;
  console.log(name, JSON.stringify({ ...r, interactions: it, errors: errs }, null, 1));

  const ids = await page.$$eval('.stopbar nav a', (as) => as.map((a) => a.getAttribute('href').slice(1)).filter((id) => document.getElementById(id)));
  for (const id of name === 'desk' ? ids : ids.slice(0, 2)) {
    await page.evaluate((i) => document.getElementById(i).scrollIntoView(), id);
    await page.waitForTimeout(300);
    await page.screenshot({ path: path.join(outDir, `${name}-${id}.jpg`), type: 'jpeg', quality: 55 });
  }
  if (name === 'desk') {
    images = await page.$$eval('img', (is) => is.filter((i) => i.id !== 'lb-img' && i.src).map((i) => ({
      src: i.src, alt: i.alt,
      where: (() => { const fc = i.closest('figure')?.querySelector('figcaption'); if (!fc) return ''; const parts = fc.children.length ? [...fc.children].map((c) => c.textContent.trim()) : [fc.textContent.trim()]; return parts.filter(Boolean).join(' · ').slice(0, 80); })(),
    })));
  }
  await ctx.close();
}

// alt-text sheets: 24 images per sheet, alt text under each
const esc = (s) => s.replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const ctx = await browser.newContext({ viewport: { width: 1200, height: 800 } });
const page = await ctx.newPage();
for (let s = 0; s < images.length; s += 24) {
  const chunk = images.slice(s, s + 24);
  await page.setContent(`<!doctype html><style>body{margin:0;font:12px system-ui;background:#fff;color:#111}.g{display:grid;grid-template-columns:repeat(6,1fr);gap:10px;padding:10px}
    figure{margin:0;display:grid;gap:4px;align-content:start}img{width:100%;height:170px;object-fit:contain;background:#eee}b{font:11px ui-monospace,monospace;color:#666}</style>
    <div class="g">${chunk.map((im, i) => `<figure><img src="${im.src}"><b>${s + i + 1}${im.where ? ' · ' + esc(im.where) : ''}</b><span>${esc(im.alt || '(no alt)')}</span></figure>`).join('')}</div>`, { waitUntil: 'load' });
  await page.screenshot({ path: path.join(outDir, `alt-${s / 24 + 1}.jpg`), type: 'jpeg', quality: 60, fullPage: true });
}
await ctx.close();
await browser.close();
console.log(`${images.length} images -> ${Math.ceil(images.length / 24)} alt sheet(s) in ${outDir}. Open them and check each alt against its image.`);
console.log(failures ? `FAIL: ${failures} problem(s) above` : 'PASS: no console errors, no horizontal overflow, interactions work');
process.exit(failures ? 1 : 0);
