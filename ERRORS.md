# Error Log

## 2026-08-23 — Vite: missing named export from composable
- What didn't work: Browser error `The requested module '/src/composables/useHistory.js' does not provide an export named 'useHistory'` even though `useHistory.ts` correctly exported the function.
- What worked instead: Removed/archived empty sibling `.js` files under `src/composables/`. Vite resolves extensionless imports to `.js` before `.ts`, so 0-byte stubs shadowed the real modules.
- Note for next time: If a named export "disappears" at runtime but exists in `.ts`, check for empty or stale `.js` files next to the TypeScript source. Archive or delete the stubs; do not leave them in `composables/`.
