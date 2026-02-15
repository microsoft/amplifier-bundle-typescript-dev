# amplifier-bundle-typescript-dev

Comprehensive TypeScript/JavaScript development tools for Amplifier.

Provides:
- **LSP integration** — typescript-language-server for code intelligence
- **Code quality** — prettier, eslint, tsc integration
- **Auto-checking** — hooks that run on file write/edit
- **Stub detection** — identifies TODO, FIXME, @ts-ignore patterns
- **Expert agents** — typescript-dev (quality) + code-intel (LSP navigation)

## Usage

```yaml
includes:
  - bundle: git+https://github.com/microsoft/amplifier-bundle-typescript-dev@main
```

## License

This project is licensed under the MIT License.
