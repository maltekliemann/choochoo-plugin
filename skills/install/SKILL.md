---
name: install
description: Install choochoo into the current project
---

# Install choochoo

> For background on Choo! Choo! concepts, workflows, and commands, see `references/choochoo-guide.md`.

Set up the Ralph autonomous coding workflow in this project.

## Pre-requisites Check

1. **Check beads CLI**: Run `bd --version`
   - If not installed: "Please install beads first. See: https://github.com/steveyegge/beads"

2. **Check Claude CLI**: Run `claude --version`
   - If not installed: Warn user they'll need it to run Ralph

3. **Check jq**: Run `jq --version`
   - If not installed: "Please install jq for JSON parsing. See: https://jqlang.github.io/jq/"

4. **Check Python 3.10+**: Run `python3 --version`
   - If python3 is not found: "Please install Python 3.10 or later. See: https://www.python.org/downloads/"
   - If installed, parse the version number from the output (e.g., "Python 3.12.3") and verify the major version is 3 and the minor version is >= 10
   - If version < 3.10: "Python 3.10+ is required but found <version>. Please upgrade: https://www.python.org/downloads/"

5. **Initialize beads**: If `.beads/` doesn't exist, run `bd init`

## Check for Existing Files

Before installing, check which bundled formula files already exist in `.beads/formulas/`.

**If ANY files exist**: Use AskUserQuestion to ask user for each existing file whether to:
- Skip (keep existing)
- Overwrite (replace with new version)

**If NO files exist**: Proceed directly to installation.

## Installation Steps

1. **Install the choochoo Python package**:
   ```
   pip install "${CLAUDE_PLUGIN_ROOT}/../runner/"
   ```
   - This installs the `choochoo` CLI from the runner/ directory
   - If `pip` is not available, try `pip3`
   - If install fails, show the error and suggest the user check their Python environment

2. **Copy formulas**:
   ```
   mkdir -p .beads/formulas
   cp "${CLAUDE_PLUGIN_ROOT}"/formulas/*.formula.toml .beads/formulas/
   ```

3. **Create spec directory**:
   ```bash
   mkdir -p .choochoo
   ```

4. **Inject Beads/Choo Choo agent instructions**:

   Append a Choo Choo section to the project's agent context file. This teaches the agent how to interact with Beads (A-type knowledge: `bd show`, `bd ready`, `bd close`, the molecule work loop, step lifecycle). This content is static and does not depend on the formula.

   - Target file: `CLAUDE.md` in project root
   - If the file doesn't exist, create it
   - If the file already contains a `## Choo Choo` section, ask user whether to skip or overwrite
   - Append the following section:

   ```markdown
   ## Choo Choo

   This project uses Choo! Choo! for autonomous coding. The runner launches agents
   to work through molecules (task units) composed of sequential steps.

   ### Beads Commands

   You interact with the task DB using the `bd` CLI:

   - `bd show <mol-root-id> --json` — Read the task description (root bead)
   - `bd ready --mol <mol-root-id> --json` — Find the next step to work on
   - `bd update <step-id> --status in_progress` — Claim a step
   - `bd close <step-id>` — Mark a step as complete
   - `bd update <step-id> --status blocked` — Mark a step as blocked

   ### Work Loop

   1. Read the root bead to understand what to build
   2. Query `bd ready` to find the next step
   3. Read the step description for phase-specific instructions
   4. Do the work described in the step
   5. Close the step with `bd close <step-id>`
   6. Repeat from step 2 until no more ready steps
   7. Exit when all steps are closed
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

   d. **Verify agent context**: Check that `CLAUDE.md` contains a `## Choo Choo` section
      - If missing: Record that agent instructions were not injected

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

## Recommended Plugins

1. **Check dev-browser plugin**: Check your available skills for `dev-browser`
   - If not available, recommend installing it for browser-based smoke tests and UI verification
   - GitHub: https://github.com/SawyerHood/dev-browser
   - This plugin is useful for browser-based smoke tests and UI verification during workflow steps

## Output

Report what was installed (and what was skipped if applicable):

- Python package: choochoo (CLI available as `choochoo`)
- Formulas: all bundled formulas copied to .beads/formulas/
- Spec directory: .choochoo/
- Agent context: Choo Choo section in CLAUDE.md

Explain next steps:

1. Use `/choochoo:spec` to generate a spec from your plan
2. Review and approve features in the spec
3. Use `/choochoo:pour` to create beads
4. Run `choochoo` to start the autonomous loop
