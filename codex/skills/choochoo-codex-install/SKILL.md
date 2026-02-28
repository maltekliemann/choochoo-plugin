---
name: choochoo-codex-install
description: Install and initialize choochoo in a repository for Codex-driven workflows. Use when asked to set up prerequisites, formulas, or project bootstrap.
---

# Install choochoo

> For background on Choo! Choo! concepts, workflows, and commands, see `references/choochoo-guide.md`.

Set up the Ralph autonomous coding workflow in this project.

## Pre-requisites Check

1. **Check beads CLI**: Run `bd --version`
   - If not installed: "Please install beads (>= v0.58.0). Recommended: `brew install beads`. Alternatives: `npm install -g @beads/bd` or see https://github.com/steveyegge/beads/blob/main/docs/INSTALLING.md"
   - If installed, parse the version number from the output and verify it is >= 0.58.0 (the SQLite backend was removed in 0.58; older versions are not compatible)
   - If version < 0.58.0: "Beads >= v0.58.0 is required but found <version>. Please upgrade: `brew upgrade beads` or see https://github.com/steveyegge/beads/blob/main/docs/INSTALLING.md"

2. **Check Python 3.10+**: Run `python3 --version`
   - If python3 is not found: "Please install Python 3.10 or later. See: https://www.python.org/downloads/"
   - If installed, parse the version number from the output (e.g., "Python 3.12.3") and verify the major version is 3 and the minor version is >= 10
   - If version < 3.10: "Python 3.10+ is required but found <version>. Please upgrade: https://www.python.org/downloads/"

3. **Initialize beads**:
   - If `.beads/` doesn't exist: run `bd init`
   - If `.beads/` exists: run `bd list` to verify the database is accessible
     - If `bd list` fails with "database not found": the Dolt server is running but doesn't have a database for this project (the database name is derived from the directory name). Run `bd init --force` to create it.

## Check for Existing Files

Before installing, check which bundled formula files already exist in `.beads/formulas/`.

**If ANY files exist**: Ask user for each existing file whether to:
- Skip (keep existing)
- Overwrite (replace with new version)

**If NO files exist**: Proceed directly to installation.

## Installation Steps

1. **Install the choochoo Python package**:
   ```bash
   if ! command -v choochoo >/dev/null 2>&1; then
     if [ -d ./runner ]; then
       pip install ./runner
     elif [ -n "${CHOOCHOO_RUNNER_PATH:-}" ]; then
       pip install "${CHOOCHOO_RUNNER_PATH}"
     else
       echo "choochoo CLI not found and no runner path available"
     fi
   fi
   ```
   - If install fails, ask user for a runner source path and retry with `pip install <path>`

2. **Copy formulas**:
   ```bash
   mkdir -p .beads/formulas
   ```
   Copy all bundled formula files:
   ```bash
   FORMULA_DIR="$(find "${CODEX_HOME:-$HOME/.codex}/skills/choochoo-codex-install" -type d -name 'assets' | head -n1)"
   cp "${FORMULA_DIR}"/*.formula.toml .beads/formulas/
   ```

3. **Create spec directory and gitignore worktrees**:
   ```bash
   mkdir -p .choochoo
   ```
   Add `.choochoo/worktrees/` to `.gitignore` if not already present:
   ```bash
   grep -qxF '.choochoo/worktrees/' .gitignore 2>/dev/null || echo '.choochoo/worktrees/' >> .gitignore
   ```

4. **Inject Beads/Choo Choo agent instructions**:

   Append a Choo Choo section to the project's agent context file. This teaches the agent how to interact with Beads (A-type knowledge: `bd show`, `bd ready`, `bd close`, the molecule work loop, step lifecycle). This content is static and does not depend on the formula.

   - Target files: both `CLAUDE.md` and `AGENTS.md` in project root (different agent backends read different files, so both must exist with the same content)
   - For each target file: if the file doesn't exist, create it; if it already contains a `## Choo Choo` section, ask user whether to skip or overwrite
   - Append the following section to both files:

   ```markdown
   ## Choo Choo

   This project uses Choo! Choo! for autonomous coding. The runner launches agents
   to work through molecules (task units) composed of sequential steps.

   ### Environment

   You are running in an **isolated git worktree**, not the main checkout. Your
   working directory is a separate copy of the repo created just for this molecule.
   All your changes are committed and merged back automatically by the runner — do
   NOT run `git add` or `git commit`.

   ### Before You Start

   1. **Read the root bead** to understand what to build and what acceptance
      criteria you must satisfy:
      ```
      bd show <mol-root-id> --json
      ```
      Pay attention to the `acceptance_criteria` field — these are the exact shell
      commands the runner will execute to verify your work. If they fail, the runner
      retries with a fresh agent.

   2. **Check for previous verification errors.** If this molecule has been
      attempted before, the runner injected error details into the bead comments.
      Read them with:
      ```
      bd comments <mol-root-id> --json
      ```
      These tell you exactly what went wrong on the previous attempt so you can
      fix it instead of repeating the same mistake.

   ### Beads Commands

   You interact with the task DB using the `bd` CLI:

   - `bd show <mol-root-id> --json` — Read task description and acceptance criteria
   - `bd comments <mol-root-id> --json` — Read comments (includes verification errors from previous attempts)
   - `bd ready --mol <mol-root-id> --json` — Find the next step to work on
   - `bd update <step-id> --status in_progress` — Claim a step
   - `bd close <step-id>` — Mark a step as complete
   - `bd update <step-id> --status blocked` — Mark a step as blocked

   ### Work Loop

   1. Read the root bead (`bd show`) — check description and acceptance criteria
   2. Check comments (`bd comments`) — look for verification errors from prior attempts
   3. Query `bd ready` to find the next step
   4. Read the step description for phase-specific instructions
   5. Do the work described in the step
   6. Close the step with `bd close <step-id>`
   7. Repeat from step 3 until no more ready steps
   8. Exit when all steps are closed

   ### Important

   - **Commit your work** — `git add` and `git commit` when done.
   - **Do NOT `git push`** — the runner handles merge to main.
   - **Do NOT close the root bead** — the runner closes it after merge. You only close step beads.

   ### Dependency Chain

   Molecules are chained in a single linear compound: A → B → C → ...
   Each molecule blocks the next. The runner processes them one at a time. You only
   see the current molecule — previous ones are already merged.
   ```

5. **Verify installation**:

   Run each verification check below. Track which checks pass and which fail.

   a. **Verify CLI**: Run `choochoo --help`
      - If it succeeds (exit code 0): CLI verification passed
      - If it fails: Record error — "choochoo CLI is not available. The pip install may have failed or the package is not on $PATH."

   b. **Verify spec directory**: Check that `.choochoo/` exists
      - If it exists: Directory verification passed
      - If it does not exist: Create it with `mkdir -p .choochoo` and note it was created during verification

   c. **Verify formulas**: Run `bd formula list` and check that all bundled formulas appear
      - If any are missing: Record which formulas are not registered

   d. **Verify agent context**: Check that both `CLAUDE.md` and `AGENTS.md` contain a `## Choo Choo` section
      - If missing from either file: Record which file(s) are missing agent instructions

   e. **Print verification results**:

      **If ALL checks passed**, print a success summary:
      ```
      ✓ Installation verified successfully!

        ✓ CLI:             choochoo is available
        ✓ Directory:       .choochoo/ exists
        ✓ Formulas:        all registered
        ✓ Agent context:   Choo Choo section present
      ```

      **If ANY check failed**, print an error summary:
      ```
      ✗ Installation verification failed:

        <✓ or ✗> CLI:             <status>
        <✓ or ✗> Directory:       <status>
        <✓ or ✗> Formulas:        <N>/<total> registered
        <✓ or ✗> Agent context:   <status>

      Please fix the issues above and re-run the install command.
      ```

## Output

Report what was installed (and what was skipped if applicable):

- Python package: choochoo (CLI available as `choochoo`)
- Formulas: all bundled formulas copied to .beads/formulas/
- Spec directory: .choochoo/
- Agent context: Choo Choo section in both CLAUDE.md and AGENTS.md

Explain next steps:

1. Use the spec skill to generate a spec from your plan
2. Review and approve features in the spec
3. Use the pour skill to create beads
4. Run `choochoo` to start the autonomous loop
