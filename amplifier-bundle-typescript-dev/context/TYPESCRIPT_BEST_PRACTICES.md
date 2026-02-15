# TypeScript/JavaScript Development Philosophy

This document outlines the core development principles for TypeScript and JavaScript code in the Amplifier ecosystem.

## Core Philosophy: Type-Safe Pragmatism

We value **type safety at boundaries**, **completion over ambition**, and **modern patterns over legacy compatibility**.

---

## The Six Principles

### 1. Type Safety at Boundaries

Public APIs, exports, and function signatures should have explicit types. Let TypeScript infer internal types.

```typescript
// Good: Explicit at boundary, inferred internally
export function processItems(items: Item[]): ProcessedItem[] {
  const filtered = items.filter(item => item.active);  // inferred
  const mapped = filtered.map(transform);               // inferred
  return mapped;
}

// Bad: Over-annotated
export function processItems(items: Item[]): ProcessedItem[] {
  const filtered: Item[] = items.filter((item: Item) => item.active);
  const mapped: ProcessedItem[] = filtered.map(transform);
  return mapped;
}
```

**Test**: *"Are the types helping humans, or just satisfying the compiler?"*

### 2. Complete or Not At All

Production code should be **finished**. These patterns indicate incomplete code:

| Pattern | What It Signals |
|---------|-----------------|
| `// TODO` / `// FIXME` | Deferred work |
| `throw new Error("not implemented")` | Unfinished method |
| `// @ts-ignore` | Suppressed type error |
| `// @ts-expect-error` (no explanation) | Undocumented suppression |
| `any` type | Type system bypass |
| `as unknown as X` | Unsafe type assertion |

**Legitimate exceptions:**
- `// @ts-expect-error — [explanation]` with clear reasoning
- `any` in type-safe wrappers for untyped third-party code
- `// TODO` in test files
- Abstract method stubs in base classes

### 3. Strict Mode Always

Every TypeScript project should use `"strict": true` in tsconfig.json. This enables:
- `strictNullChecks` — No accidental null/undefined
- `noImplicitAny` — No untyped variables
- `strictFunctionTypes` — Correct function variance
- `strictPropertyInitialization` — No uninitialized class properties

### 4. Modern Patterns

Use modern JavaScript/TypeScript features:

| Prefer | Over |
|--------|------|
| `const` / `let` | `var` |
| `async` / `await` | `.then()` chains |
| Optional chaining `?.` | Manual null checks |
| Nullish coalescing `??` | `\|\|` for defaults |
| Template literals | String concatenation |
| Destructuring | Repeated property access |
| `for...of` | `for (i = 0; ...)` |

### 5. Clean Imports

Imports should be scannable and intentional:

```typescript
// Good: Named imports, sorted, grouped
import { readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";

import express from "express";
import { z } from "zod";

import { processItems } from "./processor";
import type { Config, Item } from "./types";
```

**Rules:**
- Named imports (not `import *`)
- Group: node builtins → third-party → local
- Use `import type` for type-only imports
- Sort within groups

### 6. Error Handling

Handle errors explicitly with proper types:

```typescript
// Good: Explicit error handling
try {
  const result = await fetchData();
  return { success: true, data: result };
} catch (error) {
  if (error instanceof NetworkError) {
    return { success: false, error: "Network unavailable" };
  }
  throw error;  // Re-throw unexpected errors
}
```

---

## The Golden Rule

> Write TypeScript as if the next person to read it is a JavaScript developer learning TypeScript. Make the types guide them, not confuse them.

---

## Quick Reference

### Always Do
- Enable `strict` mode in tsconfig.json
- Add explicit types to public APIs
- Use `const` assertions for literal types
- Handle `null` and `undefined` explicitly
- Prefer interfaces over type aliases for objects

### Never Do
- Use `any` without a comment explaining why
- Use `// @ts-ignore` (use `@ts-expect-error` with explanation instead)
- Leave `TODO`s in production code
- Use `var` declarations
- Catch errors without handling or re-throwing

### Consider Context
- `as` assertions: OK for test factories, avoid in production
- `unknown` vs `any`: Prefer `unknown` — force callers to narrow
- Enums vs unions: Unions for simple cases, enums for complex
- Classes vs functions: Functions for stateless, classes for stateful
