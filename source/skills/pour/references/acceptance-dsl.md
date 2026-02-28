# Acceptance DSL

Use only machine-executable checks.

## Supported check types

- `bash: <command>`
- `file_exists: <path>`
- `file_not_exists: <path>`

## Rules

- One check per line.
- No prose in acceptance body.
- Prefer 2-3 checks for small tasks, 3-5 for normal tasks, 5-8 for complex tasks.
- Commands run through `sh -c`, so `&&` and pipes are allowed.

## Examples

```text
bash: uv run pytest tests/test_auth.py -q
file_exists: src/auth/login.py
bash: uv run ruff check src/auth
```

```text
file_not_exists: src/legacy/auth_old.py
bash: npm test -- auth
```
