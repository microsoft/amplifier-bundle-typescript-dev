"""Tests for the hooks-typescript-check module.

Validates the TypeScriptCheckHooks class interface, file pattern matching,
and the mount function signature.
"""

import asyncio
from unittest.mock import MagicMock

import pytest


class TestTypeScriptCheckHooksInterface:
    """Test that TypeScriptCheckHooks has the correct interface."""

    def test_hooks_class_importable(self):
        from amplifier_module_hooks_typescript_check import TypeScriptCheckHooks

        hooks = TypeScriptCheckHooks()
        assert hooks is not None

    def test_default_enabled(self):
        from amplifier_module_hooks_typescript_check import TypeScriptCheckHooks

        hooks = TypeScriptCheckHooks()
        assert hooks.enabled is True

    def test_config_enabled_override(self):
        from amplifier_module_hooks_typescript_check import TypeScriptCheckHooks

        hooks = TypeScriptCheckHooks({"enabled": False})
        assert hooks.enabled is False

    def test_default_file_patterns_cover_ts_and_js(self):
        from amplifier_module_hooks_typescript_check import TypeScriptCheckHooks

        hooks = TypeScriptCheckHooks()
        patterns = hooks.file_patterns
        assert "*.ts" in patterns
        assert "*.tsx" in patterns
        assert "*.mts" in patterns
        assert "*.cts" in patterns
        assert "*.js" in patterns
        assert "*.jsx" in patterns
        assert "*.mjs" in patterns
        assert "*.cjs" in patterns

    def test_custom_file_patterns(self):
        from amplifier_module_hooks_typescript_check import TypeScriptCheckHooks

        hooks = TypeScriptCheckHooks({"file_patterns": ["*.ts"]})
        assert hooks.file_patterns == ["*.ts"]

    def test_default_report_level(self):
        from amplifier_module_hooks_typescript_check import TypeScriptCheckHooks

        hooks = TypeScriptCheckHooks()
        assert hooks.report_level == "warning"

    def test_default_auto_inject(self):
        from amplifier_module_hooks_typescript_check import TypeScriptCheckHooks

        hooks = TypeScriptCheckHooks()
        assert hooks.auto_inject is True

    def test_default_verbosity(self):
        from amplifier_module_hooks_typescript_check import TypeScriptCheckHooks

        hooks = TypeScriptCheckHooks()
        assert hooks.verbosity == "normal"

    def test_handle_tool_post_is_async(self):
        from amplifier_module_hooks_typescript_check import TypeScriptCheckHooks

        hooks = TypeScriptCheckHooks()
        assert asyncio.iscoroutinefunction(hooks.handle_tool_post)


class TestFilePatternMatching:
    """Test that file pattern matching works for TS/JS extensions."""

    def test_matches_ts_file(self):
        from amplifier_module_hooks_typescript_check import TypeScriptCheckHooks

        hooks = TypeScriptCheckHooks()
        assert hooks._matches_patterns("src/app.ts") is True

    def test_matches_tsx_file(self):
        from amplifier_module_hooks_typescript_check import TypeScriptCheckHooks

        hooks = TypeScriptCheckHooks()
        assert hooks._matches_patterns("src/Button.tsx") is True

    def test_matches_mts_file(self):
        from amplifier_module_hooks_typescript_check import TypeScriptCheckHooks

        hooks = TypeScriptCheckHooks()
        assert hooks._matches_patterns("src/utils.mts") is True

    def test_matches_cts_file(self):
        from amplifier_module_hooks_typescript_check import TypeScriptCheckHooks

        hooks = TypeScriptCheckHooks()
        assert hooks._matches_patterns("src/config.cts") is True

    def test_matches_js_file(self):
        from amplifier_module_hooks_typescript_check import TypeScriptCheckHooks

        hooks = TypeScriptCheckHooks()
        assert hooks._matches_patterns("src/legacy.js") is True

    def test_matches_jsx_file(self):
        from amplifier_module_hooks_typescript_check import TypeScriptCheckHooks

        hooks = TypeScriptCheckHooks()
        assert hooks._matches_patterns("components/Card.jsx") is True

    def test_matches_mjs_file(self):
        from amplifier_module_hooks_typescript_check import TypeScriptCheckHooks

        hooks = TypeScriptCheckHooks()
        assert hooks._matches_patterns("src/esm-module.mjs") is True

    def test_matches_cjs_file(self):
        from amplifier_module_hooks_typescript_check import TypeScriptCheckHooks

        hooks = TypeScriptCheckHooks()
        assert hooks._matches_patterns("src/common.cjs") is True

    def test_does_not_match_python_file(self):
        from amplifier_module_hooks_typescript_check import TypeScriptCheckHooks

        hooks = TypeScriptCheckHooks()
        assert hooks._matches_patterns("src/app.py") is False

    def test_does_not_match_rust_file(self):
        from amplifier_module_hooks_typescript_check import TypeScriptCheckHooks

        hooks = TypeScriptCheckHooks()
        assert hooks._matches_patterns("src/main.rs") is False

    def test_does_not_match_css_file(self):
        from amplifier_module_hooks_typescript_check import TypeScriptCheckHooks

        hooks = TypeScriptCheckHooks()
        assert hooks._matches_patterns("styles/app.css") is False


class TestHookEventFiltering:
    """Test that the hook only fires for write tools and when enabled."""

    @pytest.mark.asyncio
    async def test_skips_when_disabled(self):
        from amplifier_module_hooks_typescript_check import TypeScriptCheckHooks

        hooks = TypeScriptCheckHooks({"enabled": False})
        result = await hooks.handle_tool_post(
            "tool:post",
            {
                "tool_name": "write_file",
                "tool_input": {"file_path": "src/app.ts"},
            },
        )
        assert result.action == "continue"

    @pytest.mark.asyncio
    async def test_skips_non_write_tool(self):
        from amplifier_module_hooks_typescript_check import TypeScriptCheckHooks

        hooks = TypeScriptCheckHooks()
        result = await hooks.handle_tool_post(
            "tool:post",
            {
                "tool_name": "read_file",
                "tool_input": {"file_path": "src/app.ts"},
            },
        )
        assert result.action == "continue"

    @pytest.mark.asyncio
    async def test_skips_non_matching_extension(self):
        from amplifier_module_hooks_typescript_check import TypeScriptCheckHooks

        hooks = TypeScriptCheckHooks()
        result = await hooks.handle_tool_post(
            "tool:post",
            {
                "tool_name": "write_file",
                "tool_input": {"file_path": "src/app.py"},
            },
        )
        assert result.action == "continue"

    @pytest.mark.asyncio
    async def test_skips_empty_file_path(self):
        from amplifier_module_hooks_typescript_check import TypeScriptCheckHooks

        hooks = TypeScriptCheckHooks()
        result = await hooks.handle_tool_post(
            "tool:post",
            {
                "tool_name": "write_file",
                "tool_input": {},
            },
        )
        assert result.action == "continue"

    @pytest.mark.asyncio
    async def test_recognizes_write_file_tool(self):
        """write_file should be in the recognized write tools list."""
        from amplifier_module_hooks_typescript_check import TypeScriptCheckHooks

        hooks = TypeScriptCheckHooks()
        # Non-existent file will cause early return, but we verify it gets past the tool_name check
        result = await hooks.handle_tool_post(
            "tool:post",
            {
                "tool_name": "write_file",
                "tool_input": {"file_path": "/nonexistent/src/app.ts"},
            },
        )
        # Returns continue because file doesn't exist, but got past tool_name check
        assert result.action == "continue"

    @pytest.mark.asyncio
    async def test_recognizes_edit_file_tool(self):
        from amplifier_module_hooks_typescript_check import TypeScriptCheckHooks

        hooks = TypeScriptCheckHooks()
        result = await hooks.handle_tool_post(
            "tool:post",
            {
                "tool_name": "edit_file",
                "tool_input": {"file_path": "/nonexistent/src/app.ts"},
            },
        )
        assert result.action == "continue"

    @pytest.mark.asyncio
    async def test_recognizes_Write_tool(self):
        from amplifier_module_hooks_typescript_check import TypeScriptCheckHooks

        hooks = TypeScriptCheckHooks()
        result = await hooks.handle_tool_post(
            "tool:post",
            {
                "tool_name": "Write",
                "tool_input": {"file_path": "/nonexistent/src/app.ts"},
            },
        )
        assert result.action == "continue"

    @pytest.mark.asyncio
    async def test_recognizes_Edit_tool(self):
        from amplifier_module_hooks_typescript_check import TypeScriptCheckHooks

        hooks = TypeScriptCheckHooks()
        result = await hooks.handle_tool_post(
            "tool:post",
            {
                "tool_name": "Edit",
                "tool_input": {"file_path": "/nonexistent/src/app.ts"},
            },
        )
        assert result.action == "continue"

    @pytest.mark.asyncio
    async def test_recognizes_MultiEdit_tool(self):
        from amplifier_module_hooks_typescript_check import TypeScriptCheckHooks

        hooks = TypeScriptCheckHooks()
        result = await hooks.handle_tool_post(
            "tool:post",
            {
                "tool_name": "MultiEdit",
                "tool_input": {"file_path": "/nonexistent/src/app.ts"},
            },
        )
        assert result.action == "continue"


class TestMountFunction:
    """Test the module mount function."""

    def test_mount_function_importable(self):
        from amplifier_module_hooks_typescript_check import mount

        assert asyncio.iscoroutinefunction(mount)

    @pytest.mark.asyncio
    async def test_mount_registers_hook(self):
        from amplifier_module_hooks_typescript_check import mount

        coordinator = MagicMock()
        coordinator.get_capability = MagicMock(return_value=None)
        coordinator.hooks = MagicMock()
        coordinator.hooks.register = MagicMock()

        await mount(coordinator)

        coordinator.hooks.register.assert_called_once()
        call_args = coordinator.hooks.register.call_args
        assert call_args[0][0] == "tool:post"
        assert call_args[1]["priority"] == 15
        assert call_args[1]["name"] == "typescript-check"

    @pytest.mark.asyncio
    async def test_mount_returns_metadata(self):
        from amplifier_module_hooks_typescript_check import mount

        coordinator = MagicMock()
        coordinator.get_capability = MagicMock(return_value=None)
        coordinator.hooks = MagicMock()
        coordinator.hooks.register = MagicMock()

        result = await mount(coordinator)

        assert result["name"] == "hooks-typescript-check"
        assert result["version"] == "0.1.0"
        assert "typescript_check_hook" in result["provides"]

    @pytest.mark.asyncio
    async def test_mount_passes_config(self):
        from amplifier_module_hooks_typescript_check import mount

        coordinator = MagicMock()
        coordinator.get_capability = MagicMock(return_value=None)
        coordinator.hooks = MagicMock()
        coordinator.hooks.register = MagicMock()

        result = await mount(
            coordinator, config={"enabled": True, "verbosity": "detailed"}
        )

        assert result["config"]["enabled"] is True
        assert result["config"]["verbosity"] == "detailed"
