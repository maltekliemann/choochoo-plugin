# choochoo-plugins

Single canonical source for choochoo plugins across all three backends: **Claude Code**, **Cursor**, and **Codex**.

## How it works

```
source/*.md          Canonical plugin content with {{PLACEHOLDER}} and <!-- BEGIN:backend --> markers
config.toml          Per-backend metadata, placeholder values, output paths
generate.py          Reads source + config, writes backend-specific output in-place
```

One source file produces three outputs:

| Source | Claude | Cursor | Codex |
|--------|--------|--------|-------|
| `install.md` | `commands/install.md` | `.cursor/skills/install/SKILL.md` | `codex/skills/choochoo-codex-install/SKILL.md` |
| `spec.md` | `commands/spec.md` | `.cursor/skills/spec/SKILL.md` | `codex/skills/choochoo-codex-spec/SKILL.md` |
| `pour.md` | `commands/pour.md` | `.cursor/skills/pour/SKILL.md` | `codex/skills/choochoo-codex-pour/SKILL.md` |
| `ralph-guide.md` | `skills/ralph-guide/SKILL.md` | `.cursor/skills/ralph-guide/SKILL.md` | `codex/skills/choochoo-codex-ralph/SKILL.md` |
| `spec-generation.md` | `skills/spec-generation/SKILL.md` | `.cursor/skills/spec-generation/SKILL.md` | _(skipped)_ |

## Usage

```bash
python3 generate.py
```

Requires Python 3.11+ (uses `tomllib`). No external dependencies.

## Editing plugins

Edit files in `source/`, then run `generate.py`. Never edit the generated output directly.

### Placeholders

`{{KEY}}` is replaced with the value from `config.toml` under `[backend.placeholders]`.

```markdown
{{BACKEND_CHECK}}          # Multi-line substitution
{{INVOKE:spec}}            # Nested: looks up config.toml [backend.placeholders.INVOKE] spec
{{REFS:anthropic-spec-format}}  # Nested: looks up [backend.placeholders.REFS]
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
- **references** — which reference files go where

Set `skip = true` on a header to skip generating that file for a backend.
Set `output_name` to override the default output directory name.

## Repo structure

```
choochoo-plugins/
  source/                   # Canonical content (edit these)
    install.md
    spec.md
    pour.md
    ralph-guide.md
    spec-generation.md
    formulas/               # Shared formula files
    references/             # Shared reference docs
  templates/                # Backend-specific static files (copied as-is)
    codex/
  config.toml               # Build configuration
  generate.py               # Build script
  commands/                 # Generated: Claude commands
  skills/                   # Generated: Claude skills
  .cursor/                  # Generated: Cursor skills
  codex/                    # Generated: Codex skills
  .claude-plugin/           # Generated: Claude plugin manifests
  .claude/                  # Generated: Claude settings
```
