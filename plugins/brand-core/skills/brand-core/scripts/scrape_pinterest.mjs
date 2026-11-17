#!/usr/bin/env node
// Scrape public Pinterest boards into one JSON manifest per board.
//
// Usage:
//   node scrape_pinterest.mjs <work>/data <boardUrl> [<boardUrl> ...]
//
// Why not scroll the page: logged out, Pinterest shows a signup wall after ~23 pins and the
// page height freezes. Instead this opens the board once (to get cookies and a page context),
// then pages BoardResource -> BoardFeedResource (+ BoardSectionsResource / BoardSectionPinsResource)
// with fetch() from inside the page.
//
// Output per board: <outDir>/<slug>.json with { url, slug, board{pin_count,...}, sections, count, pins[] }.
// Each pin: id, title, description, link, domain, dominant_color, created_at, section,
//   img{url,w,h} (original size), video{url,w,h,ms}|null, carousel[{url,w,h}], story_pages, story_blocks.
//
// Requirements: Node 18+, the `playwright` package resolvable from the current working directory
// (PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm i playwright) and Google Chrome installed: it launches
// the system Chrome (channel "chrome"), so no browser download is needed.
// Env: PW_CHANNEL=chrome (default) | msedge | "" (Playwright's own Chromium); PW_LOCALE=en-US; MAX_PAGES=40.
//
// Notes:
// - board.pin_count includes pins that no longer serve. Expect captured < pin_count and report the gap.
// - story_pin_data ("idea pins") are mostly single images. Only `video` (from videos.video_list or a
//   story block with a video) counts as video.
// - Board order changes between scrapes. Never reuse numbering from an older manifest.
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

async function loadPlaywright() {
  for (const base of [path.join(process.cwd(), 'noop.js'), import.meta.url]) {
    try { return createRequire(base)('playwright'); } catch { /* try next */ }
  }
  console.error('playwright not found. In your working directory run:\n  PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm i playwright\n(the script uses the system Chrome; set PW_CHANNEL="" to use Playwright\'s own Chromium instead)');
  process.exit(2);
}

const [outDir, ...boards] = process.argv.slice(2);
if (!outDir || !boards.length) {
  console.error('usage: node scrape_pinterest.mjs <outDir> <boardUrl> [<boardUrl> ...]');
  process.exit(1);
}
fs.mkdirSync(outDir, { recursive: true });
const MAX_PAGES = Number(process.env.MAX_PAGES || 40); // x25 pins per page

const pick = (p) => {
  const imgs = p.images || {};
  const orig = imgs.orig || imgs['736x'] || Object.values(imgs).at(-1) || {};
  const vl = p.videos?.video_list || {};
  const vid = vl.V_720P || vl.V_EXP7 || Object.values(vl).find((v) => v.url?.endsWith('.mp4')) || Object.values(vl)[0] || null;
  const pages = p.story_pin_data?.pages || [];
  const blocks = pages.flatMap((pg) => pg.blocks || []);
  const sv = blocks.find((b) => b.video)?.video?.video_list || null;
  const svs = sv ? sv.V_EXP7 || sv.V_720P || Object.values(sv).find((v) => v.url?.endsWith('.mp4')) || Object.values(sv)[0] : null;
  const v = vid || svs;
  const slots = p.carousel_data?.carousel_slots || [];
  return {
    id: p.id,
    title: (p.title || p.grid_title || '').trim(),
    description: (p.description || p.closeup_unified_description || '').trim(),
    link: p.link || null,
    domain: p.domain || null,
    dominant_color: p.dominant_color || null,
    created_at: p.created_at || null,
    img: { url: orig.url, w: orig.width, h: orig.height },
    video: v ? { url: v.url, w: v.width, h: v.height, ms: v.duration } : null,
    story_pages: pages.length,
    story_blocks: pages.map((pg) => (pg.blocks || []).map((b) => ({
      t: b.type || b.block_type,
      img: b.image?.images?.originals?.url || b.image?.images?.['736x']?.url || null,
      vid: !!b.video,
      text: b.text || null,
    }))),
    carousel: slots.map((c) => ({ url: c.images?.orig?.url || c.images?.['736x']?.url, w: c.images?.orig?.width, h: c.images?.orig?.height })),
  };
};

const { chromium } = await loadPlaywright();
const channel = process.env.PW_CHANNEL ?? 'chrome';
const browser = await chromium.launch({ ...(channel ? { channel } : {}), headless: true });
const ctx = await browser.newContext({
  viewport: { width: 1440, height: 1800 },
  locale: process.env.PW_LOCALE || 'en-US',
  userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
});

for (const url of boards) {
  const boardPath = new URL(url).pathname; // /<user>/<board-slug>/
  const parts = boardPath.split('/').filter(Boolean);
  if (parts.length < 2) { console.error('skip (not a board URL):', url); continue; }
  const slug = parts.at(-1);
  const page = await ctx.newPage();
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForTimeout(3000);

  const result = await page.evaluate(async ({ boardPath, maxPages }) => {
    const H = { 'X-Requested-With': 'XMLHttpRequest', Accept: 'application/json, text/javascript, */*, q=0.01', 'X-Pinterest-PWS-Handler': 'www/[username]/[slug].js' };
    const get = async (res, options) => {
      const q = new URLSearchParams({ source_url: boardPath, data: JSON.stringify({ options, context: {} }), _: Date.now() });
      const r = await fetch(`/resource/${res}/get/?${q}`, { headers: H, credentials: 'include' });
      return r.json();
    };
    const [username, slug] = boardPath.split('/').filter(Boolean);
    const b = await get('BoardResource', { username, slug, field_set_key: 'detailed' });
    const board = b?.resource_response?.data;
    if (!board?.id) return { error: 'BoardResource returned no board (private, renamed, or blocked?)' };
    const out = { board: { id: board.id, name: board.name, pin_count: board.pin_count, section_count: board.section_count, description: board.description }, pins: [], sections: [] };
    let bookmarks = null;
    for (let i = 0; i < maxPages; i++) {
      const opts = { board_id: board.id, board_url: boardPath, currentFilter: -1, field_set_key: 'react_grid_pin', filter_section_pins: false, sort: 'default', layout: 'default', page_size: 25, redux_normalize_feed: true };
      if (bookmarks) opts.bookmarks = bookmarks;
      const j = await get('BoardFeedResource', opts);
      const data = j?.resource_response?.data || [];
      out.pins.push(...data.filter((p) => p.type === 'pin'));
      const nb = j?.resource_response?.bookmark || j?.resource?.options?.bookmarks?.[0];
      if (!nb || nb === '-end-' || !data.length) break;
      bookmarks = [nb];
    }
    if (board.section_count) {
      const s = await get('BoardSectionsResource', { board_id: board.id, page_size: 25 });
      for (const sec of s?.resource_response?.data || []) {
        let bm = null; const pins = [];
        for (let i = 0; i < maxPages; i++) {
          const o = { section_id: sec.id, page_size: 25, redux_normalize_feed: true };
          if (bm) o.bookmarks = bm;
          const j = await get('BoardSectionPinsResource', o);
          const d = j?.resource_response?.data || [];
          pins.push(...d.filter((p) => p.type === 'pin'));
          const nb = j?.resource_response?.bookmark;
          if (!nb || nb === '-end-' || !d.length) break;
          bm = [nb];
        }
        out.sections.push({ id: sec.id, title: sec.title, pin_count: sec.pin_count, pins });
      }
    }
    return out;
  }, { boardPath, maxPages: MAX_PAGES });

  if (result.error) { console.error(slug, '|', result.error); await page.close(); continue; }
  const secOf = new Map();
  for (const s of result.sections) for (const p of s.pins) secOf.set(p.id, s.title);
  const all = new Map();
  for (const p of [...result.pins, ...result.sections.flatMap((s) => s.pins)]) all.set(p.id, p);
  const rows = [...all.values()].map((p, i) => ({ n: i + 1, ...pick(p), section: secOf.get(p.id) || p.board_section?.title || null }));
  const manifest = {
    url, slug, scraped_at: new Date().toISOString(), board: result.board,
    sections: result.sections.map((s) => ({ title: s.title, pin_count: s.pin_count })),
    count: rows.length, pins: rows,
  };
  fs.writeFileSync(path.join(outDir, `${slug}.json`), JSON.stringify(manifest, null, 2));
  const gap = (result.board.pin_count || 0) - rows.length;
  console.log([
    slug,
    `board pins: ${result.board.pin_count}`,
    `captured: ${rows.length}` + (gap > 0 ? ` (gap ${gap}: counted by Pinterest but not served)` : ''),
    `sections: ${result.sections.map((s) => `${s.title}(${s.pin_count})`).join(', ') || '-'}`,
    `video: ${rows.filter((r) => r.video).length}`,
    `carousel: ${rows.filter((r) => r.carousel.length).length}`,
    `idea pins: ${rows.filter((r) => r.story_pages).length} (not video unless counted above)`,
  ].join(' | '));
  await page.close();
}
await browser.close();
