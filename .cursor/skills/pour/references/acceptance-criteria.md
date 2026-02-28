# Acceptance Criteria

Use only machine-executable shell commands. No prose.

## Format

Newline-separated shell commands. Each line is passed to `sh -c` and must exit 0
to pass. The runner stops on the first failure.

## Rules

- One command per line.
- No prose in acceptance body.
- Prefer 2-3 checks for small tasks, 3-5 for normal tasks, 5-8 for complex tasks.
- Commands run through `sh -c`, so `&&` and pipes work.
- Blank lines are ignored.
- Use `test -f <path>` to check file existence, `test ! -f <path>` for absence.

## Examples

```text
uv run pytest tests/test_auth.py -q
test -f src/auth/login.py
uv run ruff check src/auth
```

```text
test ! -f src/legacy/auth_old.py
npm test -- auth
```
