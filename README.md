# Prototype | Design-Lab

**A skill for Claude Code that turns "make it a bit tighter… no, a bit less" into one round of "here's what I picked."**

When you ask Claude to design a piece of interface (a list, a card, a toolbar, a table row), the hard part is rarely the code. It's taste: spacing, density, how selection looks, how a heading reads. You can't name the answer, but you'll recognise it.

**Design-Lab** makes Claude build a **development-only lab page** for that component:

- the real component, with made-up data that exposes edge cases (long names, empty states, uneven groups);
- every design decision on a control: sliders, switches, segmented choices;
- **presets**, always starting with **Current** (what ships today);
- a **Copy settings** button.

You play until it feels right, paste the JSON back in chat, and Claude builds the real component from those exact values.

```
You:    make a lab for the order list
Claude: → /dev/order-list-lab  (Layout · Rows · Content · Heading · Mode, 5 presets)
You:    { "rowH": 34, "divider": "none", "hover": "bar", "selected": "outline", ... }
Claude: Applied to OrderList.tsx: row height 34, no dividers, edge-bar hover, …
        Left out (not chosen): zebra, table mode.
```

## What the skill teaches Claude

- **When to use a lab** and when a lighter step fits better. The ladder is: concept page (pick a direction) → lab (tune it) → tuner (CSS variables live on the real page, for glass, blur and anything that depends on what's behind it).
- **Page anatomy:**
  - gated so it 404s in production;
  - one typed `Settings` object;
  - `localStorage` persistence that survives new keys;
  - three tiny, accessible control primitives (`Seg`, `Slide`, `Flag`).
- **Control vocabulary** for lists, card stacks and floating bars.
- **Analysing a reference:** extract frames from a competitor's screenshot or recording, measure the differences, and turn them into a preset.
- **Performance rules** learned in Safari: no blur filters, blend modes or SVG noise on animated layers; canvas tips.
- **Verification:** Claude takes headless screenshots of every preset in dark and light themes and looks at them before handing over.
- **Applying the result:** maps each key back to the real component and lists what was applied and what was left out.

## Install

### Option A: as a Claude Code plugin (recommended)

Inside Claude Code:

```
/plugin marketplace add prototype-ro/prototype-design-lab
/plugin install design-lab@prototype
```

Update later with `/plugin marketplace update prototype`.

### Option B: copy the skill folder

For your user (all projects):

```bash
git clone https://github.com/prototype-ro/prototype-design-lab.git /tmp/design-lab
mkdir -p ~/.claude/skills
cp -r /tmp/design-lab/skills/design-lab ~/.claude/skills/
```

For a single project (commit it so your team gets it too):

```bash
mkdir -p .claude/skills
cp -r /tmp/design-lab/skills/design-lab .claude/skills/
```

Restart Claude Code, or start a new session, so the skill is picked up.

### Other agents

The skill is a single `SKILL.md` that follows the [Agent Skills](https://agentskills.io) format. Any agent that reads skills can use it: drop the `design-lab` folder wherever that agent looks for skills.

## Use

Claude loads the skill automatically when you say things like:

- "make a lab for the deck list"
- "give me options to test for the product card"
- "I want a playground to tweak the sidebar"
- "here's a screenshot of a competitor. Compare it with ours"

Or call it directly: `/design-lab` (or `/design-lab:design-lab` when installed as a plugin).

**The loop:**

1. Claude reads your real component and tokens, lists every decision, and builds `/dev/<name>-lab`.
2. Claude screenshots each preset in dark and light, fixes what looks off, and sends you the URL.
3. You play, then press **Copy settings** and paste the JSON in chat.
4. Claude applies it to the real component, runs the checks, and tells you exactly what changed.
5. When the design is settled, Claude offers to delete the lab. It never ships.

**Tips:**

- Not sure about the direction yet? Ask for a **concept page** first ("show me 3 directions for the header").
- Like everything except one control? Say "more options for the selected style". Claude adds values to that one control instead of rebuilding the page.
- For translucent chrome (a glass dock over content), ask for a **tuner** instead of a lab.

## Requirements

- Claude Code (or any agent that supports skills).
- A web project with a dev server. The examples use React, Next.js and Tailwind, but the method is stack-agnostic, and Claude translates the snippets to your framework.
- Optional: [Playwright](https://playwright.dev) (`pip install playwright && playwright install chromium`), so Claude can screenshot presets to check its own work.

## Structure

```
.claude-plugin/
  plugin.json        plugin manifest
  marketplace.json   lets `/plugin marketplace add` find it
skills/design-lab/
  SKILL.md           the skill itself
```

## Contributing

Issues and PRs are welcome, especially new control vocabularies (forms, charts, navigation) and ports of the snippets to other stacks.

## License

[MIT](LICENSE)

---

### Em português

**Prototype | Design-Lab** é uma skill para o Claude Code. Em vez de várias rodadas de "deixa um pouco mais apertado", ele monta uma **página de laboratório** só para desenvolvimento. Nela você ajusta o componente real com controles deslizantes, chaves e presets, copia as configurações e cola no chat, e o componente final é construído com exatamente esses valores.

Para instalar, rode `/plugin marketplace add prototype-ro/prototype-design-lab` e depois `/plugin install design-lab@prototype`. Outra opção é copiar `skills/design-lab` para `~/.claude/skills/`.
