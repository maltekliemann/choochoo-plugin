# Choo! Choo! System Guide

Reference guide for the Choo! Choo! autonomous coding system. Covers concepts,
workflows, commands, and troubleshooting.

## Overview

**Choo! Choo!** is a [Ralph Wiggum Toolset](https://ghuntley.com/ralph/) for
autonomous coding. It uses a dedicated runner to execute agent work through a
structured pipeline: **Pour** tasks into a DB, then **Loop** agents to complete
them.

Key characteristics:

- **Single-runner, one-agent-at-a-time** — no multi-agent orchestration
- **Beads DB** as persistent task storage (git-backed, distributed)
- **Git worktrees** for agent isolation — each task runs in its own worktree
- **Formula-driven workflows** — TOML files define the step sequence
- **Inspector + Refinery** — automated verification and merge gates
- **Multi-backend** — supports Claude Code, Cursor, and Codex

The flow is: write tests, go to bed, review 20k lines of code in the morning.

## Core Concepts

### Beads DB

The task database. Every task, step, and dependency is stored as a _bead_ — an
issue struct with `id`, `title`, `description`, `status`, `assignee`, and many
other fields. Beads are stored in `.beads/` and synced via git.

### Bead

The base unit. An issue struct in the Beads DB. Everything else (molecules,
steps, epics) is just a bead with certain fields set.

### Molecule

A **root bead** plus **child step beads** linked via `parent-child` dependencies.
Steps have `needs` fields for ordering. Created by pouring a formula.

- The root bead carries the task description (what to build)
- Step beads carry workflow phase instructions (how to work)
- Steps execute sequentially: step N+1 is blocked until step N closes

### Formula

A TOML file defining workflow steps. Gets "poured" into a molecule — each step
in the formula becomes a step bead under a root bead. The default `choochoo`
formula has five steps: `design` → `implement` → `review` → `test` → `submit`.

### Compound

A linear dependency chain of molecules linked by `blocks` dependencies. Choo!
Choo! processes one compound at a time. Only one molecule is unblocked at any
point — this is the compound's _cursor_.

### Step Lifecycle

```
open → in_progress → closed
```

Additional transitions used by the runner:

```
in_progress → blocked       (agent marks step as blocked)
in_progress → deferred      (agent defers step)
closed      → open          (Inspector reopens on verification failure)
blocked     → open          (Inspector reopens, vote below threshold)
deferred    → open          (Inspector reopens, vote below threshold)
```

### Molecule Lifecycle

1. **Pour** — `bd mol pour` creates root + step beads. All start `open`.
2. **Claim** — Runner claims root: `bd update <root> --claim` (sets
   `assignee = ralph-choochoo`, `status = in_progress`). Steps stay `open`.
3. **Work** — Agent works steps sequentially:
   - `bd ready --mol <root> --json` → find next step
   - `bd update <step> --status in_progress` → claim it
   - Do the work
   - `bd close <step>` → mark complete
   - Repeat until no more ready steps
4. **Complete** — All steps closed. Root bead closed after merge.

## The Workflow

The full end-to-end flow from idea to merged code.

### 1. Install

Run the install skill to set up Choo! Choo! in the project:

- Installs `choochoo` Python package (the runner CLI)
- Copies formula files to `.beads/formulas/`
- Creates `.choochoo/` spec directory
- Injects Beads/Choo Choo instructions into agent context file

### 2. Spec (Optional)

Generate a structured task breakdown from a plan:

- Output: `.choochoo/{name}.spec.md` with YAML frontmatter + XML task tags
- Each task has `id`, `priority`, `category`, `steps`, `test_steps`, `<review>`
- The `<review>` tag controls approval: empty = ready, content = needs revision

### 3. Review (Optional)

Iterate on the spec before pouring:

- Add feedback in `<review>` tags on any task
- Re-run the spec skill to process feedback
- AI regenerates affected tasks, clears review tags
- Repeat until all `<review>` tags are empty

### 4. Pour

Create molecules from ready tasks:

- Reads spec or conversation context
- Breaks high-level tasks into granular implementation tasks (molecules)
- Creates molecules via `bd mol pour` with acceptance criteria
- Chains them with `blocks` dependencies for ordering
- Archives spec after all tasks are poured

### 5. Run

Start the autonomous loop:

```bash
choochoo
```

The runner picks the next unblocked molecule, creates a worktree, launches an
agent, verifies the result, merges the work, and moves to the next molecule.

### Two Approaches

| Approach | Flow | Best for |
|----------|------|----------|
| **Spec → Beads** | Plan → Spec → Review → Pour → Run | Production features, careful planning |
| **Direct Pour** | Describe → Pour → Run | Quick tasks, prototyping |

## Spec Files

Specs are markdown files stored at `.choochoo/{name}.spec.md`. See
`spec-format.md` for the full format reference.

### YAML Frontmatter

```yaml
---
title: "Feature Name"
created: 2026-01-15
poured: []
iteration: 1
auto_discovery: false
auto_learnings: false
---
```

| Field | Description |
|-------|-------------|
| `title` | Human-readable name |
| `created` | Creation date |
| `poured` | Array of bead IDs created from this spec |
| `iteration` | Increments on each refinement cycle |
| `auto_discovery` | Enable auto-creation of gap tasks |
| `auto_learnings` | Enable auto-creation of learning skills |

### XML Task Structure

```xml
<project_specification>
  <project_name>Feature Name</project_name>
  <overview>Brief description</overview>
  <context>Background information</context>
  <tasks>
    <task id="task-id" priority="1" category="functional">
      <title>Task Title</title>
      <description>What to build</description>
      <steps>Implementation steps</steps>
      <test_steps>Verification steps</test_steps>
      <review></review>
    </task>
  </tasks>
</project_specification>
```

### Review Tags

| State | Tag | Meaning |
|-------|-----|---------|
| Ready | `<review></review>` | Approved, can be poured |
| Needs work | `<review>feedback here</review>` | Will be processed on next spec run |

## Pouring

How tasks become molecules in the Beads DB.

### Creating Molecules

For each implementation task:

```bash
# Step 1: Create the molecule (no assignee — the runner claims it later)
bd mol pour choochoo \
  --var title="Add login form" \
  --var task="Create login form with validation..." \
  --var category="functional"

# Step 2: Set acceptance criteria + priority
bd update <root-id> \
  --acceptance "pytest tests/test_login.py -q
test -f src/components/LoginForm.tsx" \
  --priority 1
```

Do NOT set `--assignee` during pour. The runner claims unassigned molecules via
`bd update <root> --claim`, which atomically sets `assignee = ralph-choochoo`
and `status = in_progress`. Pre-assigning would prevent the runner from finding
the bead.

### Acceptance Criteria

Verification commands set on the root bead via `bd update --acceptance`. The
runner executes these after the agent finishes. Each line is a shell command
passed to `sh -c`; the check passes if exit code is 0.

Format: newline-separated shell commands, same as the body of a shell script.

```
pytest tests/test_auth.py -q
mypy src/auth/ --no-error-summary
test -f src/auth/login.py
```

Pipes and `&&` work (commands run via `sh -c`). Blank lines are ignored.

### Task Ordering

Chain molecules with `blocks` dependencies:

```bash
bd dep add <mol-2> <mol-1> --type blocks   # mol-2 waits for mol-1
```

`bd ready` only surfaces unblocked molecules. When mol-1 closes, mol-2 unblocks.

### Singular vs Formula Mode

| Mode | Command | Use case |
|------|---------|----------|
| **Formula** | `bd mol pour <formula>` | Production features (structured workflow) |
| **Singular** | `bd create` | Exploratory work, one-off tasks |

Formula mode creates a molecule with workflow steps (design → implement →
review → test → submit). Singular mode creates a plain bead executed directly.

## The Runner

The `choochoo` CLI. Runs the autonomous loop.

### What It Does

1. **Pick compound** — queries `bd ready` for the next unblocked molecule
2. **Create worktree** — `git worktree add` for agent isolation
3. **Launch agent** — starts the agent subprocess with molecule root ID as prompt
4. **Agent works** — agent reads task via `bd show`, works through steps, closes
   each with `bd close`
5. **Inspector** — runs verification checks (acceptance criteria + global checks)
6. **Refinery** — merges worktree branch into feature branch (`--ff-only`)
7. **Cleanup** — removes worktree, closes completed molecules
8. **Next** — moves to next molecule in the compound

### Handoff

When the agent's context window fills up, the `PreCompact` hook signals the
runner. The runner kills the agent and relaunches with the same molecule root ID.
The new agent queries `bd ready` and picks up where the previous one left off —
completed steps are already closed in the DB.

Handoffs are unlimited. No state saving needed — the Beads DB IS the state.

### Inspector

Runs after agent exit when all steps are closed or a step is blocked.

**On completion (all steps closed):**

1. Run verification commands (global + per-molecule acceptance criteria)
2. Pass → proceed to Refinery
3. Fail → reopen steps, inject error into comments, retry with fresh agent
4. After N retries (`--max-retries`) → reject molecule, stop compound

**On blocked/deferred step:**

1. Record a vote for the molecule
2. Votes < threshold (`--block-threshold`) → reopen step, retry
3. Votes >= threshold → accept as genuinely stuck, stop compound

### Refinery (Merge Gate)

After Inspector passes:

1. `git merge --ff-only <worktree-branch>` — fast-forward into feature branch
2. Close molecule root bead: `bd close <root> --reason "merged"`
3. Remove worktree and delete branch (unless `--keep-worktrees`)

If merge fails (feature branch diverged) → fatal, compound stops. Worktree
left in place for manual conflict resolution.

### CLI Options

```
choochoo [compound]
  --keep-worktrees         Retain worktrees after success
  --never-keep-worktrees   Remove worktrees even on failure
  --log-dir <path>         Override log directory
  --quiet-agent            Suppress agent activity output
  --agent-args <args>      Extra args for agent backend
  --recover                Allow claiming in_progress molecules
  --timeout <duration>     Per-agent timeout (seconds)
  --backend <name>         Agent backend (claude, cursor, codex)
  --max-retries <n>        Inspector retries before rejecting
  --block-threshold <n>    Block votes before accepting as stuck
```

### Exit Diagnosis

How the runner diagnoses agent exit:

| Exit | Bead State | Diagnosis | Action |
|------|-----------|-----------|--------|
| SIGUSR1 | Steps remaining | **Handoff** | Relaunch same molecule |
| Exit 0 | All steps closed | **Completion** | Inspector |
| Exit 0 | Step blocked/deferred | **Blocked** | Inspector (vote) |
| Exit 0 | Steps remaining, none blocked | **Unexpected** | Stop compound |
| Timeout | Any | **Timeout** | Stop compound |
| Non-zero | Any | **Crash** | Stop compound |

## Beads Commands

Quick reference for the `bd` CLI.

### Task Management

| Command | Description |
|---------|-------------|
| `bd show <id> --json` | Read bead details (title, description, status) |
| `bd ready --json` | Find next unblocked, unassigned bead |
| `bd ready --mol <root-id> --json` | Find next ready step in a molecule |
| `bd update <id> --status <status>` | Change bead status |
| `bd update <id> --claim` | Atomically set assignee + in_progress |
| `bd close <id>` | Mark bead as closed |
| `bd close <id> --reason "text"` | Close with a reason |
| `bd create "title" --description "..."` | Create a new bead |
| `bd delete <id>` | Tombstone a bead |
| `bd comment <id> "text"` | Add a comment to a bead |

### Molecule Operations

| Command | Description |
|---------|-------------|
| `bd mol pour <formula> --var key="val"` | Create molecule from formula |
| `bd dep add <target> <blocker> --type blocks` | Add dependency |
| `bd formula list` | List available formulas |

### Status Values

`open`, `in_progress`, `blocked`, `deferred`, `closed`, `tombstone`

## Context Injection

The agent's context comes from four categories:

| Category | Content | Source |
|----------|---------|--------|
| **A — Beads/Choo Choo ops** | How to use `bd` commands, work loop, step lifecycle | Agent context file (CLAUDE.md / AGENTS.md) |
| **B — Workflow phases** | Phase instructions (design, implement, review, test, submit) | Step bead descriptions (from formula) |
| **C — Repository rules** | Coding standards, test commands, conventions | Agent context file (CLAUDE.md / AGENTS.md) |
| **D — Task context** | What to build, requirements, acceptance criteria | Root bead description |

Categories A and C live in the agent context file (injected once by install).
Category B is materialized into step beads at pour time (from the formula).
Category D is the root bead — the agent reads it via `bd show`.

This separation means:

- Custom formulas don't need to re-include Beads operational instructions
- Users can modify workflow phases without touching A-type knowledge
- The formula disappears after pouring — it's been materialized into beads

## Formulas

TOML files defining workflow steps. Stored in `.beads/formulas/`.

### The `choochoo` Formula (Default)

Five steps: `design` → `implement` → `review` → `test` → `submit`

- **design** — Read context, understand existing patterns, plan the approach
- **implement** — Make code changes, follow existing conventions
- **review** — Self-review the implementation for correctness
- **test** — Write and run tests, type checking, linting
- **submit** — Commit with a clear message

### Other Bundled Formulas

| Formula | Steps | Use case |
|---------|-------|----------|
| `shiny` | design → implement → review → test → submit | Gas Town-style full workflow |
| `shiny-enterprise` | Extends shiny, expands implement with rule-of-five | Complex tasks needing iterative implementation |
| `shiny-secure` | Shiny + security audit step | Security-sensitive work |
| `security-audit` | Dedicated security review | Standalone security assessment |
| `code-review` | Dedicated code review | Standalone review workflow |
| `design` | Dedicated design phase | Architecture and design work |

### Creating Custom Formulas

1. Create a TOML file in `.beads/formulas/`
2. Define `formula`, `description`, `type = "workflow"`, and `[[steps]]`
3. Each step needs `id`, `title`, `description`; use `needs` for ordering
4. Use `{{variable}}` for template substitution from `--var` flags
5. Pour with: `bd mol pour <your-formula> --var title="..." --var task="..."`

## Troubleshooting

### Inspector Rejects (Verification Failure)

**Symptom:** Agent completes all steps, but acceptance criteria fail. Runner
retries up to `--max-retries` times, then rejects.

**Fix:**
- Check the acceptance criteria on the root bead: `bd show <root-id> --json`
- Verify the checks are correct and achievable
- Check runner logs for the specific failing command
- Worktree is left in place — inspect the code manually

### Merge Conflicts

**Symptom:** Refinery fails with "Not possible to fast-forward."

**Cause:** Feature branch diverged (someone committed while the runner was
working).

**Fix:**
- Worktree is left in place at `worktrees/<mol-id>`
- Resolve the conflict manually in the worktree
- Merge and close the root bead: `bd close <root-id> --reason "merged"`

### Blocked Steps

**Symptom:** Agent marks a step as blocked. Runner retries with fresh agents.
After `--block-threshold` votes, accepts as genuinely stuck.

**Fix:**
- Check the bead comments for why agents are blocking: `bd show <step-id> --json`
- Address the underlying issue (missing dependency, unclear requirements)
- Reopen the step: `bd update <step-id> --status open`
- Re-run with `choochoo --recover`

### Agent Timeout

**Symptom:** Agent exceeds `--timeout` duration. Runner kills agent, compound
stops.

**Fix:**
- Increase timeout: `choochoo --timeout 3600`
- Break the task into smaller molecules
- Check if the agent is stuck in a loop (inspect logs)

### Crash Recovery

**Symptom:** Runner or agent crashed mid-molecule. Root bead is `in_progress`,
worktree exists.

**Fix:**
```bash
choochoo --recover
```

This allows claiming `in_progress` molecules. The runner skips worktree creation
(already exists) and launches a fresh agent that picks up remaining steps.

### No Work Available

**Symptom:** Runner exits with "No work available."

**Causes:**
- No molecules poured yet → run the pour skill
- All molecules already claimed → check with `bd ready --json`
- All molecules complete/tombstoned → pour new work

### Unexpected Agent Exit

**Symptom:** Agent exits cleanly (exit 0) but steps remain open and none are
blocked.

**Cause:** Agent exited without completing work or marking steps blocked. Treated
as a crash.

**Fix:**
- Inspect agent logs for what went wrong
- Re-run with `choochoo --recover`
