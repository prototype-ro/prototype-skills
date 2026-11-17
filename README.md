# Prototype Skills

Skills for [Claude Code](https://claude.com/claude-code) by **Prototype**, built while working on real products and published as a plugin marketplace.

## Install

Add the marketplace once:

```
/plugin marketplace add prototype-ro/prototype-skills
```

Then install whatever you want:

```
/plugin install design-lab@prototype
```

New skills show up after `/plugin marketplace update prototype`.

## Skills

| Skill | What it does | Install |
|---|---|---|
| [**Prototype \| Design-Lab**](plugins/design-lab) | Builds a dev-only lab page for a UI component, with sliders, switches and presets. You tune it live, paste the settings back, and the real component is built from them. | `/plugin install design-lab@prototype` |
| [**Prototype \| Brand-Core**](plugins/brand-core) | Turns your Pinterest boards, published posts and guideline sheet into one page that says what the brand looks like: palette, type, photography and a format map, measured in pixels, plus the conflicts between sources and a short list of decisions. | `/plugin install brand-core@prototype` |

## Without the plugin system

Every skill is a plain folder with a `SKILL.md`. Copy it into `~/.claude/skills/` (all projects) or `.claude/skills/` (one project), or into any agent that reads [Agent Skills](https://agentskills.io):

```bash
git clone https://github.com/prototype-ro/prototype-skills.git /tmp/prototype-skills
cp -r /tmp/prototype-skills/plugins/<skill>/skills/<skill> ~/.claude/skills/
```

## Layout

```
.claude-plugin/marketplace.json     the catalog (marketplace "prototype")
plugins/<name>/
  .claude-plugin/plugin.json        plugin manifest
  skills/<name>/SKILL.md            the skill
  README.md                         docs for that skill
```

Conventions: the plugin id is short kebab-case (`design-lab`), and the display name is `Prototype | Name` (`Prototype | Design-Lab`).

## License

[MIT](LICENSE)

---

**Em português:** coleção de skills para o Claude Code. Adicione o marketplace uma vez, com `/plugin marketplace add prototype-ro/prototype-skills`, e instale cada skill com `/plugin install <nome>@prototype`.
