# Contributing

## Branching

- `main` — production-ready
- `develop` — integration branch
- `feature/<name>` — new feature
- `fix/<name>` — bug fix

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(users): add password reset endpoint
fix(auth): correct JWT expiration check
docs: update README setup steps
```

## Pull requests

1. Open against `develop`
2. Pass linters (`ruff`, `mypy`) and tests (`pytest`)
3. At least one approval required
4. Squash-merge

## Code style

- **Python:** `ruff format` + `ruff check` + `mypy`
- **JS/TS:** `prettier` + `eslint`

## Running tests

```bash
cd backend
pytest
```
