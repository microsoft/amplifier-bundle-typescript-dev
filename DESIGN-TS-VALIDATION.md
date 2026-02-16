# TypeScript Dev Bundle End-to-End Validation Design

## Goal

Validate that the `amplifier-bundle-typescript-dev` bundle works correctly end-to-end in a real Amplifier session against a real TypeScript project — matching the level of validation the Rust bundle received against attractor-rust.

## Background

The `amplifier-bundle-typescript-dev` bundle was built and unit-tested (163 tests pass), and its LSP capabilities were spot-checked via `amplifier tool invoke`. But it hasn't been validated end-to-end in a real Amplifier session against a real TypeScript project. The Rust bundle received thorough real-world validation (rust_check across 265 files, code-intel agents producing deep architectural analysis across 3 projects). TypeScript needs the same treatment before we can consider the Language Dev Bundle Consolidation project truly complete.

Specific gaps in current validation:
- `typescript_check` has never been run against a project with actual issues to find
- The `code-intel` agent has never produced an architectural analysis of a TypeScript project
- The auto-check hook has never been triggered by a real `.ts` or `.js` file edit
- The full bundle has never been loaded via `amplifier run` (only via `amplifier tool invoke`)

## Non-Goals

- Testing against multiple TypeScript projects (one well-designed project is sufficient)
- Performance benchmarking
- Testing the deprecation hook (separate concern, deferred until bundle migration is complete)
- Testing against production Amplifier environments (local validation is sufficient)

## Approach

Create a purpose-built TypeScript project with intentional issues across all check categories, set up a local Amplifier test environment with source overrides pointing to our local bundles, and execute four validation passes covering every component of the bundle.

A purpose-built project is preferred over cloning a random GitHub repo because it guarantees specific issues exist for each check type (a random project might be perfectly clean) and provides known architectural patterns for the `code-intel` agent to analyze.

## Architecture

### Test Project Structure

Location: `/home/bkrabach/dev/rust-dev-package/test-typescript-validation/`

```
test-typescript-validation/
├── package.json              # typescript, prettier, eslint as dev deps
├── tsconfig.json             # strict mode enabled
├── .prettierrc               # prettier config
├── eslint.config.js          # eslint flat config
├── src/
│   ├── types.ts              # Shared interfaces: MessageType enum, Message, Handler, Result
│   ├── index.ts              # Entry point wiring handlers → service → router
│   ├── utils.js              # Plain JS utility file (dual-language test)
│   ├── handlers/
│   │   ├── log-handler.ts    # Handler implementation — clean
│   │   ├── filter-handler.ts # Handler implementation — prettier issues
│   │   └── transform-handler.ts  # Handler implementation — stub issues
│   └── services/
│       ├── message-service.ts    # Uses handlers — tsc type error
│       └── router.ts             # Dispatches messages — eslint issues
└── .amplifier/
    └── settings.yaml         # Local source overrides for testing
```

### Intentional Issues by Check Type

| Check Type | File | Issue Description |
|------------|------|-------------------|
| **Prettier** | `src/handlers/filter-handler.ts` | Inconsistent indentation (tabs vs spaces), missing trailing comma |
| **ESLint** | `src/services/router.ts` | Unused variable, `any` type usage, missing return type annotation |
| **tsc** | `src/services/message-service.ts` | Type error: assigning string to number field |
| **Stubs** | `src/handlers/transform-handler.ts` | `// TODO: implement caching`, `throw new Error("not implemented")` |
| **Stubs** | `src/utils.js` | `// @ts-ignore` usage, `// FIXME` comment |

Clean files (`types.ts`, `log-handler.ts`, `index.ts`) must report zero issues — this validates no false positives.

### Architectural Patterns (for code-intel analysis)

The project implements a **Handler pattern** (similar to the Rust `Handler` trait validated in the smoke test):

- `Handler` interface in `types.ts` with a `handle(message: Message): Result` method
- Three implementations: `LogHandler`, `FilterHandler`, `TransformHandler`
- `MessageService` aggregates handlers and calls them in sequence
- `Router` dispatches messages to the right service based on `MessageType`
- `index.ts` wires everything together

This gives the `code-intel` agent meaningful material: interface → implementation mappings via `goToImplementation`, call chains via `incomingCalls`/`outgoingCalls`, type info via `hover`, and cross-file references via `findReferences`.

### Amplifier Test Environment

Set up local source overrides so `amplifier run` loads our local bundles:

```bash
# Register local bundle sources
amplifier source add typescript-dev /path/to/amplifier-bundle-typescript-dev --bundle
amplifier source add lsp /path/to/amplifier-bundle-lsp --bundle
amplifier source add tool-lsp /path/to/amplifier-bundle-lsp/modules/tool-lsp

# Register a test bundle that includes foundation + typescript-dev
amplifier bundle add /path/to/test-bundle.yaml --name ts-validation
```

The test bundle YAML includes foundation (for orchestrator) + typescript-dev behaviors. If the quality tool modules can't resolve their git URLs (the repos are new and may not have published releases), fall back to the LSP-only behavior for Passes 2-4 and test quality tools via direct `typescript_check` invocation in Pass 1.

## Validation Passes

### Pass 1: `typescript_check` Tool

Invoke the tool directly against the test project and verify all check types find their planted issues.

**Test matrix:**

| Invocation | Expected Result |
|-----------|----------------|
| `typescript_check paths: ["src/"]` | Issues from all 4 categories (prettier, eslint, tsc, stubs) |
| `typescript_check paths: ["src/types.ts"]` | Zero issues (clean file) |
| `typescript_check paths: ["src/"] checks: ["format"]` | Only prettier issues |
| `typescript_check paths: ["src/"] checks: ["lint"]` | Only eslint issues |
| `typescript_check paths: ["src/"] checks: ["types"]` | Only tsc type errors |
| `typescript_check paths: ["src/"] checks: ["stubs"]` | Only stub detections |
| `typescript_check paths: ["src/"] fix: true` | Auto-fixes prettier issues (at minimum) |

**Verification criteria:**
- Each check category finds at least 1 issue in the correct file
- Clean files (`types.ts`, `log-handler.ts`, `index.ts`) report zero issues
- Issue output includes file path, line number, severity, and actionable message
- No crashes, no unhandled exceptions
- `TOOL-NOT-FOUND` issues returned gracefully if a tool is missing (not a crash)

### Pass 2: LSP Operations (Direct Tool Invoke)

Test every declared-available operation against the test project files:

| Operation | Test Target | Expected Result |
|-----------|-------------|----------------|
| `hover` | `Handler` interface in `types.ts` | Returns interface definition with type info |
| `goToDefinition` | `Handler` usage in `message-service.ts` | Jumps to interface definition in `types.ts` |
| `findReferences` | `Message` interface | Finds all usages across handlers and services |
| `documentSymbol` | `index.ts` | Returns full symbol tree with functions, variables |
| `goToImplementation` | `Handler` interface | Finds `LogHandler`, `FilterHandler`, `TransformHandler` |
| `prepareCallHierarchy` | `MessageService.process()` | Returns hierarchy item |
| `incomingCalls` | `MessageService.process()` | Finds callers from `index.ts` and/or `router.ts` |
| `outgoingCalls` | `MessageService.process()` | Finds calls to `handler.handle()` |
| `diagnostics` | `message-service.ts` (has type error) | Finds the planted type error |
| `rename` | `Handler` interface name | Preview shows edits across all implementing files |
| `codeAction` | On the type error in `message-service.ts` | Suggests a fix |
| `inlayHints` | `index.ts` | Returns type and/or parameter name hints |

**Additionally verify:**
- `workspaceSymbol` is NOT in the available operations schema (suppressed via capabilities)
- All operations return non-empty, meaningful results (not just empty arrays)
- Operations work on both `.ts` and `.js` files (test `hover` on `utils.js`)

### Pass 3: `code-intel` Agent Delegation

Start an Amplifier session with the test bundle and request an architectural analysis:

> "Analyze the architecture of this TypeScript project — map the interfaces, implementations, call chains, and identify any design patterns."

**Verification criteria:**
- The agent uses multiple LSP operations (not just grep/file reading)
- Produces a structured analysis with:
  - Interface → implementation mappings (Handler → LogHandler, FilterHandler, TransformHandler)
  - Call chain tracing (index.ts → Router → MessageService → handlers)
  - Type information from hover results
  - File:line references for key symbols
- Identifies the Handler/Strategy pattern
- Analysis quality is comparable to what the Rust `code-intel` agent produced for attractor-rust

### Pass 4: Auto-Check Hook

In the same session (or a fresh one), test the hook by editing files:

| Action | Expected Result |
|--------|----------------|
| Edit a `.ts` file | Hook fires, reports quality check results |
| Edit a `.js` file | Hook fires (dual-language support works) |
| Edit a `.py` or `.md` file | Hook does NOT fire (wrong file type) |

**Verification criteria:**
- Hook messages appear in the session output after `.ts`/`.js` edits
- Hook does not fire for non-TypeScript/JavaScript files
- Hook output includes the check results (not just a generic "checking..." message)

## Error Handling

- **Tool not installed:** If `prettier`, `eslint`, or `tsc` aren't installed in the test project's `node_modules`, `typescript_check` should return `TOOL-NOT-FOUND` issues with a helpful message — not crash. Verify this graceful degradation before installing dependencies.
- **LSP cold start:** If `typescript-language-server` isn't responding during LSP tests, retry after a few seconds (indexing delay). This is a known behavior shared with Pyright and rust-analyzer.
- **Module resolution failure:** If `amplifier run` can't load quality tool modules (git URLs not resolvable for local-only bundles), use the LSP-only behavior (`typescript-dev:behaviors/typescript-lsp.yaml`) instead of the full composite. This still validates LSP operations and the `code-intel` agent.
- **amplifier tool invoke fallback:** If starting a full interactive `amplifier run` session is impractical, use `amplifier tool invoke` for Passes 1 and 2. This exercises the real Amplifier bundle loading and tool execution paths. Passes 3 and 4 may need the interactive session — note any limitations in the verification report.

## Success Criteria

| Criterion | Pass Condition |
|-----------|---------------|
| `typescript_check` finds all 4 issue types | At least 1 issue per check category (prettier, eslint, tsc, stubs) |
| Zero false positives | Clean files report no issues |
| All 11 LSP operations work | Non-empty, meaningful results for each |
| `workspaceSymbol` suppressed | Not in available operations list |
| `code-intel` agent produces analysis | Structured output with LSP-derived insights |
| Auto-check hook fires for `.ts` | Hook message appears after `.ts` edit |
| Auto-check hook fires for `.js` | Hook message appears after `.js` edit |
| Auto-check hook silent for non-TS/JS | No hook message after `.py`/`.md` edit |
| Full bundle loads | `amplifier run` starts without errors |

All 9 criteria must pass for the validation to be considered complete. If any LSP operation fails (returns errors, not just empty results), update the capability declaration in `behaviors/typescript-lsp.yaml` for both `typescript` and `javascript` language blocks, commit, and push.

## Capability Fixes

If live testing reveals any capability declaration is wrong:

1. Update `amplifier-bundle-typescript-dev/behaviors/typescript-lsp.yaml` — both the `typescript` and `javascript` capability blocks
2. Update `amplifier-bundle-typescript-dev/tests/test_bundle_composition.py` — capability assertion tests
3. Commit with message: `fix: update TypeScript capability declarations based on live testing`
4. Push to origin/main

## Open Questions

1. **ESLint flat config vs legacy config:** The test project should use ESLint flat config (`eslint.config.js`) since legacy `.eslintrc` is deprecated in ESLint v9+. Verify the checker handles both formats or document which is required.
2. **npx behavior:** The `typescript_check` tool uses `npx` for tool invocation. If `node_modules/.bin/` exists locally, `npx` will use it. If not, `npx` may try to download — verify behavior and document any `--no-install` requirements.
3. **Hook debouncing:** If the auto-check hook fires on every keystroke/save, it could be noisy during rapid editing. Note the actual behavior and whether debouncing is needed as a future improvement.
