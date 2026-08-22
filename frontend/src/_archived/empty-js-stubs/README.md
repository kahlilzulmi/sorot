# Empty JS stubs (archived)

These 0-byte `.js` files were sitting next to real `.ts` composables and caused Vite to resolve the empty JS module first (e.g. `useHistory.js` instead of `useHistory.ts`), producing:

```
Uncaught SyntaxError: The requested module '/src/composables/useHistory.js'
does not provide an export named 'useHistory'
```

Moved here on 2026-08-23. Do not put empty `.js` siblings next to TypeScript sources under `src/composables/`.
