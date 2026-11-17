---
name: design-lab
description: Build a development-only "lab" page for a UI component or section, where the person changes its design properties live with sliders, switches and presets, compares variants side by side with made-up data, and finally pastes the settings back so the real component is built from them. Use when the person wants to try, compare or "nail down" the look of a list, card, bar, heading, row, panel or any repeated piece of interface before committing to it, or says "make a lab", "style page", "playground", "let me tweak it", or "give me options to test".
---

# Design lab

A lab is a throw-away page that exists only in development. It shows one real piece of interface (a deck list, a card stack, a command bar, a table row) with fake data, and puts every design decision of that piece on a control: a slider, a switch, a segmented choice. The person plays until it feels right, presses **Copy settings**, pastes the JSON in chat, and the real component is then built from those exact values. The lab replaces rounds of "make it a bit tighter" with one round of "here is what I chose".

It earns its keep when the question is taste (spacing, density, how selection looks, how a heading reads), not logic. It was developed on a real product (a card-collection app built with Next.js and Tailwind v4), where it settled the list view, the stacks view, the command dock and the version timeline fade, and the notes below come from that work. The code samples use React, Next.js and Tailwind; the method works the same in any stack (Vue, Svelte, plain HTML), so translate the snippets to the project's own framework and tokens.

## When to use it, and when not

Use a lab when:
- there are many small independent choices (row height, dividers, hover, selected style, heading style, columns) and the person cannot name the answer but will recognise it;
- the person shows a reference (a competitor, a screenshot, a recording) and wants to compare "ours" against it;
- a choice is better judged live and in motion (hover, selection, raised cards, animation) than in a screenshot.

Do not use a lab when the question is a single yes or no, when the data or logic is what is undecided, or when a 3-option concept page is enough. The ladder, from lightest to heaviest:

1. **Concept page**: 2 to 4 labelled options per question, each interactive, no controls (`/dev/<topic>-concepts`). Use it to choose a direction.
2. **Lab**: one component, many controls, presets (`/dev/<component>-lab`). Use it to tune the chosen direction.
3. **Tuner**: a small floating panel of sliders that sets CSS variables on the real page (for one thing that only makes sense in place, such as a dock over scrolling content). Use it for glass, blur, opacity and similar values that depend on what is behind them.

Start with a concept page when the direction is open, and a lab when the direction is known.

## Workflow

1. **Read the real component** (and the tokens, spacing and type it uses) before writing anything. The lab must look like the product, not like a generic mock. Reuse the real design tokens, the real icon/badge/button components, the real fonts.
2. **List the decisions.** Walk through the real component and write down every visual and behavioural property that could vary: sizes, spacing, dividers, hover, selected state, badges, density, alignment, which fields show, heading style, layout (columns, masonry), motion. Group them (Layout, Rows, Content, Heading, Mode).
3. **Mine references.** If the person gave a screenshot or a recording, extract frames and write down the concrete differences (see "Analysing a reference" below). Turn each difference into a control or a preset.
4. **Build the lab page** (structure below). Make the first screenshot already look good with the "Current" preset, so the starting point is the real thing.
5. **Verify** with a headless browser in dark and light, per preset (see "Verification"). Look at the screenshots. Fix clipping, wrapping and contrast before showing it.
6. **Hand it over** with: the URL, what each group of controls does, honest notes on anything that looks weak in a screenshot, and the one question that moves it forward ("paste the settings").
7. **Apply the pasted settings** to the real component exactly, and report what was applied and what was left out (the lab usually has options the person did not choose).
8. **Offer cleanup.** Keep the lab while the area is still being designed. Remove it, or leave it as a documented dev page, when the design is settled. Never ship it.

## Anatomy of a lab page

Files, under the app's dev routes (Next.js App Router shown; adapt the router):

```
app/dev/<name>-lab/
  page.tsx      server component, 404s in production
  <Name>Lab.tsx client component: settings, controls, preview
  mock.ts       made-up data (never real user data)
```

### page.tsx (the gate)

```tsx
import { notFound } from "next/navigation";
import { NameLab } from "./NameLab";

export const metadata = { title: "Name lab" };

/** A development page. It does not exist in a production build. */
export default function NameLabPage() {
  if (process.env.NODE_ENV === "production") notFound();
  return <NameLab />;
}
```

### Settings: one typed object

Every control maps to one key of a single `Settings` interface. Use string unions for choices, numbers for sliders, booleans for switches. Keep a `CURRENT` constant that reproduces what the real product does today, and a `PRESETS` array of `[name, Settings]` pairs, always starting with `["Current", CURRENT]`.

```tsx
interface Settings {
  cols: number;                       // slider
  rowH: number;                       // slider
  divider: "line" | "dotted" | "none"; // segmented
  hover: "fill" | "bar" | "lift" | "none";
  price: boolean;                     // switch
}
const CURRENT: Settings = { cols: 3, rowH: 36, divider: "line", hover: "fill", price: false };
const PRESETS: Array<[string, Settings]> = [
  ["Current", CURRENT],
  ["Compact", { ...CURRENT, rowH: 30, cols: 4 }],
];
```

### Persistence and copy

Save to `localStorage` on every change (wrapped in try/catch, the page must work without storage), load on mount merged over `CURRENT` so old saves survive new keys, and provide a **Copy these settings** button that writes `JSON.stringify(settings, null, 2)` to the clipboard (also in try/catch). The person pastes that JSON in chat. Changing a key name later is safe because of the merge.

```tsx
const set = <K extends keyof Settings>(key: K, value: Settings[K]) =>
  setS((cur) => {
    const next = { ...cur, [key]: value };
    try { localStorage.setItem(STORE, JSON.stringify(next)); } catch {}
    return next;
  });
```

### The three control primitives

Keep these tiny and identical across labs so the person learns them once.

```tsx
function Seg<T extends string>({ label, value, options, onChange }: { label: string; value: T; options: Array<[T, string]>; onChange: (v: T) => void }) {
  return (
    <div>
      <p className="mb-1.5 text-xs text-muted">{label}</p>
      <div className="flex flex-wrap gap-1" role="group" aria-label={label}>
        {options.map(([key, text]) => (
          <button key={key} type="button" aria-pressed={value === key} onClick={() => onChange(key)}
            className={`min-h-8 rounded-full border px-3 text-xs transition-colors ${value === key ? "border-ink bg-ink text-bg" : "border-line text-muted hover:text-ink"}`}>
            {text}
          </button>
        ))}
      </div>
    </div>
  );
}

function Slide({ label, value, min, max, step = 1, unit = "", onChange }: { label: string; value: number; min: number; max: number; step?: number; unit?: string; onChange: (v: number) => void }) {
  return (
    <label className="grid grid-cols-[84px_1fr_44px] items-center gap-2 text-xs">
      <span className="text-muted">{label}</span>
      <input type="range" min={min} max={max} step={step} value={value} onChange={(e) => onChange(Number(e.target.value))} className="accent-[var(--accent-text)]" />
      <span className="text-right font-mono tabular-nums">{value}{unit}</span>
    </label>
  );
}

function Flag({ label, value, onChange }: { label: string; value: boolean; onChange: (v: boolean) => void }) {
  return (
    <button type="button" role="switch" aria-checked={value} onClick={() => onChange(!value)} className="flex items-center justify-between gap-3 text-xs">
      <span className="text-muted">{label}</span>
      <span className={`relative h-5 w-9 rounded-full border transition-colors ${value ? "border-accent-text bg-accent" : "border-line bg-surface"}`}>
        <span className={`absolute top-0.5 size-3.5 rounded-full bg-ink transition-all ${value ? "left-[18px]" : "left-0.5"}`} />
      </span>
    </button>
  );
}
```

Group controls with `<fieldset>` and a small uppercase legend (Layout, Rows, Content, Group heading, Mode). Put the controls in a sticky left column (`lg:grid-cols-[300px_minmax(0,1fr)]`, `lg:sticky lg:top-4 lg:max-h-[calc(100vh-32px)] lg:overflow-auto`) and the preview in a bordered rounded container on the right. Presets go at the very top of the column as small pill buttons.

### The preview

- Render the real structure with the real classes wherever possible. When the real component is not reusable (it needs a store, auth, a server), copy its markup into the lab and keep the same class names so the port back is mechanical.
- Drive every visual choice from `Settings` through a small number of helper maps (`const SELECTED: Record<Settings["select"], string> = {...}`), not scattered conditionals. Adding a variant then costs one line, and the person can ask "add more options for X" and get them in minutes.
- Give the data enough variety to expose problems: a long name that wraps, a card with a New badge and one with a Need badge, a 35-item group beside a 2-item group, a colourless item, a zero-cost item, a multi-copy item.
- Make states clickable and hoverable in the preview (selected row, raised card) because the state styles are usually what is being chosen.
- Add a **page width** switch (for example 900, 1200, full) when the component sits in a column of a real page; many "looks fine" problems only show at the real width.

### Theme

Use the app's real tokens (`bg-bg`, `text-ink`, `text-muted`, `border-line`, `bg-surface`) so the header's own theme switch flips the lab between dark and light. If a colour needs different lightness per theme (role colours, tints), define two CSS variables scoped to the lab and override them under `:root[data-theme="light"]` and `@media (prefers-color-scheme: light)` with `:root:not([data-theme="dark"])`. Always check both themes.

## Control vocabulary for common components

When building a lab, offer these by default and add component-specific ones.

Rows and lists: row height, text size, weight, row radius; dividers (line, dashed, zebra, none); hover (fill, edge bar, lift, none); selected (fill with bar, outline, glass, invert, marker, glow, tint, dither, aura, card-colour gradient) plus a selection-colour source (accent, role, card colours) and a selection radius; menu affordance (always visible, on hover, dots); quantity (left, after name, badge); price, cost (off, left, right, dots), role (off, dot, edge bar, strand), art thumbnail, secondary badges; group heading (plain, mono caps, share bar, swiss, role dots); columns, column gap, page width; display mode (list, table with sortable sticky header).

Stacks and cards: arrangement (grid, masonry, long groups continue in next column), card width, gutter, visible strip height, corner radius, raised card (pushes the stack, floats over it), shadow between cards, tint on the strip, cost on the strip, heading style.

Bars and floating chrome: width, height, opacity, lightness, blur, saturation, border, shadow, text contrast, text weight, corner radius (use a tuner of CSS variables when the look depends on what scrolls underneath).

Add a **Mode** group for structural alternatives that change the whole layout (list vs table, grid vs masonry). Put preset buttons for named styles (for example "Current", "Compact", "Swiss", "Editorial", "Competitor-like") so the person can jump to a coherent look and then tweak.

## Tuners for in-place chrome

Some things cannot be judged inside a lab (a glass bar over scrolling art). Build a **tuner**: a small dev-only floating panel (a button in a corner, like `Dock`) that sets CSS variables on `document.documentElement`, with the real component reading them through fallbacks:

```css
.dock {
  background: color-mix(in srgb, color-mix(in srgb, var(--bg), var(--text) var(--dock-lift, 14%)) var(--dock-fill, 50%), transparent);
  backdrop-filter: blur(var(--dock-blur, 10px)) saturate(var(--dock-sat, 1.6));
  border: 1px solid color-mix(in srgb, var(--text) var(--dock-border, 24%), transparent);
}
.dock .text-muted, .dock input::placeholder {
  color: color-mix(in srgb, var(--text) var(--dock-text, 90%), var(--bg));
}
```

The tuner stores values in `localStorage`, has Reset and **Copy the values** (outputs `--dock-fill: 50%;` lines). When the person pastes them, bake them in as the CSS fallbacks, delete the tuner component and its mount in the dev tools, and say so. Include a **text contrast** and **text weight** slider whenever the chrome is translucent: low contrast of the text, not the blur, is usually the real readability problem.

A dev-only switch that previews a candidate on the real page (for example a "Mood: off / header / accents / page" button that sets `data-atmosphere` on the root element, with the CSS keyed on that attribute) is the same idea for choices of scope. Default it to off so nothing changes for anyone else.

## Analysing a reference

When the person drops a screenshot or a recording of a competitor or of their own app:

1. Extract frames: for a video, `ffmpeg -i video.webm -vf "fps=1/2,scale=720:-1,tile=3x3" -frames:v 1 sheet.png`, then single full-size frames with `ffmpeg -ss <t> -i video.webm -frames:v 1 frame.png`. A TIFF from the clipboard needs `sips -s format png in.tiff --out out.png` before it can be read.
2. Compare like for like: same data, same size. Write the differences as measurements (column width 145 against 190, visible strip 22 against 31, gutter, how many groups per row, what happens on hover) and rank them by how much they change the page, not by how easy they are to copy.
3. Turn the top differences into controls and a named preset ("Competitor-like"), keep the current look as a preset, and let the person compare.
4. Say what the other product does better and what it does worse. Do not copy features that do not fit the product.

## Performance and compatibility rules (learned the hard way)

Animated or heavy visuals in a lab must also be fast, because the lab is where the person first feels the design, and Safari is usually the slowest browser.

- Animate only `transform` and `opacity`. Collapse panels with the app's existing presence/height helper, not with layout animation.
- Avoid on animated or scrolling layers: CSS `filter: blur(...)`, `mix-blend-mode`, SVG `feTurbulence` noise overlays, large `backdrop-filter` stacks. These made a canvas lab drop to about 15 fps in Safari. Instead: pre-render glows at a fraction of the size and let the browser scale them up, bake scanlines/noise into the canvas as one `drawImage`, and use plain translucent overlays.
- Canvas: cap the device pixel ratio at 1.5 to 2, draw static layers (grid, lines) once into an off-screen canvas, batch fills (one `Path2D` per colour, not one fill per dot), cap to 30 fps for slow ambient motion, pause with `IntersectionObserver` when off-screen, and honour `prefers-reduced-motion`.
- Do not store continuously changing values (pointer position) in React state; use refs and read them in the animation loop.
- Wrap every `localStorage`, `sessionStorage` and clipboard call in try/catch.
- Keep `inert` on hidden fixed chrome so it cannot be tabbed into, and give it `pointer-events-none` while hidden.

## Verification

Do not hand a lab over unseen. Use a headless browser script that, for each preset and each colour scheme, loads the page, clicks the preset, optionally selects or hovers an item, and saves a screenshot. Then open the screenshots.

```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch()
    for scheme in ("dark", "light"):
        pg = b.new_context(viewport={"width": 1500, "height": 1000}, color_scheme=scheme).new_page()
        errs = []
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.goto("http://localhost:3000/dev/name-lab"); pg.wait_for_timeout(1500)
        for name in ("Current", "Compact", "Editorial"):
            pg.get_by_role("button", name=name, exact=True).first.click(); pg.wait_for_timeout(400)
            pg.screenshot(path=f"lab_{scheme}_{name}.png")
        print(scheme, errs)
    b.close()
```

Notes: use `.first` when a label appears both as a preset and as a control option; make a contact sheet with PIL when comparing many variants; test at a wide viewport (2000px) and a phone viewport (390px) for anything fixed or sticky; check that no console errors appear; check hover and selected states by actually hovering and clicking, not only the default render. State plainly what was and was not looked at.

For scripts that need a signed-in app, log in with a test account through the app's API in the same browser context, and use only seed/test data. Never put real credentials in a lab.

## Applying the result

1. Take the pasted JSON and map each key to the real component, one by one. List the mapping in your reply so the person can see nothing was dropped silently.
2. Keep the real component's accessibility and behaviour (keyboard, touch sizes, `aria-*`) even where the lab simplified it. Touch targets keep their larger coarse-pointer size.
3. Only the chosen options go in. Do not port the unchosen variants "just in case"; leave them in the lab.
4. If a chosen option needs data the real component does not have (card colours, a share count), compute it in the component, and say where it came from.
5. Re-run the type check and the tests, look at the real page in dark and light, and report with numbers (row height 34, radius 12).
6. If a decision is to be reused elsewhere (for example the selected-row style in two views), put it in one shared place.
7. Remove helpers that became unused (a colour helper, a tuner) unless the person wants them kept, and say which were kept.

## Style of the conversation

- Offer options in terms of what the person will see, not in code terms ("a glass pill that floats", "a halo around the row").
- After each round, say which combination you would pick and why, in one or two sentences, and what is still unverified (Safari, touch, light theme).
- When the person likes the settings but "wants other options" for one control, add more values to that one control (a new entry in the helper map) instead of building a new page.
- Keep the lab fast to load and free of dependencies beyond the app's own.
- Commit only when asked. Labs are development files; commit them in their own commit, apart from product changes.

## Checklist before saying "the lab is ready"

- [ ] Gated so it is a 404 in production.
- [ ] `CURRENT` reproduces today's product; presets start with it.
- [ ] Every control is on `Settings`; settings persist; Copy works.
- [ ] Controls are grouped, labelled, keyboard reachable, and use `aria-pressed`, `role="switch"`.
- [ ] Preview uses real tokens and components; both themes checked; wide and narrow checked when relevant.
- [ ] Mock data has long names, badges, uneven group sizes, and empty/zero cases.
- [ ] No blur filters, blend modes or SVG noise on animated layers; canvas rules followed.
- [ ] Screenshots of each preset were opened and looked at; weak spots are named in the hand-over.
- [ ] The hand-over ends with one clear request: paste the settings, or pick a preset.
