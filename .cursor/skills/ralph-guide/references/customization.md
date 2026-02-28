# Customization Guide

When you run `/choochoo:install`, you get local copies of formulas in your project. These aren't just configuration—they're yours to modify.

## Why Local Copies?

Different projects have different needs:

- A React app needs UI verification steps; a CLI tool doesn't
- One codebase might need more explicit prompts in the bearings phase
- A legacy project might require extra health checks before implementation
- Some teams want verbose commit messages; others prefer terse

The plugin provides working defaults, but you control the actual workflow. Think of install as an "eject" operation: you start with something that works, then adapt it to your project.

## What Gets Installed

See [Commands Reference](./commands.md#choochooinstall) for the complete list of files created. All of these are plain text files you can edit directly.

---

## Configuration

The runner is configured via `choochoo.toml` in your project root. See the main repo README for full configuration reference.

**Key customization points:**

| What | How |
|------|-----|
| Change iteration limit | `max_iterations = 200` |
| Add pre-flight health checks | `[health_check]` section with `checks = ["bash: just check"]` |
| Add post-iteration verification | `[verification]` section with `checks` and `max_retries` |
| Change the model | Add `"--model", "claude-opus-4-5-20251101"` to backend args |
| Block dangerous commands | Add `"--disallowedTools", "Bash(git push*)"` to backend args |

**Example: Add health check and verification:**

```toml
[health_check]
checks = [
  "bash: just check",
  "file_exists: .beads/beads.db",
]

[verification]
checks = ["bash: just check"]
max_retries = 3
```

---

## Formulas

Formulas define the multi-step workflow Ralph follows. See [Formula Reference](./formulas.md) for complete documentation.

### Quick Overview

The default `choochoo.formula.toml` defines:

```
bearings → implement → verify
```

Git commits and beads lifecycle are handled by the runner after verification passes.

Each step has:
- **id** - Unique identifier
- **title** - Human-readable name (supports `{{variables}}`)
- **assignee** - Who executes (`ralph-subagent-*` or `ralph-inline-*`)
- **needs** - Dependencies on other steps
- **description** - The prompt/instructions for that step

### Common Formula Customizations

**Adjust the bearings step:**

If your project needs specific exploration steps:

```toml
# In .beads/formulas/choochoo.formula.toml
# Find the bearings step and edit the description:
description = """
# BEARINGS

Read the task context and state.md provided by the runner.

1. Identify relevant files for this task
2. Check existing test patterns
3. Note any conventions to follow

The runner has already verified codebase health (pre-flight checks).
"""
```

**Add a code review step:**

```toml
[[steps]]
id = "review"
title = "Self-review {{title}}"
assignee = "ralph-subagent-review"
labels = ["ralph-step", "review"]
needs = ["implement"]
description = """
Review the implementation for:
- Code quality issues
- Missing edge cases
- Security concerns

Report findings in the result file.
"""

# Update verify to depend on review instead of implement
[[steps]]
id = "verify"
needs = ["review"]  # Changed from ["implement"]
```

For complete formula documentation, see [Formula Reference](./formulas.md).

---

## Spec Directory

The `.choochoo/` directory holds your spec files and related artifacts:

```
.choochoo/
├── my-feature.spec.md      # Active spec files
├── state.md                # Runner state file
├── archive/                # Completed specs
│   └── old-feature.spec.md
└── pour-preview.md         # Preview before pouring
```

**What you can customize:**
- Spec format (within the XML-like structure)
- Archive organization

---

## Updating Your Local Files

When the plugin updates, your local copies don't change automatically. This is intentional—your customizations are preserved.

**To get new features:**

1. Check the plugin's changelog for what changed
2. Manually merge changes into your local files, or
3. Re-run `/choochoo:install` and choose "Overwrite" for specific files

**Recommended approach:**
- Keep customizations minimal and well-commented
- Document why you changed things (for future merges)

---

## Examples

### Minimal: Increase Iteration Limit

```toml
# choochoo.toml
max_iterations = 200
```

### Moderate: Add Health Checks

```toml
# choochoo.toml
[health_check]
checks = [
  "bash: npm test",
  "file_exists: package.json",
]
```

### Advanced: Custom Formula

For tasks that don't need the full bearings → implement → verify workflow, create a custom formula.

Create `.beads/formulas/quick-task.formula.toml`:

```toml
formula = "quick-task"
description = """
# Quick Task: {{title}}

You are implementing this task. The runner has injected full task context,
step descriptions, and previous state into your prompt. Do NOT run `bd`
commands for task discovery or lifecycle management.

## Task
{{task}}

## Workflow
1. Read the task context and state.md provided in your prompt
2. Make the change described above
3. Run basic verification (tests, types)
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
required = true

[vars.task]
required = true

[[steps]]
id = "implement"
title = "{{title}}"
assignee = "ralph-subagent-implement"
description = """Make the change and verify it works."""
```

Once your formula is in `.beads/formulas/`, it appears as an option when you run `/choochoo:pour`. The pour command handles mapping your spec tasks to the formula's variables automatically.

You can also pour manually for one-off tasks:
```
bd mol pour quick-task --var title="Fix typo in README" --var task="Change 'teh' to 'the' on line 42" --assignee ralph
```

For workflows with child steps (like the default choochoo formula), see [Formula Reference](./formulas.md).

---

## Tips

1. **Start with defaults** - Run a few tasks before customizing
2. **Make small changes** - One modification at a time
3. **Test with single iteration** - `choochoo --max-iterations 1` to verify changes
4. **Keep a changelog** - Note what you changed and why
5. **Check formulas.md** - Deep dive on formula customization
