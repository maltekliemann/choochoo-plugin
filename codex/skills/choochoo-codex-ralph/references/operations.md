# Ralph Operations

## Runner v2 Model

The runner handles orchestration so the agent can focus on implementation:

1. **Pre-flight** — Check state.md staleness + health check commands
2. **Query & Claim** — Find next ready epic, set status to in_progress
3. **Build Prompt** — Assemble task context, state.md, step descriptions
4. **Agent Executes** — Implement, self-verify, write result.json + state.md, exit
5. **Post-Process** — Runner reads result.json, runs hard verification, git commit, close beads
6. **Next Iteration** — Repeat if tasks remain

Key principle: **the runner handles all state transitions; the agent just implements and reports**.

## Monitoring

- `bd ready --assignee ralph` — Verify there is queued work
- `bd list --status in_progress` — See what's currently running
- `bd list --status blocked` — Find blocked tasks
- `bd comments <bead-id>` — Inspect progress and failure context
- `bd show <bead-id>` — See molecule structure

## Error handling

### Verification failures
- Runner captures error output, re-launches agent with RetryPrompt
- Working tree preserved for retry
- After max retries (default 3), epic marked blocked with [CRITICAL] comment

### Pre-flight failures
- State staleness: exits with `stale_state`
- Health check commands must pass
- Required files must exist

## Recovery

- `bd update <bead-id> --status open` — Retry blocked work after fixing root cause
- `bd comments <bead-id>` — Review failure details before reopening
- `bd close <bead-id> --reason "Completed manually"` — Manual completion

## Parallel execution

- Run multiple `choochoo` instances in separate terminals
- Each claims work by setting `in_progress`
- Start with 2, scale to 3-4 if stable
- Reduce if repeated conflicts appear
