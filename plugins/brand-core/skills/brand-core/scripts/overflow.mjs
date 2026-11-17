#!/usr/bin/env node
// Which elements stick out past the right edge at phone width (the cause of horizontal scroll).
//
// Usage:
//   node overflow.mjs <page.html> [width=390]
//
// Prints up to 8 offenders: tag, class, width, right edge, section id, start of their text.
// Ignores the intentionally scrollable .tablewrap, .track and section nav. Fix the first one and rerun:
// one wide child usually pushes its parents out too. Usual fixes: min-width: 0 on grid/flex children,
// minmax(0, 1fr) columns, overflow-wrap: anywhere on long words or hexes.
//
// Requirements: as check_page.mjs (playwright resolvable from the cwd, Google Chrome or PW_CHANNEL="").
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

const [file, w = '390'] = process.argv.slice(2);
if (!file) { console.error('usage: node overflow.mjs <page.html> [width]'); process.exit(1); }
const src = fs.readFileSync(file, 'utf8');
const html = /^\s*<!doctype/i.test(src)
  ? src
  : '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>' + src + '</body></html>';
const { chromium } = await loadPlaywright();
const channel = process.env.PW_CHANNEL ?? 'chrome';
const b = await chromium.launch({ ...(channel ? { channel } : {}), headless: true });
const p = await (await b.newContext({ viewport: { width: Number(w), height: 844 } })).newPage();
await p.setContent(html, { waitUntil: 'load', timeout: 60000 });
const out = await p.evaluate(() => ({
  scrollWidth: document.documentElement.scrollWidth,
  viewport: innerWidth,
  offenders: [...document.querySelectorAll('body *')]
    .filter((e) => { const r = e.getBoundingClientRect(); return r.width && r.right > innerWidth + 1 && !e.closest('.tablewrap, .track, .stopbar nav, [hidden]'); })
    .slice(0, 8)
    .map((e) => ({ tag: e.tagName.toLowerCase(), cls: String(e.className), w: Math.round(e.getBoundingClientRect().width), right: Math.round(e.getBoundingClientRect().right), section: (e.closest('section') || {}).id || null, text: (e.textContent || '').trim().slice(0, 50) })),
}));
console.log(JSON.stringify(out, null, 1));
await b.close();
process.exit(out.offenders.length || out.scrollWidth > out.viewport ? 1 : 0);
