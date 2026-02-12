# Backend Rules

## Code Style
- Formatter: Black
- Linter: Ruff
- Type checker: mypy
- Run all checks: `ruff check . && black --check . && mypy .`

## Rules
- Never hardcode URLs. Always use environment variables or Django settings (e.g., `settings.BASE_URL`, `settings.API_URL`).
- Never use `--no-verify` when pushing or committing. If pre-push/pre-commit hooks fail, fix the underlying issue instead of bypassing them.
