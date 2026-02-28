# choochoo-plugins

Single canonical source for choochoo plugins across all three backends: **Claude Code**, **Cursor**, and **Codex**.

## How it works

```
source/skills/*/SKILL.md   Canonical skill content with {{PLACEHOLDER}} and <!-- BEGIN:backend --> markers
config.toml                Per-backend metadata, placeholder values
generate.py                Reads source + config, writes backend-specific output in-place
```

One source skill produces three outputs:

| Source | Claude | Cursor | Codex |
|--------|--------|--------|-------|
| `install/SKILL.md` | `skills/install/SKILL.md` | `.cursor/skills/install/SKILL.md` | `codex/skills/choochoo-codex-install/SKILL.md` |
| `spec/SKILL.md` | `skills/spec/SKILL.md` | `.cursor/skills/spec/SKILL.md` | `codex/skills/choochoo-codex-spec/SKILL.md` |
| `pour/SKILL.md` | `skills/pour/SKILL.md` | `.cursor/skills/pour/SKILL.md` | `codex/skills/choochoo-codex-pour/SKILL.md` |

References co-located in a skill's `references/` directory are automatically copied next to the output.

## Usage

```bash
python3 generate.py
```

Requires Python 3.11+ (uses `tomllib`). No external dependencies.

## Editing plugins

Edit files in `source/skills/`, then run `generate.py`. Never edit the generated output directly.

### Placeholders

`{{KEY}}` is replaced with the value from `config.toml` under `[backend.placeholders]`.

```markdown
{{BACKEND_CHECK}}          # Multi-line substitution
{{INVOKE:spec}}            # Nested: looks up config.toml [backend.placeholders.INVOKE] spec
{{ASK_USER}}               # Simple substitution
```

### Conditional blocks

Include content for specific backends only:

```markdown
<!-- BEGIN:claude,cursor -->
This appears in Claude and Cursor output only.
<!-- END:claude,cursor -->

<!-- BEGIN:codex -->
This appears in Codex output only.
<!-- END:codex -->
```

Blocks can be nested. Inline conditionals within a single line also work:

```markdown
Some text<!-- BEGIN:claude --> with Claude-specific detail<!-- END:claude --> continues here.
```

### Config

`config.toml` defines per-backend:

- **headers** — YAML frontmatter fields (description, argument-hint, etc.)
- **placeholders** — substitution values

Set `skip = true` on a header to skip generating that skill for a backend.
Set `output_name` to override the default output directory name (Codex).

## Repo structure

```
choochoo-plugins/
  source/                   # Canonical content (edit these)
    skills/
      install/SKILL.md
      spec/SKILL.md
      spec/references/      # Co-located references (auto-copied to output)
      pour/SKILL.md
      pour/references/
    formulas/               # Shared formula files
  templates/                # Backend-specific static files (copied as-is)
    codex/
  config.toml               # Build configuration
  generate.py               # Build script
  skills/                   # Generated: Claude skills
  .cursor/                  # Generated: Cursor skills
  codex/                    # Generated: Codex skills
  formulas/                 # Generated: Claude formulas
  .claude-plugin/           # Generated: Claude plugin manifests
  .claude/                  # Generated: Claude settings
```
