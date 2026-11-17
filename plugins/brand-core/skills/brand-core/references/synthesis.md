# Synthesis: the core, the conflicts, the decisions

## The core

### Palette, three ways

Show three rows side by side, each swatch with name, hex and a one-line note (share of pixels, "= sheet step 4", "not in the sheet"):

1. **Declared**: from the guideline sheet, **sampled from the drawn swatches** (measure.py swatch), with the label noted when it differs.
2. **Used**: from the published pieces: the dominant k-means centers plus every measured accent (measure.py accent).
3. **Referenced**: from the boards: k-means per board (outliers excluded), merged into a short list of 6-8 families with the board that contributes most.

Then write the **reading** in 2-4 sentences: where the three agree (that is the brand); what the pieces use that the sheet never wrote down (usually the accent); which colors are in the sheet and the pieces but on no board (brand-owned, not borrowed); what the boards add (often warm paper grounds).

Ramps (5 steps per color) go under the guideline section when the sheet has them; check whether a ramp step is the exact fill used in the published pieces.

### Type as roles

Describe type by **what it does**, not by font name, then name the face for each role:

| Role | Carries | Usual treatment |
|---|---|---|
| Statement | facts, names, numbers | grotesk, heavy, tight |
| Observation | the line the reader remembers | serif italic |
| Metadata | dates, codes, prices, counters | mono, caps or small |
| Annotation | an aside, one per piece | script or handwriting, with an arrow |

When the declared face and the published face differ, show both samples in the same role and point at the decision. When a face is not licensed or not on Google Fonts, show a stand-in and say so.

### Photography "worlds"

Group photography into 2-3 worlds (city, nature, product, people at home...). For each: the source, measured stats as pills (L*, b* with warm share, muted share, the dominant ratio), three bullets (subjects and light; how people appear; grain, lens, finish), and four references. Measured stats beat adjectives: "L* 44, 64% warm, 55% muted" says "low-key, warm, film-like" with evidence.

### Repeating devices

What makes a piece recognisable without the logo: a line device, card shapes and highlight bars, ephemera that carries data (tickets, labels, notebook pages), a texture. For each, a small drawn specimen (SVG or CSS), where it already appears in the published pieces, and 2-3 references. A device only counts if it repeats.

### Logo or mascot

What the mark already does (where, at what size, which slides) and whether anything in the references asks for more. Turning a lockup into a character is a decision, not a finding.

## Conflicts

One card per disagreement, each with two labeled sides and a proposal:

- **written** (docs) vs **drawn** (guideline sheet) vs **published** (pieces) vs **referenced** (boards);
- the side labels name the real source ("sheet", "launch notes", "published · boards");
- measured values on both sides (hex, L*, b*, counts);
- **Proposal:** one line.

Typical conflicts: several palettes on paper but one in use; the accent (declared one value, published another, boards a third, and the declared one appearing in 0 of N items); the serif; photo temperature (docs say "cool", measured b* says warm); shadows declared but used nowhere; the product shown in old pieces vs the current offer.

## Decisions

Few and ordered: **3 to 5**, each one something only the person can decide, ordered by **what it unblocks** (the palette unblocks every template; a tagline unblocks less).

Each decision has:

- a question and one line of context;
- 2-4 options, each with a one-line consequence;
- a **recommendation grounded in the evidence** on the page ("used in all three published posts; 11:1 on the dark fill"), marked `rec: true`;
- `unblocks`: what work starts once it is decided.

Do not turn every conflict into a decision: if the evidence settles it, make it a proposal in the conflicts section. Do not ask for decisions the person cannot make yet.

Hand-off: ask **decision 01 only**. The rest follow once the first is settled.
