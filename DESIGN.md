# Language Dev Bundle Consolidation Design

## Goal

Consolidate 7 Amplifier language-support repos into 4 comprehensive language-dev bundles, cleaning up the base LSP bundle and creating unified dev experiences for Python, Rust, and TypeScript.

## Background

The Amplifier ecosystem has fragmented language support across 7 repos: a base LSP bundle, 3 language-specific LSP bundles (Python, Rust, TypeScript), and 1 language dev bundle (Python). The language LSP bundles are thin configuration-only wrappers with zero modules that add unnecessary repo overhead. Meanwhile, only Python has a "dev" bundle with quality tooling -- Rust and TypeScript have nothing.

Live testing revealed additional issues: 3 of the base LSP bundle's 17 operations are dead (no server implements type hierarchy), the `customRequest` operation has two bugs preventing valuable server extensions from working, and capability declarations are missing or inconsistent across language bundles.

## Approach

Absorb each thin language-LSP bundle into its corresponding language-dev bundle, creating new dev bundles for Rust and TypeScript. Use a two-behavior + composite pattern within each dev bundle so users can include just LSP or just quality tools independently. Convert the old LSP repos into forwarding stubs with a new reusable deprecation hook. Clean up the base LSP bundle by removing dead operations and fixing `customRequest`.

## Architecture

### Current State (7 repos)

```
amplifier-bundle-lsp                    Base: tool-lsp module, 17 ops, proxy server
amplifier-bundle-lsp-python             Thin: Pyright config + python-code-intel agent
amplifier-bundle-lsp-rust               Thin: rust-analyzer config + rust-code-intel agent
amplifier-bundle-lsp-typescript         Thin: ts-lang-server config + typescript-code-intel agent
amplifier-bundle-python-dev             Dev: includes lsp-python + quality tools
amplifier-bundle-rust-dev               (does not exist)
amplifier-bundle-typescript-dev         (does not exist)
```

### Target State (4 active repos + 3 forwarding stubs)

```
amplifier-bundle-lsp                    Base: tool-lsp module, 14 ops (type hierarchy removed),
                                              customRequest fixed
amplifier-bundle-python-dev             Dev: absorbs lsp-python + quality tools + 2 agents
amplifier-bundle-rust-dev               Dev: absorbs lsp-rust + quality tools + 2 agents (NEW)
amplifier-bundle-typescript-dev         Dev: absorbs lsp-typescript + quality tools + 2 agents (NEW)
amplifier-bundle-lsp-python             Forwarding stub -> python-dev (with deprecation hook)
amplifier-bundle-lsp-rust               Forwarding stub -> rust-dev (with deprecation hook)
amplifier-bundle-lsp-typescript         Forwarding stub -> typescript-dev (with deprecation hook)
```

### Bundle Composition Diagram

```
+------------------------------------------------------------------+
|  {lang}-dev bundle (e.g., python-dev)                            |
|                                                                   |
|  bundle.yaml                                                      |
|    includes: {lang}-dev:behaviors/{lang}-dev                      |
|                                                                   |
|  behaviors/                                                       |
|    {lang}-lsp.yaml --- includes lsp-core.yaml from base ----+    |
|      | registers: code-intel agent + {lang}-lsp.md context   |    |
|      | configures: tool-lsp with language server config       |    |
|    {lang}-quality.yaml                                       |    |
|      | registers: tool-{lang}-check + hooks-{lang}-check     |    |
|      | registers: {lang}-dev agent + instructions context     |    |
|    {lang}-dev.yaml (composite)                               |    |
|      | includes: {lang}-lsp.yaml + {lang}-quality.yaml       |    |
|                                                               |    |
|  agents/                                                      |    |
|    code-intel.md --- pure LSP navigation specialist          |    |
|    {lang}-dev.md --- quality + general dev expert            |    |
|                                                               |    |
|  context/                                                     |    |
|    {lang}-lsp.md --- language-specific LSP guidance          |    |
|    {lang}-dev-instructions.md --- tool usage + workflows     |    |
|    {LANG}_BEST_PRACTICES.md --- development philosophy       |    |
|                                                               |    |
|  modules/                                                     |    |
|    tool-{lang}-check/ --- format, lint, types, stubs         |    |
|    hooks-{lang}-check/ --- auto-check on file edit           |    |
|                                                               |    |
|  src/amplifier_bundle_{lang}_dev/ --- shared core library    |    |
|    checker.py, config.py, models.py                          |    |
+------------------------------------------------------------------+
                                                                |
+---------------------------------------------------------------+
|  amplifier-bundle-lsp (base, unchanged except cleanup)
|    behaviors/lsp-core.yaml --- tool-lsp + empty languages: {}
|    modules/tool-lsp/ --- 14 ops (was 17), customRequest fixed
|    agents/code-navigator.md --- generic LSP agent
|    context/lsp-general.md
+---------------------------------------------------------------+
```

### Behavior Composition Detail

Each dev bundle has 3 behaviors enabling flexible composition:

```yaml
# Users who want ONLY LSP (no quality hooks):
includes:
  - bundle: python-dev:behaviors/python-lsp

# Users who want ONLY quality tools (unusual but possible):
includes:
  - bundle: python-dev:behaviors/python-quality

# Users who want the full dev experience (default):
includes:
  - bundle: git+https://github.com/microsoft/amplifier-bundle-python-dev@main
  # or equivalently:
  - bundle: python-dev:behaviors/python-dev
```

## Components

### Agent Design

Two agents per dev bundle, following ecosystem conventions:

| Full Delegate Path | Name | Convention | Role |
|---|---|---|---|
| `python-dev:code-intel` | `code-intel` | Role within domain | Pure LSP navigation specialist |
| `python-dev:python-dev` | `python-dev` | Primary expert | Quality + general dev expert |
| `rust-dev:code-intel` | `code-intel` | Role within domain | Pure LSP navigation specialist |
| `rust-dev:rust-dev` | `rust-dev` | Primary expert | Quality + general dev expert |
| `typescript-dev:code-intel` | `code-intel` | Role within domain | Pure LSP navigation specialist |
| `typescript-dev:typescript-dev` | `typescript-dev` | Primary expert | Quality + general dev expert |

The language prefix is dropped from `code-intel` because the namespace already provides language context (`python-dev:code-intel`). Multi-agent bundles in the ecosystem use role-only names (e.g., `design-intelligence:art-director`, not `design-intelligence:design-art-director`).

Each agent is registered by its corresponding behavior: `code-intel` by `{lang}-lsp.yaml`, `{lang}-dev` by `{lang}-quality.yaml`. Users who include only the LSP behavior get only the `code-intel` agent.

Description disambiguation between the two agents:
- `code-intel` trigger words: "trace", "find usages", "call hierarchy", "type of", "where defined", "what calls", "implementations"
- `{lang}-dev` trigger words: "quality", "lint", "format", "type check", "review", "best practices", "check code"

### Base LSP Bundle Changes

**Operations to remove (dead on all tested servers):**

| Operation | Pyright | rust-analyzer | Reason |
|---|---|---|---|
| `prepareTypeHierarchy` | ERROR | ERROR | Not implemented by any server |
| `supertypes` | ERROR | ERROR | Depends on prepareTypeHierarchy |
| `subtypes` | ERROR | ERROR | Depends on prepareTypeHierarchy |

Result: 17 operations to 14 operations. Simplifies the tool description the AI sees.

**customRequest fix (2 targeted changes in operations.py):**

Bug 1 -- Auto-param enrichment mangles params. When `file_path`/`line`/`character` are provided, `_op_customRequest` auto-adds `textDocument` and `position` to `customParams`. But some methods (e.g., `rust-analyzer/viewFileText`) expect flat `{uri: "..."}`, not nested `{textDocument: {uri: "..."}}`. Fix: only auto-add `textDocument`/`position` if `customParams` doesn't already include them.

Bug 2 -- Errors return as success=True. The exception handler catches errors and returns `{error: "..."}` as a normal dict, which `tool.py` wraps as `ToolResult(success=True)`. Fix: either re-raise the exception so `tool.py` marks `success=False`, or check for `error` key at the tool layer.

**Validated customRequest extensions (post-fix, tested via raw JSON-RPC):**

| Method | Result | Value |
|---|---|---|
| `rust-analyzer/expandMacro` | WORKS | Full derive trait expansion -- see generated Debug/Clone impl code |
| `rust-analyzer/relatedTests` | WORKS | Finds test functions associated with a given function/struct |
| `experimental/externalDocs` | WORKS | Returns docs.rs URLs for types |
| `rust-analyzer/viewHir` | WORKS | HIR dump for debugging compiler understanding |
| `rust-analyzer/analyzerStatus` | WORKS | Workspace status, loaded packages |

Pyright uses `workspace/executeCommand` pattern instead of direct custom methods. This should be documented in the Python LSP context.

### LSP Capability Declarations

**Python (Pyright):**

```yaml
capabilities:
  diagnostics: true        # WORKS: Found type errors, unused imports
  rename: true             # WORKS: Cross-file rename within packages
  codeAction: false        # ALWAYS EMPTY: Pyright doesn't generate code actions
  inlayHints: false        # ERROR: Unhandled method
  customRequest: false     # No direct custom methods (uses workspace/executeCommand)
  goToImplementation: false # ERROR: Unhandled method -- override base
```

Note: `goToImplementation` is a base operation (always shown), but it genuinely doesn't work in Pyright. The capability declaration should suppress it from the tool description for Python files. If the base tool doesn't support per-language base-op suppression, document the limitation in the Python LSP context instead.

**Rust (rust-analyzer):**

```yaml
capabilities:
  diagnostics: true        # WORKS via push diagnostics (pull returns empty)
  rename: true             # WORKS: Cross-crate symbol rename
  codeAction: true         # WORKS: 10+ code actions (generate impl, derive, extract, etc.)
  inlayHints: true         # WORKS: Type hints, lifetime hints, parameter names
  customRequest: true      # WORKS: expandMacro, relatedTests, externalDocs, viewHir, analyzerStatus
```

Note: rust-analyzer uses push diagnostics (`textDocument/publishDiagnostics`), not pull. The tool has fallback code for the push cache but it's not working correctly. The `rust-dev` quality tools (`cargo check --message-format=json`) provide a reliable alternative diagnostic path.

**TypeScript (typescript-language-server) -- estimated, needs live validation:**

```yaml
capabilities:
  diagnostics: true        # Expected: supports pull diagnostics
  rename: true             # Expected: TypeScript rename is well-supported
  codeAction: true         # Expected: organize imports, add missing imports, etc.
  inlayHints: true         # Configured in init options (param names, types, etc.)
  customRequest: false     # Unknown; punt until validated
```

TypeScript was not live-tested because the LSP tool only had Python and Rust configured in the current session. Live validation is needed during Phase 4.

### Quality Tools Per Language

**Python (exists -- evolve):**

| Check | Tool | Command |
|---|---|---|
| Formatting | ruff | `ruff format --check --diff` |
| Linting | ruff | `ruff check --output-format=json` |
| Type checking | pyright | `pyright --outputjson` |
| Stub detection | custom regex | Scans for TODO, FIXME, NotImplementedError, etc. |

Config source: `pyproject.toml` `[tool.amplifier-python-dev]`

**Rust (new -- build):**

| Check | Tool | Command |
|---|---|---|
| Formatting | rustfmt | `cargo fmt --check` |
| Linting | clippy | `cargo clippy --message-format=json` |
| Type/compile checking | cargo | `cargo check --message-format=json` |
| Stub detection | custom regex | Scans for `todo!()`, `unimplemented!()`, `unreachable!()`, `// TODO`, `// FIXME`, `// HACK` |

Config source: `Cargo.toml` `[workspace.metadata.amplifier-rust-dev]` or `[package.metadata.amplifier-rust-dev]`

Stub legitimacy exemptions (Rust-specific):
- `todo!()` in test files
- `unimplemented!()` in trait default implementations with doc comments explaining intent
- `unreachable!()` in match arms (legitimate safety assertion)
- `// TODO` in test files

**TypeScript (new -- build):**

| Check | Tool | Command |
|---|---|---|
| Formatting | prettier | `prettier --check` |
| Linting | eslint | `eslint --format=json` |
| Type checking | tsc | `tsc --noEmit` |
| Stub detection | custom regex | Scans for `// TODO`, `// FIXME`, `throw new Error("not implemented")`, `// @ts-ignore` |

Config source: `package.json` `amplifier-typescript-dev` key or a dedicated config file

TypeScript tooling is more fragmented than Python/Rust. Prettier and ESLint may not be installed. The checker should handle missing tools gracefully (same pattern as Python -- return a `TOOL-NOT-FOUND` issue).

### Deprecation Hook Module

A reusable foundation-level hook that any bundle can include to signal deprecation. Fires once per session, warns both the AI and user, and provides migration guidance.

**Location:** `amplifier-foundation/modules/hooks-deprecation/`

**Config schema:**

```yaml
hooks:
  - module: hooks-deprecation
    source: git+https://github.com/microsoft/amplifier-foundation@main#subdirectory=modules/hooks-deprecation
    config:
      bundle_name: lsp-python
      replacement: amplifier-bundle-python-dev
      message: "lsp-python has been consolidated into python-dev"
      migration: |
        Update your includes:
        -   - bundle: git+.../amplifier-bundle-lsp-python@main
        +   - bundle: git+.../amplifier-bundle-python-dev@main
      severity: warning
      sunset_date: "2026-06-01"
```

**Hook behavior:**

1. Fires on `session:start` event (once per session via internal flag).
2. Attempts to identify which bundle file(s) include the deprecated bundle by scanning `coordinator.config` or session metadata for the include source path. If identifiable, includes the file path in the warning message (e.g., "Found in: ~/.amplifier/bundles/my-config.yaml line 12").
3. Injects a context block visible to the AI: a deprecation warning with the bundle name, replacement, and migration instructions.
4. Emits a `deprecation:warning` event for other hooks to observe.
5. Displays a user-visible message via the hook result.
6. If `sunset_date` is set and past, escalates severity (info to warning, warning to error).

**Source file identification (best-effort):**

1. Check `coordinator.config` or similar metadata for provenance (if the bundle loader tracks it).
2. If not available, scan common locations: `.amplifier/settings.yaml` in the working directory, `~/.amplifier/settings.yaml`, and any YAML files in `.amplifier/` containing the deprecated bundle URL.
3. Report findings in the warning message.
4. If source can't be determined, fall back to generic migration instructions from the config.

### Forwarding Stubs

Each retired repo becomes a minimal forwarding bundle:

```yaml
# amplifier-bundle-lsp-python/bundle.yaml
bundle:
  name: lsp-python
  version: 2.0.0
  description: "DEPRECATED: Consolidated into python-dev. This bundle forwards automatically."

includes:
  - bundle: git+https://github.com/microsoft/amplifier-bundle-python-dev@main

hooks:
  - module: hooks-deprecation
    source: git+https://github.com/microsoft/amplifier-foundation@main#subdirectory=modules/hooks-deprecation
    config:
      bundle_name: lsp-python
      replacement: amplifier-bundle-python-dev
      message: "amplifier-bundle-lsp-python has been consolidated into amplifier-bundle-python-dev"
      migration: |
        Update your includes:
        -   - bundle: git+https://github.com/microsoft/amplifier-bundle-lsp-python@main
        +   - bundle: git+https://github.com/microsoft/amplifier-bundle-python-dev@main
      severity: warning
```

Same pattern for `lsp-rust` to `rust-dev` and `lsp-typescript` to `typescript-dev`. READMEs get a prominent deprecation notice. After 2-3 months, repos can be archived.

## Data Flow

### Bundle Loading (User Perspective)

```
User's settings.yaml
  includes: python-dev
    -> python-dev/bundle.yaml
      includes: python-dev:behaviors/python-dev.yaml (composite)
        includes: python-dev:behaviors/python-lsp.yaml
          includes: lsp:behaviors/lsp-core.yaml (from base bundle)
            -> tool-lsp module with empty languages: {}
          -> deep-merges python language config into languages: {}
          -> registers code-intel agent
        includes: python-dev:behaviors/python-quality.yaml
          -> tool-python-check module
          -> hooks-python-check module
          -> registers python-dev agent
```

### Deprecation Flow (Legacy User)

```
User's settings.yaml (unchanged, still references lsp-python)
  includes: lsp-python
    -> lsp-python/bundle.yaml (forwarding stub)
      includes: python-dev (full dev bundle loads transparently)
      hooks: deprecation hook fires on session:start
        -> warns AI with context block
        -> warns user with visible message
        -> identifies source file if possible
```

## Error Handling

- **Missing quality tools:** Each language checker handles missing external tools gracefully. If `cargo clippy` isn't installed, the check returns a `TOOL-NOT-FOUND` issue with installation instructions rather than crashing. Same pattern already proven in `python-dev`.
- **LSP server not installed:** The base `tool-lsp` already handles this -- returns a clear error message when a language server binary isn't found.
- **customRequest failures:** After the fix, errors from custom methods will properly return `success=False` with the server's error message, allowing the AI to try alternatives or inform the user.
- **Deprecation hook source identification failure:** Best-effort; falls back to generic migration instructions from the config. Never blocks session startup.

## Testing Strategy

### Per-Phase Testing

**Phase 0 (Base LSP cleanup):** Update existing test suite (16 test files). Remove type hierarchy tests. Add customRequest param-enrichment tests (verify opt-in behavior). Add customRequest error-propagation tests (verify success=False on server errors).

**Phase 1 (Deprecation hook):** Unit test with mock deprecated bundle config. Test once-per-session firing. Test context injection content. Test source file identification against known fixture files. Test sunset date escalation.

**Phase 2 (Python-dev evolution):** Move and adapt deep-merge tests from lsp-python. Verify behavior composition: LSP-only include, quality-only include, composite include. Verify agent registration matches behavior includes. Verify capability declarations match live test results.

**Phase 3 (Rust-dev):** Adapt deep-merge tests from lsp-rust. Build checker tests: `cargo fmt --check` parsing, `cargo clippy` JSON output parsing, `cargo check` JSON output parsing, stub detection regex. Test behavior composition. Live-test all LSP operations against rust-analyzer.

**Phase 4 (TypeScript-dev):** Build checker tests: prettier, eslint, tsc output parsing, stub detection. Test behavior composition. Live-test all LSP operations against typescript-language-server (first time this server will be tested with the tool).

**Phase 5 (Forwarding stubs):** Verify forwarding stubs load the full dev bundle transparently. Verify deprecation hook fires exactly once. Verify user gets migration guidance.

### Live Testing Protocol

For each language server, validate every operation in the tool's schema against a real project:

1. Set up a small but representative project (multiple files, imports/modules, at least one type hierarchy).
2. Run every operation and record: WORKS, EMPTY (returns valid but empty result), or ERROR (with error message).
3. Compare results against capability declarations and update if mismatched.
4. For TypeScript specifically, this will be the first live test -- results will inform capability declarations.

## Execution Phases

### Phase 0: Clean Up Base LSP Bundle
- Remove `prepareTypeHierarchy`, `supertypes`, `subtypes` from tool-lsp operations
- Update operation filtering, description generation, tool schema
- Fix customRequest: param enrichment (opt-in) and error signaling (success=False)
- Update `lsp-general.md` context to remove type hierarchy references
- Update tests

### Phase 1: Build Deprecation Hook
- Create `hooks-deprecation` module in amplifier-foundation
- Implement session:start handler, context injection, source file identification
- Test with a mock deprecated bundle

### Phase 2: Evolve python-dev (absorb lsp-python)
- Move `python-lsp.yaml`, `python-code-intel` agent (rename to `code-intel`), and `python-lsp.md` context from lsp-python into python-dev
- Split current `python-dev.yaml` into `python-quality.yaml` + composite `python-dev.yaml`
- Add explicit capability declarations to python-lsp.yaml
- Update bundle.yaml to use internal behavior instead of lsp-python include
- Move and adapt deep-merge tests

### Phase 3: Build rust-dev (absorb lsp-rust + new quality tools)
- Move LSP content from lsp-rust: behavior, agent (rename to `code-intel`), context
- Create behaviors: `rust-lsp.yaml`, `rust-quality.yaml`, `rust-dev.yaml` (composite)
- Build shared core: checker.py (cargo fmt/clippy/check + stubs), config.py, models.py
- Build tool-rust-check and hooks-rust-check modules
- Create rust-dev agent, context files, and RUST_BEST_PRACTICES.md
- Create bundle.yaml and pyproject.toml

### Phase 4: Build typescript-dev (absorb lsp-typescript + new quality tools)
- Move LSP content from lsp-typescript: behavior, agent (rename to `code-intel`), context, examples
- Create behaviors: `typescript-lsp.yaml`, `typescript-quality.yaml`, `typescript-dev.yaml` (composite)
- Build shared core: checker.py (prettier/eslint/tsc + stubs), config.py, models.py
- Build tool-typescript-check and hooks-typescript-check modules
- Create typescript-dev agent and context files
- Wire up TypeScript language config in LSP tool (not currently configured)
- Live-test TypeScript LSP capabilities and set explicit declarations

### Phase 5: Stub Old Repos
- Replace bundle.yaml in lsp-python, lsp-rust, lsp-typescript with forwarding stubs
- Add deprecation hook config to each
- Update READMEs with deprecation notices

### Phase 6: Update Cross-References
- Update amplifier-foundation includes if it references lsp-python directly
- Update documentation and example bundles referencing old bundle names

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Foundation includes lsp-python directly -- breaking change | Medium | High | Forwarding stubs ensure transparent fallback; update foundation in same PR |
| customRequest fix introduces regressions | Low | Medium | Targeted changes (2 lines), extensive existing test suite (16 test files) |
| TypeScript tooling fragmentation (prettier/eslint may not be installed) | High | Low | Graceful TOOL-NOT-FOUND handling, same pattern as Python |
| Rust diagnostics push/pull mismatch | Known | Medium | rust-dev quality tools (cargo check) provide reliable alternative path; document LSP limitation |
| Agent naming change breaks existing delegate references | Low | Medium | Old lsp-python/lsp-rust bundles aren't widely used yet (experimental) |

## Open Questions

1. Can the base tool-lsp support per-language suppression of base operations (e.g., `goToImplementation: false` for Python)? If not, document in context.
2. Does the bundle loader expose provenance metadata that the deprecation hook can use for source file identification? If not, fall back to file scanning.
3. What TypeScript LSP operations actually work? Live testing needed during Phase 4.
4. Should the rust-dev quality tools parse `cargo check` JSON output for diagnostics (supplementing or replacing LSP pull diagnostics)?
