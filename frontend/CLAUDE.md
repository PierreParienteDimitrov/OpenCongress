# Frontend Rules

## Code Style
- Linter: ESLint (`npm run lint`)
- Type checker: TypeScript (`npm run typecheck`)
- Build: `npm run build`

## Rules
- Never hardcode URLs. Always use environment variables (e.g., `process.env.NEXT_PUBLIC_API_URL`) or constants defined in a config file.
- Never use `--no-verify` when pushing or committing. If pre-push/pre-commit hooks fail, fix the underlying issue instead of bypassing them.
