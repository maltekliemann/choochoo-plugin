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

### Agent execution context

When the runner launches you to work on a molecule:

- **You are on an isolated git worktree.** Your working directory is a separate
  copy of the repo, not the main checkout. Do NOT run `git add` or `git commit` —
  the runner handles all git operations.

- **Read the root bead first** (`bd show <mol-root-id> --json`). Check:
  - `description` — what to build
  - `acceptance_criteria` — the exact CI commands the runner will execute to verify
    your work. If they fail, the runner retries with a fresh agent.

- **Check for previous verification errors** (`bd comments <mol-root-id> --json`).
  If previous attempts failed, the runner injected the exact error details
  (command, exit code, stdout, stderr) into the comments. Read these carefully to
  avoid repeating the same mistake.

- **Do NOT** run `git add`, `git commit`, or `git push` — the runner handles all git.
- **Do NOT** close the root bead (`bd close <mol-root-id>`) — the runner closes it after merge. You only close step beads.
- **Do NOT** run `bd sync` — the runner manages bead synchronization.

- **Dependency chain.** Molecules are chained in a single linear compound:
  A → B → C → ... Each molecule blocks the next. You only see the current
  molecule — previous ones are already merged into the branch.
