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

## Good Checks

Only run your project's CI commands — test suites, linters, type checkers, build
steps. These are the same commands a human would run to validate a PR:

```text
uv run pytest tests/test_auth.py -q
uv run mypy src/auth/ --no-error-summary
uv run ruff check src/auth/
npm test -- --run auth
npm run build
cargo test --lib auth
```

## Bad Checks — Do NOT Use

**Checking if a file exists (`test -f`):** A file existing says nothing about
whether the code is correct. Tests catch missing files anyway.

**Grep for strings (`grep`):** Brittle and meaningless. The string can exist
without the feature working. Tests catch missing functionality.

**Anything that is not running CI:** Checking directory structure, counting lines,
inspecting git history, curl-ing endpoints, reading config files — all of these
are bad. If the project's CI suite (tests, linting, type checking, build) passes,
the work is correct. If it doesn't, fix the CI suite.

```text
# BAD — never use these as acceptance criteria
test -f src/auth/login.py
grep -q "class LoginForm" src/auth/login.py
test -d src/components/auth
wc -l src/auth/login.py | awk '$1 > 10'
curl -s http://localhost:3000/health
```

## Examples

```text
uv run pytest tests/test_auth.py -q
uv run mypy src/auth/ --no-error-summary
uv run ruff check src/auth/
```

```text
npm test -- --run auth
npm run lint
npm run build
```

```text
cargo test --lib auth
cargo clippy -- -D warnings
```
