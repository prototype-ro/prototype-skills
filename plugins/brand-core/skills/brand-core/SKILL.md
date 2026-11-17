---
name: brand-core
description: Use when someone wants to define, consolidate or audit a brand's visual identity from material they already have (Pinterest boards or folders of reference images, posts and carousels already published, an existing brand guideline sheet, brand docs), or wants to know which reference serves which content format before designing templates. Triggers on "brand core", "brand identity from my boards", "turn my moodboards into a brand", "what is my visual identity", "audit my brand guidelines", "organize my references by format", "which palette and fonts should my posts use".
---

# Brand core

A brand core is one page that says what a brand looks like, **measured from its own material**: the visual identity (palette, type roles, photography worlds, repeating devices, logo role), a map of which reference serves which content format, the conflicts between sources, and 3 to 5 open decisions.

Core principle: **look and measure, never guess.** Every number comes from pixels, every citation from a freshly labeled contact sheet, and the findings live in the gaps between what the brand **declared** (guideline sheet, docs), what it **published**, and what it **references** (boards).

**Use it** when the person has boards, published pieces, a guideline sheet or brand docs and wants them turned into one coherent identity, an audit, or a format map.
**Not for**: a brand from nothing (no material to measure: brainstorm or art-direct first), logo design, or building the templates themselves (that comes after the decisions).

## Step 0: intake, before anything else

Ask once, in one compact message, for what is missing. Full checklist, reasons and a message template: `references/intake.md`.

- **Required**: (a) at least one reference set: public Pinterest board URLs or a folder of images, ideally one board per job; (b) **either** published pieces (carousel PNG/PDF exports, videos, profile screenshots) **or** a guideline sheet; (c) one paragraph of positioning: what the brand offers now, for whom (age, place, language), where the audience meets it.
- **Strongly recommended**: published pieces **and** guidelines (the gap between them is where most findings are), brand docs (voice, banned words, taglines, content series, audience tensions), logo/mascot SVG, the channel list.
- **Context**: did the offer change recently? which source wins in a conflict? who decides and who reviews? which fonts are licensed? which design tool? which language is the copy in?
- **Minimum viable run**: one reference set + positioning. The page then says, next to every palette and type conclusion, that it rests on references only.

Do not start measuring until each source is marked **own** or **reference**.

## Setup

Dependencies: Node 18+ with `playwright` (uses the system Google Chrome, no browser download), Python 3.9+ with Pillow and numpy, ffmpeg, poppler (`pdfinfo`, `pdftoppm`). Details: `references/collecting.md`.

```bash
mkdir -p work && cd work
PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm i playwright
python3 -I <skill>/scripts/colorlab.py          # numpy self-test; must print "ok"
```

`<skill>` is this skill's folder. Run Node scripts from `work/`; run Python with `-I`.

| Job | Command |
|---|---|
| Scrape public boards | `node <skill>/scripts/scrape_pinterest.mjs data <board URL>...` |
| Download pins, slots, video frames | `python3 -I <skill>/scripts/fetch_media.py .` |
| Import a folder, PDFs, videos, slide exports | `python3 -I <skill>/scripts/import_local.py <folder> . <slug>` |
| Labeled contact sheets | `python3 -I <skill>/scripts/contact_sheets.py .` |
| CIELAB grade, palettes, saturation outliers | `python3 -I <skill>/scripts/grade.py .` |
| Swatch vs label, accents, contrast | `python3 -I <skill>/scripts/measure.py grid\|swatch\|accent\|contrast ...` |
| Build the page | `python3 -I <skill>/scripts/build_page.py content.json brand-core.html --template brand-core.tpl.html --strict` |
| Verify | `node <skill>/scripts/check_page.mjs brand-core.html checks/` |

Each script documents its arguments at the top.

## Method

1. **Inventory.** One row per source: items (captured / counted), static · carousel · video split, main ratios, L*, b* (warmth), chroma, and "what this source answers". Own material in separate, highlighted rows.
2. **Collect.** Scrape boards, download media, extract video frames, import folders and PDFs, make contact sheets. → `references/collecting.md`
3. **Look.** Open every sheet and strip. Classify each item by intended format, role and photography world. Note items pinned for layout rather than color.
4. **Measure.** Per-source CIELAB stats and palettes (`grade.py`); accent sampling by hue band; WCAG contrast of the real text/background pairs; saturation outliers. → `references/measuring.md`
5. **Trace and audit.** Match published slide photos to board pins (a board that fed the posts is the photo bank, not inspiration). Sample every guideline swatch and compare to its label, then compare the sheet to what was published. → `references/measuring.md`
6. **Synthesize.** Format map by channel with specs, measured durations and sub-types mapped to content series (`references/formats.md`); the core: palette declared / used / referenced, type as roles, photography worlds with stats, repeating devices, logo role; conflicts with a one-line proposal each; 3 to 5 ordered decisions, each with options, an evidence-based recommendation and what it unblocks (`references/synthesis.md`).
7. **Publish** the brand-core page from `assets/brand-core.tpl.html` + `content.json`. With the Artifact tool, **load `artifact-design` and `artifact-capabilities` first**, then publish with the decision-log capability in `references/page.md`. Without it, build with `--standalone` and hand over the file.
8. **Verify once**: `check_page.mjs` (console errors, overflow at 390 px, interactions, broken images), then open the section screenshots and the alt sheets and fix every alt that does not match its image. Hand off with **decision 01 only**.

## Gotchas (each one cost real time)

| # | Trap | Do instead |
|---|---|---|
| 1 | Logged out, Pinterest stops at ~23 pins (signup wall, page height frozen) | Page the board feed API from the page context (the scraper does). `pin_count` includes dead pins: report the gap (131 of 146 in one run). |
| 2 | Idea pins (`story_pin_data`) look like video | Count video only from `videos.video_list` or a story block with a video. |
| 3 | numpy returned silent garbage above ~20k rows on macOS | Chunk conversion (≤ 8k rows) and k-means distances (≤ 2k); run the self-test (white → L* 100) first. |
| 4 | Board order changes between scrapes | Never reuse an old manifest's numbers. Cite only from fresh sheets; check every alt against its image (4 of ~90 were wrong). |
| 5 | Guideline labels lie | Sample swatch pixels (`measure.py swatch`); compare label, pixel and published use. Found: a Background labeled with the Error red, radius written "1,2px", a Shadows block titled "Border Radius", a swatch drawn off its label, the accent of every post missing, a declared serif nobody used. |
| 6 | Treating every board as inspiration | Trace published photos to pins; one board fed 9 of 22 slide photos. |
| 7 | One neon pin drives the palette | Items with p90 chroma 2-3× the source median are layout pins: flag them, leave them out of the palette. |
| 8 | Eyeballed accents and contrast | Sample by hue band + chroma/lightness, take the median pixel; report WCAG ratios of real pairs (off-white on a mid green was 3.4:1: large text only). |
| 9 | 20 MB page | Refs ~460 px, slides ~540 px, sheet ~2000 px, quality ~68; stay under ~9 MB (cap 16). |
| 10 | Blank headless screenshots | Force `scroll-behavior: auto` before `scrollIntoView` screenshots. |
| 11 | Squinting at PDFs | `pdfinfo` for pages and size, `pdftoppm -r 40` for quick sheets; prefer per-slide PNG exports. |

## Red flags: stop and go back

- About to cite "#12" without having opened the sheet made from the current manifest.
- About to copy a hex from a guideline label.
- A palette that changes when one pin is removed.
- Calling something "warm", "muted" or "minimal" without the L*, b* or chroma behind it.
- More than 5 decisions, or a decision without a recommendation.
- Publishing before opening the screenshots and the alt sheets.
- Material from before an offer change treated as current without a flag.

## Platform specs

The format defaults used (Instagram feed 1080×1350 with the grid cropping to 3:4, keep key content in the central 1012 px; Reels/Stories 1080×1920 with text out of roughly the top 220-250 px and bottom 340-420 px) change over time. Re-verify against current platform docs and state the date on the page. Full table: `references/formats.md`.
