"""Amplifier tool module for TypeScript/JavaScript code quality checks.

This module provides the `typescript_check` tool that agents can use to
check TypeScript/JavaScript code for formatting, linting, type errors, and stubs.
"""

from typing import Any

from amplifier_core import ToolResult
from amplifier_bundle_typescript_dev import CheckConfig, check_content, check_files


class TypeScriptCheckTool:
    """Tool for checking TypeScript/JavaScript code quality."""

    @property
    def name(self) -> str:
        return "typescript_check"

    @property
    def description(self) -> str:
        return """Check TypeScript/JavaScript code for quality issues.

Runs prettier (formatting), eslint (linting), tsc (type checking), and stub detection
on TypeScript and JavaScript files or code content.

Input options:
- paths: List of file paths or directories to check
- content: TypeScript/JavaScript code as a string to check
- fix: If true, auto-fix issues where possible (only works with paths)

Examples:
- Check a file: {"paths": ["src/main.ts"]}
- Check a directory: {"paths": ["src/"]}
- Check multiple paths: {"paths": ["src/", "tests/"]}
- Check code string: {"content": "const x: number = 'hello';"}
- Auto-fix issues: {"paths": ["src/"], "fix": true}

Returns:
- success: True if no errors (warnings are OK)
- clean: True if no issues at all
- summary: Human-readable summary
- issues: List of issues with file, line, code, message, severity"""

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of file paths or directories to check",
                },
                "content": {
                    "type": "string",
                    "description": "TypeScript/JavaScript code as a string to check (alternative to paths)",
                },
                "fix": {
                    "type": "boolean",
                    "description": "Auto-fix issues where possible",
                    "default": False,
                },
                "checks": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["format", "lint", "types", "stubs"],
                    },
                    "description": "Specific checks to run (default: all)",
                },
            },
        }

    async def execute(self, input_data: dict[str, Any]) -> ToolResult:
        """Execute the TypeScript/JavaScript check tool."""
        paths = input_data.get("paths")
        content = input_data.get("content")
        fix = input_data.get("fix", False)
        checks = input_data.get("checks")

        config_overrides = {}
        if checks:
            config_overrides["enable_prettier"] = "format" in checks
            config_overrides["enable_eslint"] = "lint" in checks
            config_overrides["enable_tsc"] = "types" in checks
            config_overrides["enable_stub_check"] = "stubs" in checks

        config = CheckConfig.from_dict(config_overrides) if config_overrides else None

        if content:
            result = check_content(content, config=config)
        elif paths:
            result = check_files(paths, config=config, fix=fix)
        else:
            result = check_files(["."], config=config, fix=fix)

        return ToolResult(success=result.success, output=result.to_tool_output())


async def mount(
    coordinator: Any, config: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Mount the typescript_check tool into the coordinator."""
    tool = TypeScriptCheckTool()
    await coordinator.mount("tools", tool, name=tool.name)

    return {
        "name": "tool-typescript-check",
        "version": "0.1.0",
        "provides": ["typescript_check"],
    }
