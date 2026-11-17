# Looking, measuring, tracing, auditing

## Look before you count

Open **every** contact sheet and every carousel/video strip. For each item write one line in a working note (not on the page yet):

```
<slug> #N | format (feed carousel / single / reel / story / long-form / web) | ratio | role (cover, text slide, photo, texture, layout idea, device) | world (city, nature, product...) | why it is pinned, in 5 words
```

Classify by **intended format** (what the item is for), not only by ratio: a 9:16 pin can be a story, a reel frame, or a phone screenshot of a feed post. Note items pinned for layout rather than for color or photography: they matter for the format map, not for the palette.

## Per-source stats (grade.py)

```bash
python3 -I <skill>/scripts/grade.py .
```

All numbers are CIELAB (D65), computed on 160 px thumbnails, one cover image per item.

| Field | Reads as | Typical range |
|---|---|---|
| `L_mean` | lightness, 0 black to 100 white | low-key city photography ~40, paper/editorial ~60-70 |
| `L_sd` | tonal contrast within images | flat/foggy < 15, punchy > 25 |
| `chroma` | colorfulness, 0 = grey | muted < 12, colorful > 20 |
| `b_mean` | warmth: + yellow, - blue | neutral ±2, warm > +5 |
| `warm_share_pct` | share of items with mean b* > +5 | |
| `low_chroma_share_pct` | share of items with mean C* < 12 ("muted") | |
| `palette` | 10 k-means centers, share %, outliers excluded | |
| `outliers` | items with p90 chroma >= 2x the source median | |

**Saturation outliers**: items whose p90 chroma is 2-3x the source median are almost always pinned for a layout or a graphic, not for color. `grade.py` leaves them out of the palette and lists them; say so on the page instead of letting one neon poster turn the palette orange.

**The numpy trap**: a macOS numpy build once returned garbage, silently, for vectorized math on arrays above ~20k rows (both 2D matmul and chains of 1D ops). All color math lives in `colorlab.py`, chunked (≤ 8k rows for conversion, ≤ 2k for k-means distances), and every script runs `self_test()` first (white must be L* 100, black 0, sRGB red 53.2). If you write any new color math, chunk it the same way and test it on known colors before trusting a number.

## The inventory table

One row per source, own material first:

| Source | Items | Static · carousel · video | Main ratios | L* | b* (warmth) | Chroma | What it answers |
|---|---|---|---|---|---|---|---|

- Items: `captured / pin_count` for boards, so the gap is visible.
- Main ratios: the top 2-3 with counts, from the contact sheet labels (`4:5 ×28 · 9:16 ×11`).
- "What it answers" is one line in plain words: "how a carousel is built", "the photo bank the posts draw from", "outdoor photography and reels".

## Guideline sheet audit: labels lie

Never copy a hex from a label. Sample the drawn swatch and compare.

```bash
python3 -I <skill>/scripts/measure.py grid guidelines.png grid.jpg --step 250    # open grid.jpg, read coordinates
python3 -I <skill>/scripts/measure.py swatch guidelines.png \
  "Background:3300,1990,120,40=#E5484D" "Primary:3300,745,120,40=#2B2B2B"
```

`swatch` prints the median color of each box, the label's hex, ΔE, and ok / close / MISMATCH. Pick boxes inside the flat part of the swatch, away from its text (a "box not flat" warning means text or an edge got in).

Things that were actually found on a real sheet, so look for each:

- a token labeled with **another token's hex** (a "Background" labeled with the Error red; anyone copying the label paints the UI red);
- **unreadable values** ("radius 1,2px · 2,4px · 4,8px" — decimal commas and wrong units);
- a section **titled as another section** (a Shadows block headed "Border Radius");
- a **main swatch drawn in a different hex** than its label (ΔE ~6: small, but it is the color of every dark card);
- ramps whose top steps quietly change hue (a grey ramp ending in a teal), which turned out to be the exact fill used in the published posts.

Then check the sheet against what was **published**: the accent used in every post may be missing from the sheet; the declared serif may not be the serif in the posts; declared shadows may appear nowhere. Each of these becomes a conflict (synthesis.md).

## Measured accents

Accents are small areas (a highlighted word, an arrow, a stat), so a whole-image palette misses them.

```bash
python3 -I <skill>/scripts/measure.py accent media/published                      # hue histogram of saturated pixels
python3 -I <skill>/scripts/measure.py accent media/published --hue 95-115 --min-chroma 35 --min-l 75
```

First run without `--hue` to see which hue bands exist, then isolate one band with chroma and lightness thresholds. The result is the median pixel of the matching set (a real pixel, not an average that never occurs) and which images contain it. Report it next to the declared value, if any.

## Contrast pairs

Measure the real text/background pairs used in the published pieces, not every palette combination:

```bash
python3 -I <skill>/scripts/measure.py contrast "#FFFFFF:#5E8C8A" "#F5F5F4:#3E7D65"
```

WCAG 2.x: ≥ 4.5 for body text, ≥ 3 for large text (18 pt, or 14 pt bold), ≥ 7 for AAA. A mid-tone fill under white text often lands at 3.5-4:1: fine for a headline, not for body copy. Say which pairs are large-text-only. The page's contrast checker lets reviewers try any other pair.

## Trace what fed the published pieces

For every photo in the published pieces, look for its source on the boards: put the published slides' strips next to the board sheets and match by eye (same scene, same crop, same grade), then confirm by opening both originals. Record pairs as `board/NNN → piece P slide S`.

Why it matters: in one run, 9 of 22 slide photos came straight from one board. That board stopped being "inspiration" and became "the photo bank", which changes its weight in every conclusion (its grade *is* the published grade). Report the count ("9 of 22 slide photos are pins from one board") and show the pairs on the page.

## Before anything goes on the page

- Re-make the contact sheets if anything was re-scraped, and re-check every number you will cite against them.
- Write each alt text by looking at the image, then check it again on the alt sheets `check_page.mjs` produces. On one first pass, 4 of ~90 alts described the wrong image.
