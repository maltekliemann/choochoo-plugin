---
name: Ralph Guide
description: Guidance for customizing Ralph workflows, formulas, learning capture, and troubleshooting. Use for questions about Ralph loop, formulas, or running multiple Ralphs.
---

# Ralph Guide

Quick reference for operating choochoo across all workflow phases.

## The Workflow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   1. Plan   │ ──▶ │  2. Spec    │ ──▶ │  3. Pour    │ ──▶ │  4. Ralph   │
│    (you)    │     │  (you + AI) │     │    (AI)     │     │    (AI)     │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

1. **Plan** - Write what you want to build (this is on you)
2. **Spec** - AI transforms it into structured tasks; you review and refine
3. **Pour** - Tasks become beads (workflow or singular)
4. **Ralph** - The runner executes autonomously until done

See `docs/workflow.md` for the complete guide.

## Prerequisites & Safety

**Required:**
- [Claude Code](https://claude.com/claude-code) - Anthropic's CLI for agentic coding
- [Beads](https://github.com/steveyegge/beads) - Git-backed issue tracker (`bd` command)
- [jq](https://jqlang.github.io/jq/) - JSON parsing
- Python 3.10+

**Safety:** Ralph runs with `--dangerously-skip-permissions`. Run in a Docker container or VM, especially for untrusted codebases.

## Install

```bash
/choochoo:install
```

Creates local copies you can customize:

| File | Purpose |
|------|---------|
| `.beads/formulas/choochoo.formula.toml` | Standard workflow formula |
| `.choochoo/` | Spec file directory |

The install also installs the `choochoo` Python package (the runner CLI).

## Spec Phase

### Generate a Spec

```bash
/choochoo:spec [source-file] [spec-name]
```

- From plan file: `/choochoo:spec plans/my-feature.md`
- From conversation: `/choochoo:spec` (uses context)
- With explicit name: `/choochoo:spec plans/feature.md auth-system`

Specs are stored at `.choochoo/{spec-name}.spec.md`

### Spec Format

Tasks use XML-like tags with a review workflow:

```xml
<task id="add-login-form" priority="1" category="functional">
  <title>Add Login Form Component</title>
  <description>Create a reusable login form...</description>
  <steps>
    1. Create LoginForm component
    2. Add validation
  </steps>
  <test_steps>
    1. Verify form renders
    2. Test validation
  </test_steps>
  <review></review>  <!-- Empty = ready to pour -->
</task>
```

### Review Process

1. **Add feedback** in `<review>` tags:
   ```xml
   <review>Split this into two tasks: validation and submission</review>
   ```
2. **Run `/choochoo:spec` again** - AI processes feedback
3. **Repeat** until all `<review>` tags are empty

**Common review patterns:**
- Split: `<review>Split into: schema creation, indexes, migration</review>`
- Add detail: `<review>Add step for handling duplicate emails</review>`
- Remove: `<review>Remove - already exists in utils/</review>`
- Combine: `<review>Merge with task-xyz, too small separately</review>`

See `docs/spec-format.md` for complete format reference.

## Pour Phase

### Convert Spec to Beads

```bash
/choochoo:pour [target-tasks] [spec-file] [formula]
```

Examples:
- Auto-detect everything: `/choochoo:pour`
- Target 80 tasks: `/choochoo:pour 80`
- Specific spec and formula: `/choochoo:pour 80 auth-system choochoo`

### Modes

**Workflow Formula** (recommended) - Multi-step process per task:
```
bearings → implement → verify
```
The runner handles git commits and beads lifecycle automatically after verification passes.

**Singular Tasks** - Direct execution without phases (for research, prototyping)

### What Happens

1. Tasks created as beads in `.beads/issues/`
2. Spec's `poured` array updated with bead IDs
3. Spec archived to `.choochoo/archive/`
4. Tasks ready for Ralph

See `docs/commands.md` for all options.

## Ralph Loop

### Running Ralph

```bash
choochoo                    # Default iterations
choochoo --max-iterations 50  # Run up to 50 tasks
choochoo --verbose          # Detailed output
```

### How It Works (Runner v2)

The runner handles orchestration so the agent can focus on implementation:

```
Runner Loop:
  1. Pre-flight health check (configured commands + state.md staleness)
  2. Query beads → find next ready epic
  3. Claim epic (set status to in_progress)
  4. Build enriched prompt (task context, state.md, step descriptions)
  5. Launch agent → agent implements, writes result.json + state.md
  6. Read result.json → run hard verification
  7. Git commit as Ralph (cross-checked against actual changes)
  8. Close beads (steps + epic)
  9. Next iteration
```

Key insights:
- The **runner** handles git commits, beads lifecycle, and verification — not the agent
- The agent writes `result.json` (outcome, files_changed, commit_message) and `state.md` (persistent context)
- Verification failures trigger automatic retry with error context injected into the prompt
- After max retries, the epic is marked blocked and the runner picks another

### Core Concepts

**Formula**: TOML template defining a workflow (steps, dependencies, prompts)
**Molecule**: Instance of a formula (actual beads with real tasks)

Default `choochoo` formula has 3 steps (guidance sections within a single agent session):
1. **bearings** - Read context and state.md, identify relevant files
2. **implement** - Make changes, add tests
3. **verify** - Run tests, type checks, lint

The runner launches **one agent** per iteration with all step descriptions inlined in the prompt. These are not separate sub-agent executions.

**Runner-Driven Model**:
1. Runner does pre-flight (health checks, state staleness)
2. Runner builds enriched prompt (task context, step descriptions, state.md)
3. Agent reads context → implements → self-verifies → writes result.json + state.md → exits
4. Runner does hard verification → git commit → close beads

### Viewing Progress

```bash
bd show <root-id>              # See molecule structure
bd ready --assignee ralph      # What's ready for work
bd blocked                     # What's waiting
bd comments <id>               # Read progress notes
bd list --status in_progress   # Currently active tasks
```

### Running Multiple Ralphs

Multiple instances run safely in parallel:

```bash
# Terminal 1
choochoo

# Terminal 2
choochoo
```

- Each claims work by setting `in_progress`
- Won't double-pick same task
- Need multiple ready molecules

Start with 2, scale to 3-4 if stable. Rarely need more than 4-5.

## Error Handling

Key principle: **the runner handles all state transitions; the agent just implements and reports**.

### Verification Failures

When the runner's hard verification fails after an iteration:

1. **Runner captures error output** from verification commands
2. **Retry with context** → Runner re-launches agent with `RetryPrompt` containing the error output, attempt number, and files from previous attempt
3. **Working tree preserved** → Agent's changes stay in the working tree for the retry
4. **After max retries** (default 3) → Runner marks epic as blocked with `[CRITICAL]` comment

### Pre-flight Failures

The runner checks before each iteration:

1. **State staleness** → If `state.md` commit hash doesn't match HEAD, exits with `stale_state`
2. **Health check commands** → Configured commands (e.g., `just check`) must pass
3. **File existence checks** → Required files must exist

### Blocked Epics

After max retry failures:

1. Runner marks the epic as blocked
2. Runner adds a `[CRITICAL]` comment with failure details
3. Loop continues — picks next unblocked epic
4. Blocked epics don't appear in `next_ready_epic` queries

**Manual resolution:**
```bash
bd list --status=blocked       # Find blocked beads
bd comments <bead-id>          # Review what went wrong
bd update <bead-id> --status open   # Reopen for retry
```

See `docs/troubleshooting.md` for recovery procedures.

## Customization

All installed files are yours to modify.

### Configuration

Edit `choochoo.toml` in your project root:

- `backend` — Which AI backend to use
- `max_iterations` — Safety limit on iterations
- `assignee` — Task filter
- `health_check.checks` — Pre-flight verification commands
- `verification.checks` — Post-iteration verification commands
- `verification.max_retries` — How many retries before blocking

### Formulas

Edit `.beads/formulas/choochoo.formula.toml`:

- Add/remove steps
- Modify step prompts
- Change assignee patterns
- Add conditional steps

**Creating custom formulas:**
```toml
formula = "quick-task"
description = """Instructions for the task..."""
version = 2

[vars]
title = ""
task = ""

[[steps]]
id = "implement"
title = "{{title}}"
assignee = "ralph-subagent-implement"
description = """Step instructions..."""
```

### Assignee Conventions

| Prefix | Execution |
|--------|-----------|
| `ralph` | Picked up by Ralph loop |
| `ralph-subagent-*` | Spawned as sub-agent |
| `ralph-inline-*` | Executed by orchestrator directly |

See `docs/customization.md` for complete guide.
See `docs/formulas.md` for formula reference.

## Troubleshooting

### Common Issues

**Tasks not being picked up:**
```bash
bd show <bead-id>                    # Check status and assignee
bd update <bead-id> --assignee ralph # Assign to Ralph
bd update <bead-id> --status open    # Set status
bd dep <bead-id>                     # Check for blockers
```

**Health check always failing:**
1. Stop Ralph
2. Run checks manually: `just check` (or your configured health check)
3. Fix all failures
4. Resume Ralph

**Infinite retry loop:**
```bash
bd update <bead-id> --status blocked  # Block manually
bd comments <bead-id>                 # Review all attempts
# Fix underlying issue, then:
bd update <bead-id> --status open     # Reopen when ready
```

### Recovery Procedures

**Re-pour a spec:**
1. Move spec from archive: `mv .choochoo/archive/spec.md .choochoo/`
2. Delete existing beads (IDs in spec's `poured` array)
3. Clear `poured: []` in frontmatter
4. Run /choochoo:pour

**Session recovery (mid-task crash):**
```bash
bd list --status=in_progress --assignee=ralph  # Find in-progress task
bd comments <bead-id>                          # Review progress
bd update <bead-id> --status open              # Reopen to retry
```

### Debugging

```bash
choochoo --max-iterations 1   # Test single iteration
choochoo --verbose             # Verbose output
bd comments <bead-id>          # View task history
bd show <root-id>              # Inspect molecule structure
```

See `docs/troubleshooting.md` for complete guide.

## Documentation

- **`docs/workflow.md`** - Complete workflow guide
- **`docs/spec-format.md`** - Spec file format reference
- **`docs/commands.md`** - All commands with examples
- **`docs/formulas.md`** - Formula reference and customization
- **`docs/customization.md`** - Customizing Ralph for your project
- **`docs/troubleshooting.md`** - Common issues and solutions

### Commands

| Command | Purpose |
|---------|---------|
| `/choochoo:install` | Set up Ralph in project |
| `/choochoo:spec` | Generate/refine spec from plan |
| `/choochoo:pour` | Create beads from spec |
| `choochoo` | Run Ralph loop |
