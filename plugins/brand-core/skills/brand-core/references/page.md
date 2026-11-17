# The brand-core page: build, publish, verify

## What the page contains

Sections, in order (each one a `<section class="stop">` with a nav link; delete a section and its link when there is no material for it):

| # | id | Contents |
|---|---|---|
| hero | | brand name, one-line frame, how the material was read, 4-5 KPIs (items read of total, pieces traced to a board, sheet errors, decisions open) |
| 01 | `sources` | the inventory table, own rows highlighted |
| 02 | `made` | each published piece as a swipeable carousel with per-slide role, note and flags; the board → slide trace pairs; keep / change / fix-before-reposting columns |
| 03 | `guidelines` | the sheet (lightbox), the type scale, sampled ramps, the errors found (severity hi / md / lo) |
| 04 | `formats` | the format map with source filter chips; own pieces outlined |
| 05 | `core` | palette three ways, contrast checker, type voices, photography worlds, devices, logo/mascot |
| 06 | `conflicts` | written vs drawn vs published vs referenced, each with a proposal |
| 07 | `decisions` | the shared decision log |

Built-in behaviour (already in the template): sticky section nav with scrollspy; lightbox on every image (arrows, Escape, focus trap; groups by carousel/strip/grid); filter chips generated from the `data-src` keys found in the format map (choice remembered per viewer); click-to-copy hex swatches; a WCAG contrast checker over every palette; swipeable carousels with prev/next and a counter; light and dark themes; phone layout at 390 px.

## Files

```
work/
  brand-core.tpl.html   copy of <skill>/assets/brand-core.tpl.html; you edit this copy
  content.json          start from <skill>/assets/content.example.json
  brand-core.html       the build output
```

### Template conventions

- `@@TITLE@@`, `@@BRAND@@`, `@@POSTS@@`, `@@PAIRS@@`, `@@DATA@@`: generated from `content.json`.
- `@@<source>/<name>@@`: an image, inlined as a JPEG data URI. `<source>` is a key of `content.json` `sources`; `<name>` is the file name without extension (`@@city/016@@`, `@@city/007-c4@@`, `@@outdoor/012-v3@@`).
- `@@RATIO:<source>/<name>@@`: that image's `W / H`, for `aspect-ratio`.
- `[[...]]`: text you write. Every one must be gone before publishing (`--strict` refuses otherwise).
- HTML comments (the `SLOT` notes) are stripped from the output.
- Every reference figure in the format map needs `data-src="<source>"`; own pieces use `data-src="made"` and `class="ref made"`.
- Re-skin the page tokens (`:root` and both dark-mode blocks) with the brand's measured UI colors once known, and the `--brand-*` tokens used by specimens. Swap the Google Fonts link for the brand's faces or the closest licensed stand-ins.

### content.json

See `assets/content.example.json`. Keys: `title`, `brand`, `lang`, `storage_key`, `quality`, `default_box`, `sources` (`dir` or `file`, optional `box` and `label`), `slide_name` (how published slides are named in `sources.made.dir`, default `p{post}-{slide}`), `posts`, `pairs`, `palettes`, `ramps`, `contrast_default`, `decisions`. Paths are relative to `content.json`.

### Image budget

| Image | Box (px) | Note |
|---|---|---|
| board reference | ~460 on the long side | `default_box: [460, 740]` |
| published slide | ~540 | `sources.made.box: [540, 675]` |
| guideline sheet | ~2000 | people zoom into it |

JPEG quality ~68. A page with ~100 images lands around 8 MB. Keep it under ~9 MB; the Artifact hard cap is 16 MB.

### Build

```bash
python3 -I <skill>/scripts/build_page.py content.json brand-core.html --template brand-core.tpl.html            # draft: reports slots left
python3 -I <skill>/scripts/build_page.py content.json brand-core.html --template brand-core.tpl.html --strict   # before publishing
```

Add `--standalone` when the result is a local file instead of an Artifact (it adds the `<!doctype html>`, `<head>` and `<body>` the Artifact host otherwise provides).

## Publish

### As a claude.ai Artifact (when the Artifact tool exists)

1. Load the `artifact-design` and `artifact-capabilities` skills first. They hold the current page contract and the runtime API; if they disagree with this file, they win.
2. Publish the build (without `--standalone`) with this capability declaration, which is what worked for the shared decision log:

```json
{
  "db": { "rules": [
    { "path": "picks", "read": "view", "write": "owner" },
    { "path": "picks/{self}", "write": "interact" },
    { "path": "final", "write": "admin" }
  ] },
  "user": { "scopes": ["profile"] }
}
```

Each viewer writes only `picks/<their user id>` (`{ <decision id>: <option key>, at }`); everyone who can view reads all picks and sees avatars under each option; editors write `final/state` (`{ <decision id>: <option key> }`) with "mark final". The template already does this through `window.claude.use('db')` and `use('user')`, and renders the options **read-only** with a status line when `window.claude` or `db` is unavailable (a local file, a signed-out viewer, view-only access).

3. The page imitates no one: it is the person's own brand material, private by default. Do not include account handles of the boards in the page; name boards by their title.

### As a standalone file (no Artifact tool)

Build with `--standalone`, verify, and hand over the file path. Picks are read-only there; ask for decisions in chat instead.

## Verify (one pass)

```bash
node <skill>/scripts/check_page.mjs brand-core.html checks/
node <skill>/scripts/overflow.mjs brand-core.html 390      # only if check_page reports overflow
```

`check_page.mjs` checks desktop (1280, light) and phone (390, dark): console and page errors, horizontal overflow, broken or placeholder images, and the interactions (a filter chip hides other sources; the lightbox opens, advances with the arrow key and closes with Escape; a carousel advances; the contrast checker computes a ratio). It writes a screenshot per section and `alt-N.jpg` sheets with every image next to its alt text.

Then **open the screenshots and the alt sheets**. Fix any alt that does not describe its picture (on one first pass, 4 of ~90 were wrong) and anything that looks off, rebuild with `--strict`, and re-run the check once. Screenshots taken right after `scrollIntoView` under `scroll-behavior: smooth` can come out blank; the script forces `scroll-behavior: auto` for that reason.

## Hand-off

Send the link (or file path), one line on what the page shows, what was not verified (for example: platform specs as of a date, fonts shown as stand-ins), and **decision 01 only**.
