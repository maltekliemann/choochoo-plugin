---
name: choochoo-codex-install
description: Install and initialize choochoo in a repository for Codex-driven workflows. Use when asked to set up prerequisites, formulas, or project bootstrap.
---

# Install choochoo

Set up the Ralph autonomous coding workflow in this project.

## Pre-requisites Check

1. **Check beads CLI**: Run `bd --version`
   - If not installed: "Please install beads first. See: https://github.com/steveyegge/beads"

2. **Check jq**: Run `jq --version`
   - If not installed: "Please install jq for JSON parsing. See: https://jqlang.github.io/jq/"

3. **Check Python 3.10+**: Run `python3 --version`
   - If python3 is not found: "Please install Python 3.10 or later. See: https://www.python.org/downloads/"
   - If installed, parse the version number from the output (e.g., "Python 3.12.3") and verify the major version is 3 and the minor version is >= 10
   - If version < 3.10: "Python 3.10+ is required but found <version>. Please upgrade: https://www.python.org/downloads/"

4. **Initialize beads**: If `.beads/` doesn't exist, run `bd init`

## Check for Existing Files

Before installing, check which files already exist:
- `.beads/formulas/choochoo.formula.toml`

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

2. **Set up formulas directory**:
   ```bash
   mkdir -p .beads/formulas
   ```
   Copy the bundled formula template:
   ```bash
   FORMULA_SRC="$(find "${CODEX_HOME:-$HOME/.codex}/skills/choochoo-codex-install" -type f -name 'choochoo.formula.toml' | head -n1)"
   cp "${FORMULA_SRC}" .beads/formulas/choochoo.formula.toml
   ```

3. **Create spec directory**:
   ```bash
   mkdir -p .choochoo
   ```

4. **Verify installation**:

   Run each verification check below. Track which checks pass and which fail.

   a. **Verify CLI**: Run `choochoo --help`
      - If it succeeds (exit code 0): CLI verification passed
      - If it fails: Record error — "choochoo CLI is not available. The pip install may have failed or the package is not on $PATH."

   b. **Verify spec directory**: Check that `.choochoo/` exists
      - If it exists: Directory verification passed
      - If it does not exist: Create it with `mkdir -p .choochoo` and note it was created during verification

   c. **Verify formulas**: Run `bd formula list` and check the output
      - Verify `choochoo` appears in the output
      - If missing: Record that the formula is not registered

   d. **Print verification results**:

      **If ALL checks passed**, print a success summary:
      ```
      ✓ Installation verified successfully!

        ✓ CLI:        choochoo is available
        ✓ Directory:  .choochoo/ exists
        ✓ Formulas:   choochoo registered
      ```

      **If ANY check failed**, print an error summary:
      ```
      ✗ Installation verification failed:

        <✓ or ✗> CLI:        <status>
        <✓ or ✗> Directory:  <status>
        <✓ or ✗> Formulas:   <status for each>

      Please fix the issues above and re-run the install command.
      ```

## Output

Report what was installed (and what was skipped if applicable):

- Python package: choochoo (CLI available as `choochoo`)
- Formulas: .beads/formulas/choochoo.formula.toml
- Spec directory: .choochoo/

Explain next steps:

1. Use the spec skill to generate a spec from your plan
2. Review and approve features in the spec
3. Use the pour skill to create beads
4. Run `choochoo` to start the autonomous loop
