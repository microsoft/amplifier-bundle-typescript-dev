# TypeScript/JavaScript Development Tools

This bundle provides comprehensive TypeScript and JavaScript development capabilities for Amplifier.

## Available Tools

### typescript_check

Run code quality checks on TypeScript/JavaScript files or code content.

```
typescript_check(paths=["src/"])           # Check a directory
typescript_check(paths=["src/main.ts"])    # Check a specific file
typescript_check(content="const x = 1")   # Check code string
typescript_check(paths=["src/"], fix=True) # Auto-fix issues
```

**Checks performed:**
- **prettier**: Code formatting
- **eslint**: Linting rules (configurable per project)
- **tsc**: TypeScript type checking (project-wide, TS files only)
- **stub detection**: TODOs, @ts-ignore, placeholders, unimplemented errors

**Supported file types:**
- TypeScript: `.ts`, `.tsx`, `.mts`, `.cts`
- JavaScript: `.js`, `.jsx`, `.mjs`, `.cjs`

### LSP Tools (via typescript-language-server)

Semantic code intelligence for TypeScript AND JavaScript:

| Tool | Use For |
|------|---------|
| `hover` | Get type info, JSDoc, and inferred types |
| `goToDefinition` | Find where a symbol is defined |
| `findReferences` | Find all usages of a symbol |
| `incomingCalls` | What calls this function? |
| `outgoingCalls` | What does this function call? |
| `goToImplementation` | Find interface implementations |

## Automatic Checking Hook

When enabled, TypeScript/JavaScript files are automatically checked after write/edit operations.

**Behavior:**
- Triggers on `write_file`, `edit_file`, and similar tools
- Checks `.ts`, `.tsx`, `.js`, `.jsx` (and `.mts`, `.cts`, `.mjs`, `.cjs`) files
- Runs lint and type checks (fast subset)
- Injects issues into agent context for awareness

**Configuration** (in `package.json`):
```json
{
  "amplifier-typescript-dev": {
    "hook": {
      "enabled": true,
      "file_patterns": ["*.ts", "*.tsx", "*.js", "*.jsx"],
      "report_level": "warning",
      "auto_inject": true
    }
  }
}
```

## Configuration

Configure via `package.json`:

```json
{
  "amplifier-typescript-dev": {
    "enable_prettier": true,
    "enable_eslint": true,
    "enable_tsc": true,
    "enable_stub_check": true,
    "exclude_patterns": [
      "node_modules/**",
      "dist/**",
      "build/**"
    ]
  }
}
```

## Tool Availability

TypeScript tools are project-local (in `node_modules/.bin/`). If a tool is not installed, the checker reports `TOOL-NOT-FOUND` with installation instructions:

| Tool | Install Command |
|------|----------------|
| prettier | `npm install --save-dev prettier` |
| eslint | `npm install --save-dev eslint` |
| tsc | `npm install --save-dev typescript` |

## Best Practices

See @typescript-dev:context/TYPESCRIPT_BEST_PRACTICES.md for the full development philosophy.

**Key points:**
1. Run `typescript_check` after writing TypeScript/JavaScript code
2. Fix issues immediately — don't accumulate debt
3. Use LSP tools to understand code before modifying
4. Enable `strict` mode in tsconfig.json
5. Type boundaries, not everything — infer internal types
