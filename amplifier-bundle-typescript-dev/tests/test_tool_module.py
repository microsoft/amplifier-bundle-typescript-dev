"""Tests for the tool-typescript-check module.

Validates the TypeScriptCheckTool class interface and the mount function signature.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest


class TestTypeScriptCheckToolInterface:
    """Test that TypeScriptCheckTool has the correct interface."""

    def test_tool_class_importable(self):
        from amplifier_module_tool_typescript_check import TypeScriptCheckTool

        tool = TypeScriptCheckTool()
        assert tool is not None

    def test_tool_name_is_typescript_check(self):
        from amplifier_module_tool_typescript_check import TypeScriptCheckTool

        tool = TypeScriptCheckTool()
        assert tool.name == "typescript_check"

    def test_tool_has_description(self):
        from amplifier_module_tool_typescript_check import TypeScriptCheckTool

        tool = TypeScriptCheckTool()
        assert len(tool.description) > 50
        assert "TypeScript" in tool.description or "typescript" in tool.description

    def test_input_schema_has_paths(self):
        from amplifier_module_tool_typescript_check import TypeScriptCheckTool

        tool = TypeScriptCheckTool()
        schema = tool.input_schema
        assert "properties" in schema
        assert "paths" in schema["properties"]
        assert schema["properties"]["paths"]["type"] == "array"

    def test_input_schema_has_content(self):
        from amplifier_module_tool_typescript_check import TypeScriptCheckTool

        tool = TypeScriptCheckTool()
        schema = tool.input_schema
        assert "content" in schema["properties"]
        assert schema["properties"]["content"]["type"] == "string"

    def test_input_schema_has_fix(self):
        from amplifier_module_tool_typescript_check import TypeScriptCheckTool

        tool = TypeScriptCheckTool()
        schema = tool.input_schema
        assert "fix" in schema["properties"]
        assert schema["properties"]["fix"]["type"] == "boolean"

    def test_input_schema_has_checks(self):
        from amplifier_module_tool_typescript_check import TypeScriptCheckTool

        tool = TypeScriptCheckTool()
        schema = tool.input_schema
        assert "checks" in schema["properties"]
        checks_items = schema["properties"]["checks"]["items"]
        assert set(checks_items["enum"]) == {"format", "lint", "types", "stubs"}

    def test_execute_is_async(self):
        from amplifier_module_tool_typescript_check import TypeScriptCheckTool

        tool = TypeScriptCheckTool()
        assert asyncio.iscoroutinefunction(tool.execute)


class TestMountFunction:
    """Test the module mount function."""

    def test_mount_function_importable(self):
        from amplifier_module_tool_typescript_check import mount

        assert asyncio.iscoroutinefunction(mount)

    @pytest.mark.asyncio
    async def test_mount_registers_tool(self):
        from amplifier_module_tool_typescript_check import mount

        coordinator = MagicMock()
        coordinator.mount = AsyncMock()

        await mount(coordinator)

        coordinator.mount.assert_called_once()
        call_args = coordinator.mount.call_args
        assert call_args[0][0] == "tools"
        assert call_args[1]["name"] == "typescript_check"

    @pytest.mark.asyncio
    async def test_mount_returns_metadata(self):
        from amplifier_module_tool_typescript_check import mount

        coordinator = MagicMock()
        coordinator.mount = AsyncMock()

        result = await mount(coordinator)

        assert result["name"] == "tool-typescript-check"
        assert result["version"] == "0.1.0"
        assert "typescript_check" in result["provides"]
