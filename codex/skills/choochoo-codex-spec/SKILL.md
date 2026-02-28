---
name: choochoo-codex-spec
description: Generate or refine choochoo spec files from plans or conversation context. Use when asked to create, revise, or review .choochoo/*.spec.md.
---

# Generate or Refine Spec

## Load format rules first

Read `references/spec-format.md` before writing a spec.

## Inputs

- Optional source plan path
- Optional spec name
- Conversation context as fallback

## Spec File Naming

Specs are stored as `.choochoo/<name>.spec.md`. Each project can have multiple specs.

### When `spec_name` is provided:

- Use that name directly: `.choochoo/{spec_name}.spec.md`
- If file exists, enter refinement mode (Mode 2 or 3)
- If file doesn't exist, create new spec (Mode 1)

### When `spec_name` is NOT provided:

1. **Check for existing specs** in `.choochoo/*.spec.md`
2. **If exactly one spec exists**: Use that spec (refinement mode)
3. **If multiple specs exist**: Ask user which spec to work with
4. **If no specs exist**: Generate a suggested name based on:
   - The plan content or conversation context
   - Use kebab-case, descriptive, short (e.g., `user-auth`, `dark-mode`, `api-refactor`)
   - Ask user to confirm or provide alternative

## Mode Detection

1. **No spec exists (or new name)** → Generate new spec from plan/conversation
2. **Spec exists with review comments** → Refine spec based on comments
3. **Spec exists, no comments** → Ask: regenerate from scratch or continue with existing?

## Mode 1: Generate New Spec

When the target spec file doesn't exist:

### Step 1: Gather Context (before writing anything)

Before generating the spec, explore the codebase to inform task design:

- **Codebase exploration** — Search existing project structure and architecture.
  Identify patterns, conventions, file organization, test patterns, and relevant
  code the new feature will integrate with. Note existing utilities and components
  to reuse.
- **Technology research** — If the plan mentions unfamiliar tech, research
  documentation, best practices, common patterns, and integration examples with
  the existing stack.

Summarize findings concisely. Include them in the spec's `<context>` section
(`<existing_patterns>`, `<integration_points>`, `<new_technologies>`,
`<conventions>`).

### Step 2: Generate Spec

With context gathered:

- Accept plan from conversation context or file path
- Read `references/spec-format.md` for format guidance
- **Get current date** by running `date +%Y-%m-%d` bash command for the frontmatter `created` field
- **Include research findings** in the spec's `<context>` section
- Set `iteration: 1` and `poured: []`
- Include `auto_discovery` and `auto_learnings` (default `false`)
- Create concrete tasks with `id`, `priority`, `category`, `steps`, `test_steps`, and empty `<review></review>`
- Generate at `.choochoo/{spec_name}.spec.md`

## Mode 2: Refine Based on Comments (Review Loop)

When spec exists and has non-empty `<review>` tags:

1. **Parse existing spec** with all review comments
2. **Process comments** - understand requested changes:
   - "Split this into smaller tasks"
   - "Add more detail about X"
   - "Combine with task Y"
   - "Remove this, not needed"
   - Comments from other AI agents
3. **Regenerate affected tasks** based on feedback
4. **Clear review tags** after processing (empty tags remain for future comments)
5. **Increment frontmatter `iteration`** by 1
6. **Leave already-approved tasks unchanged**

This enables the review loop:

```
spec → user reviews → adds comments → spec → reviews → ... → pour
```

## Mode 3: Spec Exists, No Comments

When spec exists but all `<review>` tags are empty:

- Ask user: "Existing spec found. Would you like to:"
  - A) Start fresh (regenerate from plan)
  - B) Continue reviewing (open spec for editing)
  - C) Proceed to pour (tasks are ready)

## Quality rules

- No XML declaration line (`<?xml ...?>`)
- Keep task slices coherent and testable
- Prefer explicit, executable test steps
- Keep categories to: `functional`, `style`, `infrastructure`, `documentation`

## Output

**For new spec:**

- Location of generated spec file
- Mode used (`generate` or `refine`)
- Number of tasks extracted
- Instructions for reviewing
- Next step: review, add comments, run spec again or pour

**For refined spec:**

- Summary of changes made
- Number of tasks added/modified/removed
- Tasks still containing review comments
- Next step: review changes, add more comments or pour
