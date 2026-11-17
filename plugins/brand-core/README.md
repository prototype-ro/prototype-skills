# Prototype | Brand-Core

**A skill for Claude Code that turns a pile of boards, old posts and a guideline sheet into one page that says what the brand looks like, with numbers behind every claim.**

Most brands already have their identity scattered across places: a few Pinterest boards, some carousels already posted, a guideline PNG someone made last year, a doc with the voice rules. They rarely agree. The posts use an accent the guideline never wrote down; the guideline declares a serif nobody used; one board turns out to be where half the photos came from.

**Brand-Core** makes Claude assemble the brand's **core** from that material:

- the **visual identity**: palette compared three ways (declared, used, referenced), type as roles, photography "worlds" with measured CIELAB stats, repeating devices, the logo's role;
- a **format map**: which reference is for which format, per channel, with specs, measured durations and sub-types mapped to the brand's content series;
- the **conflicts** between what is written, drawn, published and referenced, each with a one-line proposal;
- **3 to 5 decisions**, ordered by what they unblock, each with a recommendation grounded in the evidence.

It all lands on one interactive page (a claude.ai Artifact, or a standalone HTML file): section nav, a lightbox on every image, source filters, click-to-copy swatches, a WCAG contrast checker, swipeable carousels of what was published, reference → slide trace pairs, and a shared decision log where everyone records their pick.

```
You:    build the brand core from these boards and our last four carousels
Claude: Before I start I need: the positioning paragraph, and (if you have it) the guideline sheet...
        → scrapes 4 boards (131 of 146 pins served), imports 3 carousels + the sheet
        → measures, traces 9 of 22 slide photos to one board, finds 6 errors in the sheet
        → publishes the page: 7 sections, 5 decisions. Decision 01: which palette do we follow?
```

## What the skill teaches Claude

- **Intake first**: what to require (a reference set; published pieces or a guideline sheet; a positioning paragraph), what is strongly recommended, the context questions, and the minimum viable run.
- **Collecting** public Pinterest boards past the logged-out wall (~23 pins) by paging the board feed from the page context; downloading original images, carousel slots and video frames; importing local folders, PDFs and videos into the same layout.
- **Looking** at every item on labeled contact sheets before citing anything, because board order changes between scrapes.
- **Measuring** in CIELAB: lightness, warmth, chroma, k-means palettes without saturation outliers, accent sampling by hue band, WCAG contrast of real pairs, guideline swatches sampled from pixels and compared with their labels.
- **Tracing** which references actually fed the published pieces.
- **Synthesizing** the format map, the core, the conflicts and a short list of decisions.
- **Publishing and verifying** the page: console errors, horizontal overflow at 390 px, interactions, and alt texts checked against their images.

## Bundled tools

| Script | What it does |
|---|---|
| `scrape_pinterest.mjs` | Public Pinterest board → JSON manifest (pins, sections, carousels, real videos, original sizes) |
| `fetch_media.py` | Downloads originals, carousel slots and video frames; re-downloads numbers whose pin changed |
| `import_local.py` | Folder of images / sub-folders / PDFs / videos → the same layout |
| `contact_sheets.py` | Labeled contact sheets (`#N ratio kind`) and per-item strips |
| `grade.py` | Per-source CIELAB stats, k-means palette, saturation outliers |
| `measure.py` | `grid`, `swatch` (pixel vs label, ΔE), `accent` (hue band median), `contrast` (WCAG) |
| `colorlab.py` | Chunked color math with a self-test (a macOS numpy build returned silent garbage on big arrays) |
| `build_page.py` | Fills the page template from `content.json`, builds carousels and trace pairs, inlines images |
| `check_page.mjs`, `overflow.mjs` | Headless verification and alt-text sheets |

Plus `assets/brand-core.tpl.html` (the page skeleton with marked slots) and `assets/content.example.json`.

## Install

### Option A: as a Claude Code plugin (recommended)

Inside Claude Code:

```
/plugin marketplace add prototype-ro/prototype-skills
/plugin install brand-core@prototype
```

Update later with `/plugin marketplace update prototype`.

### Option B: copy the skill folder

```bash
git clone https://github.com/prototype-ro/prototype-skills.git /tmp/prototype-skills
mkdir -p ~/.claude/skills
cp -r /tmp/prototype-skills/plugins/brand-core/skills/brand-core ~/.claude/skills/
```

Restart Claude Code, or start a new session, so the skill is picked up.

### Other agents

The skill follows the [Agent Skills](https://agentskills.io) format: a `SKILL.md` plus `references/`, `scripts/` and `assets/`. Drop the `brand-core` folder wherever your agent looks for skills.

## Use

Claude loads the skill when you say things like:

- "build our brand core from these Pinterest boards"
- "what is our visual identity, based on what we already posted?"
- "audit our brand guidelines against our last carousels"
- "which of these references is for reels and which for the feed?"

Or call it directly: `/brand-core` (or `/brand-core:brand-core` when installed as a plugin).

**What to have ready:** the board URLs (public) or a folder of references; your published pieces (per-slide PNG exports are best) and/or your guideline sheet; one paragraph on what you offer, for whom and where they find you. Brand docs, the logo as SVG and the list of channels make the result sharper.

## Requirements

- Claude Code (or any agent that supports skills).
- Node 18+ and the `playwright` package (`PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm i playwright`); it drives your installed Google Chrome, so no browser download is needed.
- Python 3.9+ with Pillow and numpy.
- ffmpeg (video frames) and poppler (`pdfinfo`, `pdftoppm`) for PDFs.
- Optional: claude.ai Artifacts, for the shared decision log. Without them the page is a standalone HTML file with read-only decisions.

## Structure

```
plugins/brand-core/
  .claude-plugin/plugin.json          plugin manifest
  skills/brand-core/
    SKILL.md                          the skill
    references/                       intake, collecting, measuring, formats, synthesis, page
    scripts/                          the tools above
    assets/                           page template and content.json example
```

Part of [Prototype Skills](../../README.md).

## License

[MIT](../../LICENSE)

---

### Em português

**Prototype | Brand-Core** é uma skill para o Claude Code. A partir do material que a marca já tem (boards do Pinterest ou pastas de referências, peças já publicadas, um guia de marca, documentos de voz), ele monta o **núcleo da marca**: identidade visual medida nos pixels, um mapa de qual referência serve para qual formato, os conflitos entre as fontes e de 3 a 5 decisões em aberto, tudo numa página interativa com registro de decisões compartilhado.

Para instalar, rode `/plugin marketplace add prototype-ro/prototype-skills` e depois `/plugin install brand-core@prototype`. Outra opção é copiar `skills/brand-core` para `~/.claude/skills/`.
