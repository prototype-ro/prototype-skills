# Collecting: boards, folders, PDFs, videos

Everything ends up in one layout so the same sheet and grade scripts work on every source:

```
work/
  data/<slug>.json        one manifest per source (items numbered n = 1, 2, 3 ...)
  media/<slug>/NNN.<ext>  one cover image per item
  media/<slug>/NNN-cK.*   carousel slot K (or PDF page K)
  media/<slug>/NNN-vK.jpg video frame K (every 2 s, max 6)
  sheets/                 contact sheets
```

Use one slug per source, short and meaningful: `posts-board`, `city`, `outdoor`, `graphics`, `published`, `guidelines`.

## Setup once per work folder

```bash
mkdir -p work && cd work
PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm i playwright   # uses the system Google Chrome; no browser download
python3 -m pip install pillow numpy                   # if missing
python3 -I <skill>/scripts/colorlab.py                # numpy self-test: must print "ok"
```

Run the Node scripts from the work folder (that is where `playwright` resolves). If Chrome is not installed, `npx playwright install chromium` and set `PW_CHANNEL=""`.

## Pinterest boards

```bash
node <skill>/scripts/scrape_pinterest.mjs data https://www.pinterest.com/<user>/<board>/ [more boards]
python3 -I <skill>/scripts/fetch_media.py .
```

How it works and why:

- **Logged out, scrolling stops at ~23 pins**: a signup modal appears and the page height freezes. The scraper does not scroll. It opens the board once, then pages Pinterest's own JSON resources from inside the page with `fetch` (`BoardResource` for the board, `BoardFeedResource` for pins, `BoardSectionsResource` + `BoardSectionPinsResource` for sections), with the headers the site itself sends (`X-Requested-With: XMLHttpRequest`, `X-Pinterest-PWS-Handler`). It reads only what a logged-out visitor can see, so only public boards work. Use it on boards the person owns or curates.
- **The gap is normal.** `board.pin_count` includes pins that no longer serve (deleted source, removed image). Expect captured < pin_count (in one real run, 184 of 207) and report the gap in the inventory instead of hunting for the missing ones.
- **Idea pins are not videos.** `story_pin_data` ("idea pins") were almost all single images. Real video comes from `videos.video_list` or from a story block that contains a video; only those get a `video` field. Count video from that field only.
- **Board order changes between scrapes.** Pin #12 today may be #15 tomorrow. Numbers are only valid for the manifest that produced them. `fetch_media.py` keeps `.ids.json` per folder and re-downloads any number whose pin id changed, but anything you wrote down from an older run is stale: re-check every citation against a freshly made contact sheet.
- Each manifest keeps title, description, link, domain, dominant color, section, original image size, video size and duration, carousel slots. Durations of the pinned videos are what the format map's duration range comes from.

## Local folders (references or the brand's own pieces)

```bash
python3 -I <skill>/scripts/import_local.py <folder> . <slug>
```

- Image files become single items; a **sub-folder of images becomes one carousel item** (put each published carousel's slides in its own sub-folder); a **PDF becomes one carousel item** with a slot per page; a **video file becomes a video item** with a cover and frames.
- Prefer the designer's per-slide PNG exports over PDFs: sharper, true color, real pixel size.
- PDFs: `pdfinfo file.pdf` gives the page count and page size (a 1080×1350 pt page is a 4:5 post); `pdftoppm -r 40 -jpeg file.pdf out/p` is enough for a quick look; import renders at 72 dpi (`--dpi` to change).
- Screenshots of the live profile grid are evidence of how the 3:4 grid crop treats the 4:5 posts. Import them as their own source (`profile`).
- HEIC needs macOS `sips`; TIFF and BMP are converted to PNG.

## The guideline sheet

Import it as its own source (`guidelines`) so it gets a contact sheet, but measure it at full size with `measure.py` (see measuring.md). Keep the original file: labels and swatches are read from it, never from a downscaled copy.

## Contact sheets

```bash
python3 -I <skill>/scripts/contact_sheets.py .
```

12 tiles per sheet, each labeled `#N  ratio  kind` (kind = img, CAROUSEL xK, VIDEO 12s), plus a strip per carousel or video item (`<slug>-xNNN.jpg`) with every slot or frame. These labeled sheets are the only numbering you cite.
