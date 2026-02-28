# Troubleshooting

This guide covers error handling, debugging techniques, and recovery procedures for choochoo workflows.

## Automatic Error Handling

Ralph handles most failures automatically through built-in retry and recovery mechanisms.

### Verification Failures

When the runner's hard verification fails after an agent iteration:

1. **Runner captures error output** from the failed verification commands
2. **Runner re-launches agent** with a `RetryPrompt` containing the error output, attempt number, and list of files from previous attempt
3. **Working tree preserved** — agent's changes remain for the retry
4. **After max retries** (default 3) → runner marks the epic as blocked with `[CRITICAL]` comment

Example verification failure flow:
```
Attempt 1: Agent implements → Runner verification fails → Retry with error context
Attempt 2: Agent fixes → Runner verification fails → Retry with updated context
Attempt 3: Agent fixes → Runner verification fails → Epic marked BLOCKED
```

The retry prompt includes:
- What specifically failed verification
- Error messages or test output (stderr)
- List of files changed in previous attempt
- Attempt number

### Pre-flight Failures

The runner checks before each iteration:

1. **State staleness** — `state.md` commit hash must match HEAD. Mismatch exits with `stale_state`
2. **Health check commands** — Configured commands (e.g., `just check`) must pass
3. **File existence** — Required files must exist

If pre-flight fails, the runner stops the loop with an appropriate `exit_reason`.

## Blocked Tasks

### Viewing Blocked Tasks

List all blocked tasks:
```
bd list --status=blocked
```

Or use the dedicated command:
```
bd blocked
```

### Understanding What Went Wrong

Review the task's comment history:
```
bd comments <bead-id>
```

Look for:
- `[CRITICAL]` markers for severe issues
- Error messages and stack traces
- Verification failure output

### Unblocking Tasks

To unblock a task and let Ralph retry:

1. **Fix the underlying issue manually** (update code, fix tests, etc.)
2. **Reopen the task**:
   ```
   bd update <bead-id> --status open
   ```
3. **Ralph will pick it up** on the next iteration

If the task has dependencies that are also blocked, fix those first.

## Common Issues

### Tasks Not Being Picked Up

**Symptom:** Ralph says "no ready tasks" but tasks exist in the system

**Possible causes:**
- Task not assigned to Ralph
- Task status is not "open"
- Task has unresolved blockers (dependencies)
- Task is part of a different molecule

**Fixes:**
```
# Check task details
bd show <bead-id>

# Assign to Ralph
bd update <bead-id> --assignee ralph

# Set status to open
bd update <bead-id> --status open

# Check for blockers
bd dep <bead-id>
```

### Infinite Retry Loop

**Symptom:** Task keeps failing verification but never gets blocked (or reaches blocked state repeatedly)

**Cause:** Fundamental issue that the agent cannot fix within its capabilities

**Fix:**
1. Block the task manually:
   ```
   bd update <bead-id> --status blocked
   ```
2. Review all comments for patterns:
   ```
   bd comments <bead-id>
   ```
3. Fix the underlying issue yourself
4. Reopen when ready:
   ```
   bd update <bead-id> --status open
   ```

### Health Check Always Failing

**Symptom:** Runner stops immediately with `exit_reason="preflight_failed"`

**Possible causes:**
- Test suite is fundamentally broken
- Environment configuration issues
- Missing dependencies
- Database not seeded

**Fix:**
1. Stop Ralph
2. Run health checks manually (e.g., `just check`, or whatever is in your `[health_check]` config)
3. Fix all failing checks
4. Verify everything passes
5. Resume Ralph

### Pour Creates Duplicate Tasks

**Symptom:** Running pour multiple times creates duplicate beads

**Cause:** The `poured` array in spec frontmatter wasn't updated, or spec was modified after pour

**Fix:**
- Check the spec's frontmatter for the `poured` array
- Delete duplicates manually
- Ensure spec is archived after successful pour

### Wrong Task Order

**Symptom:** Tasks are being worked in unexpected order

**Cause:** Dependencies not set correctly during pour, or manual dependency changes

**Fix:**
```
# View dependency graph
bd dep <molecule-id>

# Add missing dependency
bd dep add <dependent-id> <dependency-id>

# Remove incorrect dependency
bd dep remove <dependent-id> <dependency-id>
```

## Debugging Tips

### Run Single Iteration

Test Ralph behavior without committing to a full loop:
```
choochoo --max-iterations 1
```

This runs exactly one iteration and stops, letting you inspect results.

### Use Verbose Mode

Get detailed output about what Ralph is doing:
```
choochoo --verbose
```

### Check Task History

View all comments and state changes:
```
bd comments <bead-id>
```

### Inspect Molecule Structure

See the full dependency tree:
```
bd show <root-id>
```

Or visualize dependencies:
```
bd dep <molecule-id>
```

### Check Spec Status

View archived specs and their pour status:
```
ls -la .choochoo/archive/
```

Read a spec's frontmatter to see poured beads:
```
head -50 .choochoo/archive/my-feature.spec.md
```

## Recovery Procedures

### Partially Completed Pour

If pour fails mid-way through creating beads:

**State after failure:**
- Spec is NOT archived (still in `.choochoo/`)
- Some beads may have been created
- Dependency links may be incomplete

**Recovery:**
1. Check which beads were created:
   ```
   bd list --assignee=ralph
   ```
2. Fix the issue that caused pour to fail
3. Run pour again:
   ```
   /choochoo:pour
   ```

Pour is idempotent - it tracks created beads in the `poured` array and won't duplicate them.

### Corrupted State

If beads are in an inconsistent state:

1. List all Ralph-assigned beads:
   ```
   bd list --assignee=ralph
   ```

2. Delete problematic beads:
   ```
   bd delete <bead-id>
   ```

3. Re-pour from the spec:
   ```
   /choochoo:pour
   ```

### Starting Over (Re-pouring a Spec)

To completely redo a feature from its spec:

**Step 1: Unarchive the spec**
```
mv .choochoo/archive/my-feature.spec.md .choochoo/
```

**Step 2: Delete existing beads**

The spec's frontmatter contains a `poured` array listing all created bead IDs. Delete these beads:
```
bd delete <bead-id-1>
bd delete <bead-id-2>
# ... for each bead in the poured array
```

**Step 3: Clear the poured array**

Edit the spec's frontmatter to reset the `poured` array:
```yaml
---
poured: []
---
```

**Step 4: Re-pour**
```
/choochoo:pour
```

**Note:** If the original plan no longer exists, the archived spec still contains all task definitions and can be re-poured.

### Recovering from Git Issues

If Ralph's commits cause problems:

1. Stop Ralph
2. Use git to revert or reset as needed:
   ```
   git log --oneline -20  # Find the bad commits
   git revert <commit>    # Revert specific commits
   ```
3. Update task status to match current state
4. Resume Ralph

### Session Recovery

If a Claude Code session ends unexpectedly mid-task:

1. Check what task was in progress:
   ```
   bd list --status=in_progress --assignee=ralph
   ```
2. Review the task's last comments:
   ```
   bd comments <bead-id>
   ```
3. Either:
   - Mark complete if work was finished
   - Reopen if work needs to continue
   - Block if the interruption caused issues

## Getting Help

If you encounter issues not covered here:

1. Check the task comments for specific error messages
2. Review the spec file for task definitions
3. Inspect the molecule structure for dependency issues
4. Run in verbose mode to see detailed execution flow
