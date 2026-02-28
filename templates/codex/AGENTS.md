## Skills

Use these Codex skills for the choochoo workflow.

### Available skills

- `choochoo-codex-install`: Install and initialize choochoo in a repository (file: `choochoo-codex/skills/choochoo-codex-install/SKILL.md`)
- `choochoo-codex-spec`: Generate or refine `.choochoo/*.spec.md` files (file: `choochoo-codex/skills/choochoo-codex-spec/SKILL.md`)
- `choochoo-codex-pour`: Convert ready spec tasks into beads with acceptance checks (file: `choochoo-codex/skills/choochoo-codex-pour/SKILL.md`)
- `choochoo-codex-ralph`: Run and operate Ralph loops, monitor progress, and recover failures (file: `choochoo-codex/skills/choochoo-codex-ralph/SKILL.md`)

### Trigger rules

- Use `choochoo-codex-install` for setup, bootstrap, prerequisites, or formula install requests.
- Use `choochoo-codex-spec` when asked to create, update, or review a choochoo spec.
- Use `choochoo-codex-pour` when asked to create beads from a spec or convert tasks to executable work.
- Use `choochoo-codex-ralph` when asked to run Ralph, inspect loop status, or debug blocked retries.

### Coordination

- Use the smallest set of skills that fully covers the request.
- For end-to-end execution, typical order is: `install` -> `spec` -> `pour` -> `ralph`.
- Ask the user before large irreversible actions (bulk pour, deletion, overwrite).
