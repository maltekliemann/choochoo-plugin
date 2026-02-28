# Commands Reference

Complete reference for all choochoo commands with options and examples.

## /choochoo:install

Set up choochoo in your project by installing the runner and copying formulas. These files are yours to modify—see [Customization Guide](./customization.md) for details.

### Usage

```
/choochoo:install
```

### What It Does

1. **Checks prerequisites** - Verifies bd (beads), claude, jq, and Python 3.10+ are installed
2. **Initializes beads** - Runs `bd init` if .beads directory doesn't exist
3. **Installs runner** - Installs the `choochoo` Python package (CLI)
4. **Copies formulas** - choochoo formula template to `.beads/formulas/`
5. **Creates spec directory** - .choochoo/ for spec files

### Files Created

| File | Purpose |
|------|---------|
| `.beads/formulas/choochoo.formula.toml` | Standard workflow formula (bearings → implement → verify) |
| `.choochoo/` | Directory for spec files |

The `choochoo` CLI is installed globally via pip and available as a command.

All formula files are yours to modify. See [Customization Guide](./customization.md) for details on what you can change.

---

## /choochoo:spec

Generate or refine a spec file from a plan or conversation context.

### Usage

```
/choochoo:spec [source-file] [spec-name]
```

### Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `source-file` | No | Conversation context | Path to plan file (markdown, text) |
| `spec-name` | No | Auto-detected from content | Name for the spec file |

### Modes

The command operates in three modes based on current state:

1. **No spec exists** - Generate new spec from plan file or conversation
2. **Spec has review comments** - Refine spec based on your feedback
3. **Spec exists, no comments** - Prompts: regenerate or continue to pour?

### Examples

**Generate from plan file:**
```
/choochoo:spec docs/feature-plan.md auth-system
```

**Auto-detect spec name from conversation:**
```
/choochoo:spec
```
After discussing a feature, the spec name is inferred from context.

**Work with existing spec:**
```
/choochoo:spec
```
If `.choochoo/auth-system.spec.md` exists, offers to refine or regenerate.

**Refine after review:**
```
# Add feedback in <review> tags, then:
/choochoo:spec
```
Tasks with content in `<review>` tags trigger refinement mode.

---

## /choochoo:pour

Convert spec tasks into beads (issues) for Ralph to work on.

### Usage

```
/choochoo:pour [target-tasks] [spec-file] [formula]
```

### Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `target-tasks` | No | Project-size based | Number of tasks to create |
| `spec-file` | No | Most recent spec | Path to spec file |
| `formula` | No | Interactive prompt | Formula to use |

### Interactive Prompts

1. **Mode Selection** - Use workflow formula or create singular tasks
2. **Formula Selection** - Choose workflow formula (if not specified)
3. **Confirmation** - One of:
   - "Pour all tasks" - Create beads immediately
   - "Show task overview first" - Write preview to `.choochoo/pour-preview.md` for review
   - "Cancel" - Exit without creating beads

The preview option is useful for reviewing how spec tasks will be granularized before committing. If the breakdown doesn't look right, refine your spec and try again.

### Default Task Targets

| Project Type     | Target Tasks | Breakdown Ratio     |
| ---------------- | ------------ | ------------------- |
| Single feature   | 15-30 tasks  | ~5-10 per spec task |
| Feature set      | 50-100 tasks | ~5-8 per spec task  |
| Full application | 150-300 tasks| ~5-10 per spec task |

### Examples

**Pour all tasks from current spec:**
```
/choochoo:pour
```

**Pour specific number of tasks:**
```
/choochoo:pour 80
```

**Pour from specific spec with formula:**
```
/choochoo:pour 80 auth-system choochoo
```

---

## BD Commands Reference

Useful beads (bd) commands for working with Ralph workflows.

### View Tasks

**List ready tasks assigned to Ralph:**
```
bd ready --assignee ralph
```

**Show detailed task information:**
```
bd show <bead-id>
```

**View task comments and history:**
```
bd comments <bead-id>
```

**List all open Ralph tasks:**
```
bd list --status=open --assignee=ralph
```

**List blocked tasks:**
```
bd list --status=blocked
```

**List tasks by priority:**
```
bd list --status=open --sort=priority
```

### Manual Intervention

**Reopen a task:**
```
bd update <bead-id> --status open
```

**Mark task as blocked:**
```
bd update <bead-id> --status blocked
```

**Close a task manually:**
```
bd close <bead-id> --reason "Completed manually"
```

**Reassign a task:**
```
bd update <bead-id> --assignee someone-else
```

**Update task priority:**
```
bd update <bead-id> --priority high
```

### Formulas

**List available formulas:**
```
bd formula list
```

**Create task manually with formula:**
```
bd mol pour choochoo \
  --var title="Implement user auth" \
  --var task="Add JWT authentication to API endpoints" \
  --assignee ralph
```

### Dependencies

**Add dependency between tasks:**
```
bd dep add <bead-id> --blocks <other-bead-id>
```

**Remove dependency:**
```
bd dep remove <bead-id> --blocks <other-bead-id>
```

**View task dependencies:**
```
bd show <bead-id> --deps
```

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `/choochoo:install` | Set up Ralph in project |
| `/choochoo:spec` | Generate/refine spec file |
| `/choochoo:pour` | Create beads from spec |
| `choochoo` | Run Ralph loop |
| `bd ready --assignee ralph` | See queued tasks |
| `bd show <id>` | View task details |
