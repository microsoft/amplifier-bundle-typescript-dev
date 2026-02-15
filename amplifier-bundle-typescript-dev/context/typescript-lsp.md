# TypeScript/JavaScript LSP Context

You have access to TypeScript/JavaScript code intelligence via the LSP tool with typescript-language-server.

## Quick Start - Most Useful Operations

| Want to... | Use this |
|------------|----------|
| See what type a variable is | `hover` on the variable |
| Find all usages of a function | `findReferences` on the function name |
| Jump to a function's definition | `goToDefinition` on a call site |
| See what calls a function | `incomingCalls` on the function |
| See what a function calls | `outgoingCalls` on the function |
| Find interface implementations | `goToImplementation` on the interface |

**Tip**: `hover` and `findReferences` are the most reliable. Start with these.

## TypeScript/JavaScript-Specific Capabilities

- **Type Information**: Get precise type hints and inferred types (even in JavaScript!)
- **Module Resolution**: Trace imports across the project (CommonJS, ESM, Node.js)
- **Interface/Type Hierarchies**: Navigate TypeScript interfaces and type definitions
- **JSDoc Support**: Understands JSDoc type annotations in JavaScript
- **React Support**: Recognizes JSX/TSX and component prop types
- **Framework Awareness**: Understands Node.js, Express, React, Next.js patterns

## Effective TypeScript/JavaScript Navigation

### Finding Class/Interface Definitions
1. Position cursor on class/interface name
2. Use `goToDefinition` to find where it's defined
3. Use `findReferences` to see all usages
4. Use `goToImplementation` to find implementations

### Understanding Type Hierarchies
1. Use `hover` on a class/interface to see its structure
2. Use `goToImplementation` to find implementations
3. Navigate inheritance with repeated `goToDefinition`

### Tracing Function Calls
1. Position on function name
2. Use `incomingCalls` to see what calls this function
3. Use `outgoingCalls` to see what this function calls

### Understanding Module Dependencies
1. Use `goToDefinition` on import statements
2. Follow through barrel exports (`index.ts`)
3. Use `documentSymbol` to see module structure

## Common Patterns

### Finding Where a Component is Used (React)
```
1. findReferences on the component name
2. Filter for usage sites (vs import statements)
3. hover on props to see type information
```

### Understanding Express Route Handlers
```
1. goToDefinition on the route handler function
2. hover to see req/res parameter types
3. outgoingCalls to see middleware/service calls
```

### Tracing API Call Flow
```
1. Start at the API endpoint handler
2. outgoingCalls to see service layer
3. Continue tracing with outgoingCalls
4. Use hover to verify request/response types
```

### Finding Type Definitions
```
1. hover on a variable to see its type
2. goToDefinition on the type name
3. documentSymbol to see all type members
```

### Understanding Async/Promise Chains
```
1. hover on async function to see return type
2. goToDefinition on Promise types
3. Trace through .then() chains with outgoingCalls
```

## Workspace Detection

The TypeScript/JavaScript LSP detects workspace root by looking for:
- `tsconfig.json` (preferred for TypeScript projects)
- `jsconfig.json` (preferred for JavaScript projects)
- `package.json` (fallback)
- `.git` directory

Ensure your project has one of these at the root for accurate analysis.

## Configuration Files

### TypeScript Projects
The language server reads `tsconfig.json` to understand:
- Module resolution strategy (`node`, `bundler`, etc.)
- Path mappings for import aliases
- Type checking strictness
- Included/excluded files

Example:
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  }
}
```

### JavaScript Projects
The language server reads `jsconfig.json`:
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "checkJs": true
  },
  "exclude": ["node_modules"]
}
```

## Known Limitations

### TypeScript Language Server Specifics

- **goToImplementation**: Works but may be slow in large workspaces with many interfaces
  - **Workaround**: Use `findReferences` on the interface and filter for `implements` keyword

- **workspaceSymbol**: May return empty on first use before workspace is indexed
  - **Workaround**: Run `documentSymbol` on relevant files first to trigger indexing, then retry

- **Complex Generic Types**: Very complex conditional/mapped types may show simplified versions
  - **Workaround**: Use `hover` at intermediate steps to see resolved types

- **Dynamic Imports**: `import()` expressions may not resolve perfectly
  - **Workaround**: Use `findReferences` to find usages instead

### Type Resolution

- **Missing Type Definitions**: Code may show `any` type if `@types/*` packages aren't installed
- **Complex Type Inference**: Some patterns may not infer perfectly (use explicit annotations)
- **Circular Dependencies**: May cause incomplete type information in some cases

## Common Installation Issues

### typescript-language-server not found

Install both the language server and TypeScript compiler:
```bash
npm install -g typescript-language-server typescript
```

Verify installation:
```bash
typescript-language-server --version
tsc --version
```

### npm install succeeds but LSP still fails

The new installation might be shadowed by an older one earlier in PATH:

1. **Check**: `which -a typescript-language-server` to see all locations
2. **Remove stale ones**: Usually in `~/.local/bin/` or old installation paths
3. **Verify**: The first result of `which typescript-language-server` should be the working one

### Server fails with "Cannot find module 'typescript'"

The language server needs TypeScript installed:
```bash
npm install -g typescript
```

Or install it locally in your project:
```bash
npm install --save-dev typescript
```

### Types not resolving for Node.js/React/etc.

Install the appropriate type definitions:
```bash
# For Node.js
npm install --save-dev @types/node

# For React
npm install --save-dev @types/react @types/react-dom

# For Express
npm install --save-dev @types/express

# For Jest
npm install --save-dev @types/jest
```

### Using nvm (Node Version Manager)

If using nvm, ensure the correct Node.js version is activated:
```bash
nvm use --lts
# or
nvm use 18
```

The language server needs to be installed in the active Node.js environment.

## Framework-Specific Notes

### React Projects
- JSX/TSX syntax is fully supported
- Component prop types are inferred from usage
- Hooks like `useState`, `useEffect` have proper types
- Context API types flow correctly

### Node.js Projects
- Built-in modules (`fs`, `path`, `http`) are recognized
- `require()` and `module.exports` work alongside ESM
- `@types/node` provides Node.js API types

### Express Projects
- Request/Response types from `@types/express`
- Middleware signatures are properly typed
- Route parameter types can be inferred

### Next.js Projects
- Page component types (`GetServerSideProps`, etc.)
- API route handlers have proper types
- File-based routing is understood

## Best Practices

1. **Use `hover` liberally** - It's the fastest way to understand types
2. **Start with `findReferences`** - More reliable than grep for code
3. **Follow imports with `goToDefinition`** - Understand module structure
4. **Check types at error sites** - Use `hover` to diagnose type mismatches
5. **Install type definitions** - Add `@types/*` packages for better inference

## Performance Tips

- Large workspaces may take 5-10 seconds to index
- First `workspaceSymbol` call triggers indexing
- Subsequent operations are fast once indexed
- Close unused files to reduce memory usage