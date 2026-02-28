---
name: choochoo-codex-pour
description: Convert ready choochoo spec tasks into beads using formulas or singular tasks. Use when asked to pour specs into executable Ralph work.
---

# Pour into Beads

> For background on Choo! Choo! concepts, workflows, and commands, see `references/choochoo-guide.md`.

Create beads from ready tasks in a spec file, or directly from conversation context.

## Load reference first

Read `references/acceptance-criteria.md` before generating acceptance criteria.

## Inputs

- Optional target task count
- Optional spec file/name
- Optional formula name

## Spec File Resolution

When `spec_name` is provided:

- If it's a path (contains `/` or ends in `.md`): use directly
- If it's just a name: look for `.choochoo/{spec_name}.spec.md`

When `spec_name` is NOT provided:

1. **Check for existing specs** in `.choochoo/*.spec.md`
2. **If exactly one spec exists**: Use that spec automatically
3. **If multiple specs exist**: Ask user which spec to pour
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
2. **Ask user** before proceeding:
   - Pour directly - Create beads immediately from these tasks
   - Create spec first (Recommended) - Run spec skill for reviewable task breakdown
   - Cancel - Stop without creating anything
3. **Wait for user response** before taking any action

## Workflow Mode Selection

After determining the source (spec file or conversation), ask the user how they want to pour:

- **Use workflow formula (Recommended)** - Multi-step workflow with structured phases (design, implement, review, test, submit). The runner handles git commits and beads lifecycle. Best for production features.
- **Create singular tasks** - Simple beads executed directly. Good for exploratory work, research, prototyping, or one-off tasks.

**If "Use workflow formula"**: Proceed to Formula Selection below.

**If "Create singular tasks"**: Skip Formula Selection entirely and go straight to task breakdown.

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

### Target Implementation Tasks

If `target_tasks` is provided (e.g., 80):

- This is the target number of **implementation tasks (molecules)**, NOT spec tasks
- Break down spec tasks to reach this target

### Default Targets (Guidance)

If `target_tasks` is NOT provided, use these defaults:

| Project Type     | Target Molecules | Breakdown Ratio     |
| ---------------- | ---------------- | ------------------- |
| Single feature   | 15-30 tasks      | ~5-10 per spec task |
| Feature set      | 50-100 tasks     | ~5-8 per spec task  |
| Full application | 150-300 tasks    | ~5-10 per spec task |

### What Makes a Good Implementation Task

Each implementation task (molecule) should be a **coherent slice of work**:

- **Cohesive**: All changes belong together logically
- **Testable together**: Can be verified as a unit
- **Complete slice**: Delivers a piece of functionality, not just a layer or file change
- **Reasonable scope**: Not so big it's hard to review, not so small it's wasteful

## Acceptance Criteria Generation

When pouring spec tasks into beads, **generate acceptance criteria** for each bead. These are set on the root bead via `bd update --acceptance` and are executed by the runner after the agent finishes.

### Acceptance Criteria Complexity

| Task Type        | Checks | Examples                                         |
| ---------------- | ------ | ------------------------------------------------ |
| Simple/focused   | 2-3    | File exists, test suite passes                   |
| Standard feature | 3-5    | Tests pass, file exists, no old references       |
| Complex workflow | 5-8    | Multiple test files, build passes, lint passes   |

### Acceptance Criteria Format (REQUIRED)

**Format:** Newline-separated shell commands, same as the body of a shell script.

**Format rules:**

- One command per line
- Each line is passed to `sh -c`; passes if exit code is 0
- Blank lines are ignored
- Pipes and `&&` work
- Use `test -f <path>` to check file existence, `test ! -f <path>` for absence

## Ask before pouring

Present summary and require confirmation:

- spec task count
- estimated implementation task count
- mode (`workflow formula` or `singular`)
- formula name when relevant

Options:
- Pour all tasks (Recommended) - Proceed with pouring
- Show task overview first - Save preview to `.choochoo/pour-preview.md`
- Cancel - Stop without pouring

Do not pour until user confirms.

## Pour tasks sequentially

For each implementation task, run the pour command, then immediately set its acceptance criteria and priority. Do NOT use sub-agents — pour all tasks yourself, sequentially.

> **Important: Do NOT set `--assignee` during pour.** The runner discovers unassigned
> molecules via `bd ready` and claims them with `bd update <id> --claim`, which
> atomically sets `assignee = ralph-choochoo` and `status = in_progress`.
> Pre-assigning would prevent the runner from finding the bead.

   **For workflow formula mode**, each task requires two commands:

   **Step A — Create the molecule:**

   ```bash
   bd mol pour <FORMULA_NAME> \
     --var title="<TASK_TITLE>" \
     --var task="<TASK_DESCRIPTION>" \
     --var category="<TASK_CATEGORY>"
   ```

   **Capture the root bead ID** from the output (e.g. `proj-mol-abc`).

   **Step B — Set acceptance criteria and priority on the root bead:**

   ```bash
   bd update <ROOT_BEAD_ID> \
     --acceptance "<ACCEPTANCE_CRITERIA>" \
     --priority <TASK_PRIORITY>
   ```

   Notes for formula mode:

   - Use `bd mol pour` (not `bd formula pour`)
   - Use `--var` for variables (not `--set`)
   - `<TASK_DESCRIPTION>` is the task description only — do NOT append test steps to it
   - `<TASK_CATEGORY>` comes from the spec task's category attribute
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

   ### Singular Task Description Template

   For singular tasks, wrap the task description with execution instructions:

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

## Spec updates

After successful pour:

1. Update frontmatter `poured` with all created root bead IDs.
2. Archive spec to `.choochoo/archive/`.

If any step fails mid-pour:

- Stop immediately.
- Report created IDs + failure details.
- Do not archive spec.

## Handling Review Comments

If any tasks have content in `<review>` tags, warn the user and offer:
- Run spec skill first (Recommended) - Process review feedback before pouring
- Ignore and pour all - Pour tasks as-is
- Cancel - Stop and let user review manually

## Output

Summary differs based on workflow mode:

**For workflow formula mode:**

- N tasks poured using <FORMULA_NAME> formula
- Root bead IDs for each
- Total beads created (tasks × formula steps)
- Command to start: `choochoo`

**For singular task mode:**

- N singular tasks created
- Bead IDs for each
- Command to start: `choochoo`
