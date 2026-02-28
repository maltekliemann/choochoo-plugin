---
description: Install choochoo into the current project
---

# Install choochoo

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

Before installing, check which files already exist:
- `.beads/formulas/choochoo.formula.toml`

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

2. **Set up formulas directory**:
   ```
   mkdir -p .beads/formulas
   cp "${CLAUDE_PLUGIN_ROOT}/formulas/choochoo.formula.toml" .beads/formulas/
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

## Recommended Plugins

1. **Check dev-browser plugin**: Check your available skills for `dev-browser`
   - If not available, recommend installing it for browser-based smoke tests and UI verification
   - GitHub: https://github.com/SawyerHood/dev-browser
   - This plugin is used by the bearings step (smoke test) and verify step (UI verification)

## Output

Report what was installed (and what was skipped if applicable):

- Python package: choochoo (CLI available as `choochoo`)
- Formulas: .beads/formulas/choochoo.formula.toml
- Spec directory: .choochoo/

Explain next steps:

1. Use `/choochoo:spec` to generate a spec from your plan
2. Review and approve features in the spec
3. Use `/choochoo:pour` to create beads
4. Run `choochoo` to start the autonomous loop
