---
name: pour
description: Create Ralph beads from ready tasks in a spec file or conversation context
---

# Pour into Beads

> For background on Choo! Choo! concepts, workflows, and commands, see `references/choochoo-guide.md`.

## Arguments

<arguments>
  target_tasks = $1  <!-- Optional: target number of implementation tasks -->
  spec_name = $2     <!-- Optional: spec file name or path to pour from -->
  formula = $3       <!-- Optional: formula name to use (default: auto-detect) -->
</arguments>

Create beads from ready tasks in a spec file, or directly from conversation context.

## Spec File Resolution

When `spec_name` is provided:

- If it's a path (contains `/` or ends in `.md`): use directly
- If it's just a name: look for `.choochoo/{spec_name}.spec.md`

When `spec_name` is NOT provided:

1. **Check for existing specs** in `.choochoo/*.spec.md`
2. **If exactly one spec exists**: Use that spec automatically
3. **If multiple specs exist**: Ask user which spec to pour using AskUserQuestion
4. **If no specs exist**: Fall back to conversation mode

## Modes

### From Spec File (Recommended)

If spec file is found:

- Parse ready tasks (empty `<review>` tag)
- Skip tasks that need refinement (have content in `<review>` tag)
- Create one molecule per ready task
- Archive spec after pouring all tasks

### From Conversation (Quick Start)

If no spec file provided or found:

1. Extract tasks from conversation context
2. **STOP and use AskUserQuestion** - Do NOT proceed without user confirmation:

   ```
   Question: "No spec file found. How would you like to proceed with these tasks?"
   [List extracted tasks]

   Options:
   - Pour directly - Create beads immediately from these tasks
   - Create spec first (Recommended) - Run /choochoo:spec for reviewable task breakdown
   - Cancel - Stop without creating anything
   ```

3. **Wait for user response** before taking any action
4. If user chooses "Pour directly": create molecules from extracted tasks
5. If user chooses "Create spec first": run /choochoo:spec command
6. If user chooses "Cancel": stop and report cancellation

## Workflow Mode Selection

After determining the source (spec file or conversation), ask the user how they want to pour the tasks using **AskUserQuestion**:

```
Question: "How would you like to pour these tasks?"
Header: "Workflow"

Options:
- Use workflow formula (Recommended) - Multi-step workflow with structured phases (design, implement, review, test, submit). The runner handles git commits and beads lifecycle. Best for production features.
- Create singular tasks - Simple beads executed directly. Good for exploratory work, research, prototyping, or one-off tasks.
```

**If "Use workflow formula"**: Proceed to Formula Selection below.

**If "Create singular tasks"**: Skip Formula Selection entirely and go straight to task breakdown. Tasks will be created with `bd create` instead of `bd mol pour`.

## Formula Selection

**Note:** This section only applies when "Use workflow formula" is chosen above.

1. If `formula` provided, use that formula
2. Otherwise, run `bd formula list`:
   - If only one formula exists, use it automatically
   - If multiple formulas exist, ask user to choose

## Task Granularity (CRITICAL)

**Spec tasks are NOT implementation tasks.** Each spec task must be broken down into multiple granular implementation tasks (molecules).

### The Breakdown Process

1. **Spec tasks** = High-level features/capabilities from the spec
2. **Implementation tasks** = Granular, atomic units of work (molecules)
3. **Formula steps** = Workflow phases within each task (design, implement, review, test, submit) - these are NOT counted toward task granularity. Note: the runner handles git commits and beads lifecycle automatically.

**Example:**

- Spec has 10 high-level tasks
- Each spec task breaks down into 5-10 implementation tasks
- Target: 50-100 implementation tasks (molecules)
- Formula steps (5 per molecule) are internal workflow, NOT part of task count

### Target Implementation Tasks

If `target_tasks` is provided (e.g., 80):

- This is the target number of **implementation tasks (molecules)**, NOT spec tasks
- Break down spec tasks to reach this target
- A spec with 10 tasks targeting 80 molecules = ~8 implementation tasks per spec task

### Default Targets (Guidance)

If `target_tasks` is NOT provided, use these defaults:

| Project Type     | Target Molecules | Breakdown Ratio     |
| ---------------- | ---------------- | ------------------- |
| Single feature   | 15-30 tasks      | ~5-10 per spec task |
| Feature set      | 50-100 tasks     | ~5-8 per spec task  |
| Full application | 150-300 tasks    | ~5-10 per spec task |

### What Makes a Good Implementation Task

Each implementation task (molecule) should be a **coherent slice of work**:

- **Cohesive**: All changes belong together logically (e.g., frontend + backend for one feature slice is fine)
- **Testable together**: Can be verified as a unit - the changes make sense to test together
- **Complete slice**: Delivers a piece of functionality, not just a layer or file change
- **Reasonable scope**: Not so big it's hard to review, not so small it's wasteful

**TOO GRANULAR (bad):**

- "Install package X" then "Install package Y" then "Install package Z" as separate tasks
- "Update users.ts" then "Update users.test.ts" then "Update users.types.ts" as separate tasks
- Breaking apart changes that only make sense together

**TOO COARSE (bad):**

- "Build entire authentication system" (frontend + backend + infrastructure + tests all in one)
- Combining unrelated features into one task
- Tasks that would take hours to review

**JUST RIGHT:**

- "Add login form with validation" - includes component, styles, validation logic, tested together
- "Implement login API endpoint" - includes route, controller, validation, tests for that endpoint
- "Add password reset flow" - frontend + backend for this specific slice, can be tested end-to-end

**Key question:** Can this slice be implemented, committed, and tested as one coherent unit? If yes, it's the right size.

## Acceptance Criteria Generation

When pouring spec tasks into beads, **generate acceptance criteria** for each bead. These are set on the root bead via `bd update --acceptance` and are executed by the runner after the agent finishes.

- **Spec-level test steps** = Integration guidance (kept for reference in the spec)
- **Bead acceptance criteria** = Machine-checkable shell commands set on the root bead

### Acceptance Criteria Complexity (Important)

Use a **mix of complexity** based on the task:

| Task Type        | Checks | Examples                                           |
| ---------------- | ------ | -------------------------------------------------- |
| Simple/focused   | 2-3    | Test suite passes, linter passes                   |
| Standard feature | 3-5    | Tests pass, type checker passes, linter passes     |
| Complex workflow | 5-8    | Multiple test suites, build passes, lint passes    |

For each bead, generate acceptance criteria that:

1. Are specific to what this bead implements
2. Are shell commands (each line runs via `sh -c`)
3. Are machine-executable (no natural language)
4. Match complexity to task importance

### Acceptance Criteria Format (REQUIRED)

Write acceptance criteria as plain shell commands. The runner executes each line via `sh -c` after the agent finishes — if any command exits non-zero, the runner retries or blocks the task.

**Format:** Newline-separated shell commands, same as the body of a shell script.

**Format rules:**

- One command per line
- Each line is passed to `sh -c`; passes if exit code is 0
- Blank lines are ignored
- Pipes and `&&` work
- Only use CI commands: test suites, linters, type checkers, build steps
- Do NOT use `test -f` (file existence), `grep`, or anything outside of CI

**Execution environment:** Commands run in a bare shell (`sh -c`) with the worktree as the working directory. There is NO venv activation, no project-specific PATH, and no prior build step. You must account for this:

- Use `uv run <cmd>` (or equivalent) for project entry points and CLI tools installed via the project
- If the task produces a binary, install/build before testing it (e.g., `uv sync && uv run <cmd>`)
- Do not assume any tool is on PATH unless it's a standard system utility

**Example acceptance criteria:**
```bash
uv run pytest tests/test_auth.py -q
uv run mypy src/auth/ --no-error-summary
uv run ruff check src/auth/
```

**Example transformation:**

Spec task "User Authentication" with integration test steps might pour into:

- Bead: "Create login form component" → `npm test -- --run LoginForm && npm run lint`
- Bead: "Add form validation" → `npm test -- --run validation && npm run build`
- Bead: "Implement auth API endpoint" → `uv run pytest tests/test_auth_api.py -q && uv run mypy src/api/auth.py`

## Process

1. **Determine source**: Spec file or conversation
2. **Select workflow mode**: Ask user (see "Workflow Mode Selection" above):
   - If "Use workflow formula": proceed to step 3
   - If "Create singular tasks": skip to step 4 (no formula needed)
3. **Select formula** (workflow formula mode only): Use provided, auto-select, or prompt (see "Formula Selection" above)
4. **Parse spec tasks**: Extract high-level tasks from source
5. **Break down into implementation tasks** (CRITICAL):
   - Each spec task → multiple granular implementation tasks
   - Target 5-10 implementation tasks per spec task
   - Each implementation task = one molecule (or singular task)
   - See "Task Granularity" section above for guidance
6. **Generate acceptance criteria**: Create acceptance criteria for each implementation task (see Acceptance Criteria Generation above)
7. **Confirm with user** (AskUserQuestion):

   Present a summary and let user choose. The summary differs based on workflow mode:

   **For workflow formula mode:**
   ```
   "Ready to pour tasks from spec."

   Spec tasks: 27
   Implementation tasks: ~135 (after breakdown)
   Formula: choochoo (5 workflow steps each)

   Options:
   - Pour all tasks (Recommended) - Proceed with pouring
   - Show task overview first - Review all tasks before pouring
   - Cancel - Stop without pouring
   ```

   **For singular task mode:**
   ```
   "Ready to pour singular tasks from spec."

   Spec tasks: 27
   Implementation tasks: ~135 (after breakdown)
   Mode: Singular tasks (direct execution, no workflow steps)

   Options:
   - Pour all tasks (Recommended) - Proceed with pouring
   - Show task overview first - Review all tasks before pouring
   - Cancel - Stop without pouring
   ```

   **If "Show task overview first":**

   - Save full breakdown to `.choochoo/pour-preview.md`
   - Include: task title, description snippet, category, priority, acceptance criteria check count
   - Tell user: "Overview saved to .choochoo/pour-preview.md - review and run /choochoo:pour again when ready"
   - Exit without pouring

   **If "Cancel":** Exit without pouring

   **If "Pour all tasks":** Continue to step 8

8. **Pour tasks via batch script** (MANDATORY):

   You MUST generate a shell script (`.choochoo/pour-tasks.sh`) and run it. Never pour tasks by executing `bd` commands individually — always use the batch script. This is faster, reliable, and ensures correct chaining. Do NOT use sub-agents.

   The script should:
   - Define a `pour()` helper function that takes `feature`, `priority`, and `acceptance` arguments
   - The helper runs `bd mol pour` (or `bd create` for singular tasks), extracts the root bead ID from output, then runs `bd update` to set acceptance criteria and priority
   - Call `pour()` once per implementation task, **ordered by priority ascending**, then by spec order within the same priority
   - Use `set -e` so the script stops on first failure
   - After all tasks are poured, chain them into a linear compound using `bd dep add`
   - Print a summary at the end

   **Example script structure** (workflow formula mode):

   ```bash
   #!/bin/bash
   set -e

   POURED_IDS=()

   pour() {
     local feature="$1"
     local priority="$2"
     local acceptance="$3"

     echo ">>> Pouring: $feature"
     output=$(bd mol pour <FORMULA_NAME> --var feature="$feature" 2>&1)
     echo "$output"
     root_id=$(echo "$output" | grep "Root issue:" | sed 's/.*Root issue: //')
     if [ -z "$root_id" ]; then
       echo "ERROR: Failed to extract root ID for: $feature"
       exit 1
     fi
     bd update "$root_id" --title "$feature" --acceptance "$acceptance" --priority "$priority" 2>&1
     POURED_IDS+=("$root_id")
     echo "---"
   }

   pour "Add login form with validation" 1 \
   "uv run pytest tests/test_login.py -q
   uv run mypy src/components/auth/ --no-error-summary"

   pour "Implement auth API endpoint" 1 \
   "uv run pytest tests/test_auth_api.py -q
   uv run mypy src/api/ --no-error-summary"

   # ... one pour() call per implementation task ...
   # NOTE: pour tasks in priority order (ascending), then spec order within
   # the same priority. The chaining below assumes this ordering.

   # Chain molecules into a compound
   if [ ${#POURED_IDS[@]} -gt 1 ]; then
     echo ""
     echo "=== Chaining ${#POURED_IDS[@]} molecules into compound ==="
     for ((i=1; i<${#POURED_IDS[@]}; i++)); do
       bd dep add "${POURED_IDS[$i]}" "${POURED_IDS[$((i-1))]}" --type blocks
       echo "  ${POURED_IDS[$i]} waits for ${POURED_IDS[$((i-1))]}"
     done
   fi

   echo ""
   echo "=== DONE: ${#POURED_IDS[@]} molecules poured ==="
   printf '%s\n' "${POURED_IDS[@]}"
   ```

   After generating the script, run it with `bash .choochoo/pour-tasks.sh`. Parse the output to collect all root bead IDs for the spec frontmatter update. Clean up the script after a successful run.

   **For singular task mode**, the helper uses `bd create` instead:

   ```bash
   pour() {
     local title="$1"
     local description="$2"
     local priority="$3"
     local acceptance="$4"

     echo ">>> Creating: $title"
     output=$(bd create "$title" --description "$description" 2>&1)
     echo "$output"
     bead_id=$(echo "$output" | grep -oE '[a-z]+-[a-z0-9]+' | head -1)
     if [ -z "$bead_id" ]; then
       echo "ERROR: Failed to extract bead ID for: $title"
       exit 1
     fi
     bd update "$bead_id" --acceptance "$acceptance" --priority "$priority" 2>&1
     POURED_IDS+=("$bead_id")
     echo "---"
   }
   ```

> **Important: Do NOT set `--assignee` during pour.** The runner discovers unassigned
> molecules via `bd ready` and claims them with `bd update <id> --claim`, which
> atomically sets `assignee = ralph-choochoo` and `status = in_progress`.
> Pre-assigning would prevent the runner from finding the bead.

   **For workflow formula mode**, each task requires two commands (inside the `pour()` helper):

   **Step A — Create the molecule:**

   ```bash
   bd mol pour <FORMULA_NAME> \
     --var feature="<TASK_TITLE_AND_DESCRIPTION>"
   ```

   The `--var` names must match the formula's declared variables. Run `bd formula show <FORMULA_NAME>` to see which variables are required. Common variable names: `feature`, `title`, `task`, `assignee`. Pass only the variables the formula declares.

   **Capture the root bead ID** from the output (e.g. `proj-mol-abc`).

   **Step B — Set title, acceptance criteria, and priority on the root bead:**

   ```bash
   bd update <ROOT_BEAD_ID> \
     --title "<TASK_TITLE>" \
     --acceptance "<ACCEPTANCE_CRITERIA>" \
     --priority <TASK_PRIORITY>
   ```

   The `<ACCEPTANCE_CRITERIA>` is a newline-separated string of shell commands. The runner executes each line via `sh -c` after the agent finishes. See "Acceptance Criteria Format" above.

   **Complete example** (inside the batch script):

   ```bash
   pour "Add login form with validation" 1 \
   "uv run pytest tests/test_login.py -q
   uv run mypy src/components/auth/ --no-error-summary
   uv run ruff check src/components/auth/"
   ```

   Which expands to:

   ```bash
   bd mol pour shiny --var feature="Add login form with validation"
   # Output: Root issue: proj-mol-x7k
   bd update proj-mol-x7k --title "Add login form with validation" --acceptance "..." --priority 1
   ```

   **Placeholder notation:** `<PLACEHOLDER>` values are filled in by YOU (the agent) before running the command. These are NOT processed by beads — you must substitute them with actual values. In contrast, `{{variable}}` in formula files IS processed by beads templating.

   Notes for formula mode:

   - Use `bd mol pour` (not `bd formula pour`)
   - Use `--var` for variables (not `--set`)
   - Check formula variables with `bd formula show <name>` before generating the script — variable names vary by formula
   - Priority values: 0-4 (0=critical, 1=high, 2=medium, 3=low, 4=backlog)

   **For singular task mode**, each task also requires two commands:

   **Step A — Create the task:**

   ```bash
   bd create "<TASK_TITLE>" \
     --description "<TASK_DESCRIPTION_WITH_TEMPLATE>"
   ```

   **Step B — Set acceptance criteria and priority:**

   ```bash
   bd update <BEAD_ID> \
     --acceptance "<ACCEPTANCE_CRITERIA>" \
     --priority <TASK_PRIORITY>
   ```

   **Important:** `bd create` does NOT perform any template substitution. The `<PLACEHOLDER>` values must be filled in by YOU before running the command. Whatever string you pass to `--description` is stored exactly as-is.

   **How to construct `<TASK_DESCRIPTION_WITH_TEMPLATE>`:**
   1. Copy the **Singular Task Description Template** structure below
   2. Replace `<TASK_DESCRIPTION>` with the actual task description
   3. Pass the entire constructed string to `--description`

   Notes for singular task mode:

   - Use `bd create` (not `bd mol pour`)
   - **Capture the bead ID** from output

   ### Singular Task Description Template

   For singular tasks, wrap the task description with execution instructions. Fill in `<TASK_DESCRIPTION>` with actual content before creating:

   ```markdown
   ## Task
   <TASK_DESCRIPTION>

   ## Execution
   Execute this task directly. The runner handles git commits and beads lifecycle.

   1. Implement the changes
   2. Self-verify (run tests, type checks)
   3. Exit when done

   ## Constraints
   - Do NOT run `git add` or `git commit` — the runner handles git
   ```

9. **Collect bead IDs**: Parse the script output to collect all root bead IDs. Clean up the script: `rm .choochoo/pour-tasks.sh`
10. **Chain into compound**: The batch script chains all poured molecules into a single linear compound using `bd dep add`. The chain is: mol-1 → mol-2 → mol-3 → ... where each molecule blocks the next. Molecules are chained in pour order (by priority ascending, then spec order within the same priority). This ensures `bd ready` surfaces only one molecule at a time — the compound cursor.
11. **Update spec frontmatter**: After all tasks are poured successfully, update the spec's YAML frontmatter `poured` array with the created bead IDs (see below)
12. **Archive spec**: Move spec to archive folder after all tasks poured (see below)

## Error Recovery

If a pour or update command fails mid-way through the task list:

1. **Identify failed task**: Note which task failed and the error message
2. **Rollback partial state**: Delete any orphaned beads created for the failed task: `bd delete <partial-bead-id>`
3. **Report to user**:
   - List successfully poured tasks (with bead IDs)
   - Identify the failed task and error
   - Suggest fix or ask user for guidance
4. **Resume option**: User fixes the issue, then runs pour again (will re-pour all tasks since spec wasn't archived)

## Updating Spec Frontmatter

After all tasks are poured successfully, update the spec's YAML frontmatter with the bead IDs:

1. **Collect bead IDs** from each `bd mol pour` or `bd create` command output
2. **Update the `poured` array** in the frontmatter with all collected IDs

**Example before pour:**

```yaml
---
title: "User Authentication"
created: 2026-01-11
poured: []
---
```

**Example after pour:**

```yaml
---
title: "User Authentication"
created: 2026-01-11
poured:
  - proj-abc
  - proj-def
  - proj-ghi
---
```

This provides traceability from spec to beads, and allows querying which specs have been poured.

## Spec Archiving

After successfully pouring **all ready tasks** from a spec:

1. **Create archive directory** if it doesn't exist: `.choochoo/archive/`
2. **Move the spec file** to archive:
   - From: `.choochoo/my-feature.spec.md`
   - To: `.choochoo/archive/my-feature.spec.md`
3. **Report**: "Spec archived to .choochoo/archive/my-feature.spec.md"

**When NOT to archive:**

- If pour failed mid-way (spec stays in place for retry)
- If some tasks still need refinement (have content in `<review>` tags)
- If pouring from conversation (no spec file to archive)

The archived spec serves as a record of what was planned and poured, with bead IDs for traceability.

## Handling Review Comments

If any tasks have content in `<review>` tags, use **AskUserQuestion** to let the user decide:

```
"Some tasks have review comments that haven't been processed."

Options:
- Run /choochoo:spec first (Recommended) - Process review feedback before pouring
- Ignore and pour all - Pour tasks as-is, ignoring review comments
- Cancel - Stop and let me review the spec manually
```

**If user chooses "Run /choochoo:spec first":**

- Run the spec command to process review feedback
- After spec completes, continue with pour

**If user chooses "Ignore and pour all":**

- Clear all review tags (treat as empty)
- Pour all tasks
- Archive spec

**If user chooses "Cancel":**

- Report spec location for manual review
- Exit without pouring

## Output

Summary differs based on workflow mode:

**For workflow formula mode:**

- N tasks poured using <FORMULA_NAME> formula
- Root bead IDs for each
- Total beads created (tasks × formula steps)
- Compound chain created (N molecules linked)
- Command to start: `choochoo`

**For singular task mode:**

- N singular tasks created
- Bead IDs for each
- Compound chain created (N tasks linked)
- Command to start: `choochoo`
