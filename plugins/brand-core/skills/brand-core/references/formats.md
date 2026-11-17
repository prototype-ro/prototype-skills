# The format map

The format map answers "which reference is for which format", channel by channel, so whoever makes the next piece opens one section and finds the spec, the sub-types that repeat, the references for each, and the content series each serves.

## Channel specs (defaults, re-verify)

These are the values one real run used. **Platforms change them; check the current official docs before publishing the page**, and say on the page when a value was last checked.

| Channel / format | Canvas | Ratio | Safe zones and notes |
|---|---|---|---|
| Instagram feed post / carousel | 1080×1350 | 4:5 | The profile grid crops to 3:4: keep key content in the central 1012 px of width. Check the current max slides per carousel. |
| Instagram single square (legacy) | 1080×1080 | 1:1 | Still accepted; looks small in a 4:5 feed. |
| Reels | 1080×1920 | 9:16 | Keep text out of roughly the top 220-250 px and the bottom 340-420 px (caption, buttons, audio). |
| Stories | 1080×1920 | 9:16 | Same safe zones; leave room for a poll or link sticker. |
| TikTok | 1080×1920 | 9:16 | Bottom ~400 px and the right edge (~120 px, action buttons) are covered. |
| YouTube Shorts | 1080×1920 | 9:16 | Similar overlays to Reels. |
| YouTube thumbnail | 1280×720 | 16:9 | Readable at 160 px wide. |
| LinkedIn image post | 1080×1350 or 1200×627 | 4:5 or 1.91:1 | Document (PDF) carousels: 1080×1350 or 1080×1080 pages. |
| Pinterest pin | 1000×1500 | 2:3 | Taller pins get cropped in the grid. |
| Ebook / guide / print | A4 or 2:3 pages, spreads | | Bleed and margins depend on the printer. |
| Landing page | 1440 desktop, 390 phone | | Hero must work at 390 px. |
| App Store / Google Play screenshots | per current store spec | | Device sizes change every year; take them from App Store Connect / Play Console. |

## Measured, not assumed

Take these from the references, not from habit:

- **Duration range** of video formats: from the pinned videos' `video.ms` in the manifests (for example "8-22 s, median 15 s across the 9 pinned reels").
- **Slide count** of carousels: from the carousel slots (`carousel` length) and the published pieces.
- **What the text does** in video: count how many reels carry a voice-over, big captions, or one small line. That decides the reel template more than any color.

## Sub-types

Inside each format, group references by **how they are built**, not by subject. Typical sub-types that recur on boards:

- Reels: near-static scene with one line of text; POV clips with one caption that stays while clips cut every ~2 s; cinematic montage (sometimes letterboxed); detail cuts (macro, materials, hands).
- Stories: photo in a rounded card with poem-length text and a mono date; texture or sky ground that leaves room for a sticker; a dark "night" story with one warm light.
- Feed carousel: editorial essay (photo full-bleed, mixed grotesk + serif headline, series label in the same corner of every slide); text over photo, one idea per slide; collage cover with notebook or grid-paper inside pages; annotated photo (labels pointing at things); scrapbook itinerary or step list.
- Single post: poster with a big name and small data; one line over a landscape; an announcement with a single button.
- Photo series: photo-only carousel, no type or a month name at most (3:4 or 4:5, up to the platform max).
- Long-form: contents spreads, photo + text spreads, covers; usually the lowest chroma of all sources.
- Web / app / store: screens over a photo, widgets, phone mockups.

Name each sub-type in a few words, give its build in one line, show 2-4 references, and say which **content series** of the brand it serves ("For the brand: <series>"). A sub-type that no series needs is noise: leave it out or list it under "not now".

## Own pieces in the map

Put the brand's already-published pieces into the map too, as the first sub-type of their format ("Already made"), outlined (`class="ref made"`, `data-src="made"`). The filter chips let a reviewer show only what the brand already did, or only one board.

## When a format has no references

Say so ("Nothing made yet; no references") rather than inventing a sub-type. If the channel matters for the positioning, that gap is a finding.
