# Frontend Rules

## Code Style
- Linter: ESLint (`npm run lint`)
- Type checker: TypeScript (`npm run typecheck`)
- Build: `npm run build`

## Rules
- Never hardcode URLs. Always use environment variables (e.g., `process.env.NEXT_PUBLIC_API_URL`) or constants defined in a config file.
- Never use `--no-verify` when pushing or committing. If pre-push/pre-commit hooks fail, fix the underlying issue instead of bypassing them.
- Always use shadcn/ui components (`@/components/ui/`) when possible — Card, Badge, Button, Skeleton, Alert, Table, Select, Separator — instead of writing raw HTML+Tailwind equivalents.
- Always use theme CSS variables from `globals.css` via Tailwind classes (e.g., `bg-card`, `text-foreground`, `border-primary`). Never hardcode hex colors (`#1a1a2e`), oklch values, or custom font families. The theme is the single source of truth for all colors and typography.
- Use server-side rendering (RSC) for pages whenever possible. Keep client components (`"use client"`) limited to interactive parts that genuinely need browser APIs or React state.
