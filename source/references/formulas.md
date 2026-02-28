# Formula Reference and Customization

## Overview

Formulas are TOML templates that define multi-step workflows for Ralph to execute. They provide a declarative way to describe complex tasks as a series of dependent steps, each with its own assignee and instructions.

Formulas live in `.beads/formulas/` within your project directory. When you "pour" a formula, it creates a set of beads (tasks) based on the formula's step definitions, with dependencies automatically wired up.

Key concepts:

- **Formula**: A TOML template defining a workflow
- **Step**: An individual task within the workflow
- **Variables**: Placeholders substituted when pouring (e.g., `{{title}}`, `{{task}}`)
- **Dependencies**: Steps can depend on other steps via the `needs` array

## Built-in Formula

choochoo ships with a built-in formula for feature implementation workflows.

### choochoo

The standard feature implementation workflow. Use this for new features, enhancements, and general development tasks.

**Steps:**

In runner v2, these steps are **guidance sections within a single agent session**, not separate sub-agent executions. The runner launches one agent with all step descriptions inlined in the prompt.

1. **bearings** - Read context and state.md, identify relevant files

   - Read task context and state.md provided by the runner
   - Identify relevant files and existing patterns
   - Runner has already verified codebase health (pre-flight)

2. **implement** - Make the actual changes

   - Follow existing patterns and conventions
   - Keep changes minimal
   - Add necessary tests
   - Depends on: `bearings`

3. **verify** - Self-verify before reporting

   - Run test suite, type checking, linting
   - Fix trivial issues inline; note substantial failures in result file
   - Depends on: `implement`

After the agent exits, the runner reads result.json, runs hard verification, commits as Ralph, and closes beads.

**Conditional Steps:**

- **gap-review** - Reviews implementation for missing work (when `auto_discovery=true`)
- **learning-capture** - Captures learnings and gaps discovered (when `auto_learnings=true`)

## Assignee Conventions

Assignees determine how Ralph handles each step. The prefix indicates execution mode:

| Prefix             | Meaning           | Example                    | Execution                      |
| ------------------ | ----------------- | -------------------------- | ------------------------------ |
| `ralph`            | Root molecule     | `ralph`                    | Picked up by Ralph loop        |
| `ralph-subagent-*` | Spawned sub-agent | `ralph-subagent-implement` | Ralph spawns a new agent       |
| `ralph-inline-*`   | Inline execution  | `ralph-inline-gap-review`  | Orchestrator executes directly |

**When to use each:**

- **`ralph`**: Top-level tasks that Ralph should pick up and orchestrate
- **`ralph-subagent-*`**: Complex steps requiring focused attention (implementation, diagnosis)
- **`ralph-inline-*`**: Simple, quick steps (status updates, gap reviews)

The distinction between subagent and inline affects resource usage and context isolation:

- Subagents get fresh context and can work independently
- Inline steps share the orchestrator's context and are faster

## Creating Custom Formulas

### Basic Structure

Create a new `.toml` file in `.beads/formulas/`. Here's a complete example:

```toml
formula = "code-review"
description = """
# Task: {{title}}

You are implementing this task. The runner has injected full task context,
step descriptions, and previous state into your prompt. Do NOT run `bd`
commands for task discovery or lifecycle management.

## Task
{{task}}

## Workflow
1. Read the task context and state.md provided in your prompt
2. Implement the changes
3. Self-verify (run tests, type checks, lint)
4. Write the result JSON file to the configured path
5. Update `.choochoo/state.md` with anything you learned
6. Exit

## Constraints
- Do NOT run `bd` commands — the runner handles beads lifecycle
- Do NOT run `git add` or `git commit` — the runner handles git
- Focus exclusively on implementation, testing, and self-verification
"""
version = 2
type = "workflow"

[vars.title]
description = "Short title for the task"
required = true

[vars.task]
description = "Detailed description of what needs to be done"
required = true

[[steps]]
id = "analyze"
title = "Analyze changes in {{title}}"
assignee = "ralph-subagent-analyze"
description = """
Analyze the code context for this task.

1. Read state.md and task context
2. Identify relevant files
3. Note any concerning patterns
"""

[[steps]]
id = "implement"
title = "Implement {{title}}"
assignee = "ralph-subagent-implement"
needs = ["analyze"]
description = """
Implement the changes.

- Follow existing patterns
- Keep changes minimal
- Add tests
"""

[[steps]]
id = "verify"
title = "Verify {{title}}"
assignee = "ralph-subagent-verify"
needs = ["implement"]
description = """
Self-verify before writing the result file.

1. Run test suite
2. Run type checking if available
3. Run linting if available
"""
```

### Formula Fields

| Field         | Required | Description                                 |
| ------------- | -------- | ------------------------------------------- |
| `formula`     | Yes      | Unique identifier for the formula           |
| `description` | Yes      | Root description explaining the workflow     |
| `version`     | No       | Version number for tracking changes         |
| `type`        | No       | Formula type (`"workflow"` for multi-step)   |
| `[vars.*]`    | No       | Variable definitions for template variables |
| `[[steps]]`   | Yes      | Array of step definitions                   |

### Step Fields

| Field         | Required | Description                                           |
| ------------- | -------- | ----------------------------------------------------- |
| `id`          | Yes      | Unique step identifier (used in `needs`)              |
| `title`       | Yes      | Human-readable title (supports variables)             |
| `assignee`    | Yes      | Who executes this step                                |
| `description` | Yes      | Detailed instructions (supports variables)            |
| `needs`       | No       | Array of step IDs that must complete first            |
| `condition`   | No       | Expression that must be truthy for bead to be created |

### Variables

Variables are placeholders that get substituted when pouring a formula. Define them with `[vars.*]` sections and use them with double braces:

```toml
[vars.title]
description = "Short title for the task"
required = true

[vars.task]
description = "Detailed description"
required = true

[vars.category]
description = "Task category"
required = false
default = "functional"

[[steps]]
id = "implement"
title = "{{title}}"
description = """
Implement: {{task}}

Category: {{category}}
"""
```

When pouring, pass values with `--var`:

```
bd mol pour my-formula \
  --var title="Add dark mode" \
  --var task="Implement theme toggle" \
  --var category="ui" \
  --assignee ralph
```

### Step Dependencies

Use the `needs` array to specify execution order. Steps only become ready when all dependencies are complete:

```toml
[[steps]]
id = "step-a"
title = "First step"
assignee = "ralph-subagent-a"
description = "This runs first"

[[steps]]
id = "step-b"
title = "Second step"
assignee = "ralph-subagent-b"
needs = ["step-a"]
description = "This waits for step-a"

[[steps]]
id = "step-c"
title = "Third step"
assignee = "ralph-subagent-c"
needs = ["step-a", "step-b"]
description = "This waits for both a and b"
```

### Conditional Steps

Conditions control whether a bead is **created** for a step when the formula is poured. If the condition is falsy, no bead is created for that step.

```toml
[vars.auto_discovery]
default = "false"

[vars.run_e2e]
default = "false"

[[steps]]
id = "gap-review"
title = "Review for gaps"
assignee = "ralph-inline-gap-review"
condition = "{{auto_discovery}}"
needs = ["implement"]
description = "Check for missing work..."

[[steps]]
id = "e2e-tests"
title = "Run E2E tests"
assignee = "ralph-subagent-e2e"
condition = "{{run_e2e}}"
needs = ["verify"]
description = "Run end-to-end test suite..."
```

Conditions are evaluated at pour time as truthy/falsy:

- `"true"`, `"yes"`, `"1"` → bead created
- `"false"`, `"no"`, `"0"`, `""` → bead not created

## Testing Your Formula

After creating a formula, verify it works correctly:

```
# 1. Check the formula is registered
bd formula list

# 2. Pour a test instance
bd mol pour my-formula \
  --var title="Test task" \
  --var task="Verify formula works" \
  --assignee ralph

# 3. Verify tasks were created
bd ready --assignee ralph

# 4. Check dependencies are correct
bd show <bead-id>
```

Common issues:

- **Formula not listed**: Check file is in `.beads/formulas/` with `.toml` extension
- **Variables not substituted**: Ensure variable names match exactly (case-sensitive)
- **Steps not created**: Check for TOML syntax errors

## Adding Learning Capture

In runner v2, agents capture learnings and gaps via the `notes` field in `result.json`:

```json
{
  "bead_id": "choo-mol-net",
  "outcome": "done",
  "files_changed": ["src/auth/login.py"],
  "commit_message": "feat(auth): add login endpoint",
  "notes": "[LEARNING] Auth middleware expects tokens in Authorization header\n[GAP] Missing input validation for registration API"
}
```

The agent also writes persistent context to `state.md` that survives across iterations.

For custom formulas, you can add capture instructions in step descriptions:

```toml
[[steps]]
id = "implement"
title = "Implement {{title}}"
assignee = "ralph-subagent-implement"
needs = ["bearings"]
description = """
Implement the feature: {{task}}

Follow patterns established in the codebase.
Write clean, well-tested code.

## Capturing Learnings

If you discover something noteworthy, include it in result.json notes:
- [LEARNING] <description>
- [GAP] <title> - <description>

Also update state.md with any persistent context for future iterations.
"""
```

## Labels Used by Ralph

Ralph uses labels to categorize and track tasks:

| Label                 | Meaning                                    |
| --------------------- | ------------------------------------------ |
| `ralph-step`          | Task is part of a Ralph workflow           |
| `bearings`            | Health check / codebase understanding step |
| `implement`           | Implementation step                        |
| `verify`              | Verification / testing step                |
| `gap-review`          | Gap discovery step (conditional)           |
| `learning-capture`    | Learning capture step (conditional)        |

Query by label:

```
# Find all implementation tasks
bd list --label implement

# Find all verification tasks
bd list --label verify
```

## Parallel Execution

Multiple Ralph instances can run safely in parallel, processing different tasks simultaneously.

### How It Works

- Tasks are claimed by setting status to `in_progress`
- `bd ready` only shows open tasks, so claimed tasks won't appear to other Ralphs
- Other Ralphs will see different ready tasks
- No coordination needed between instances

### Running Multiple Ralphs

```
# Terminal 1
choochoo

# Terminal 2
choochoo

# Terminal 3 (optional)
choochoo
```

### Scaling Guidelines

| Ralphs | Use Case                                   |
| ------ | ------------------------------------------ |
| 1      | Simple workflows, sequential tasks         |
| 2      | Standard development, moderate parallelism |
| 3-4    | Large features, many independent steps     |
| 5+     | Rarely needed, diminishing returns         |

### Best Practices

1. **Start small**: Begin with 2 Ralphs, scale up if stable
2. **Monitor progress**: Use `bd ready --assignee ralph` to check queue
3. **Watch for conflicts**: If Ralphs frequently compete for tasks, reduce count
4. **Consider dependencies**: Parallel execution helps most when steps are independent

### Monitoring

```
# Check what's ready for Ralph
bd ready --assignee ralph

# See all in-progress tasks
bd list --status in_progress

# View recent activity
bd list --limit 10
```
