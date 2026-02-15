"""Tests for agent and context files.

Validates that the typescript-dev agent and context files exist,
have correct structure, and contain required content.
"""

from pathlib import Path

import yaml

BUNDLE_ROOT = Path(__file__).parent.parent


class TestTypescriptDevAgent:
    """Test the typescript-dev.md agent file."""

    def test_agent_file_exists(self):
        path = BUNDLE_ROOT / "agents" / "typescript-dev.md"
        assert path.exists(), "agents/typescript-dev.md should exist"

    def test_agent_has_yaml_frontmatter(self):
        path = BUNDLE_ROOT / "agents" / "typescript-dev.md"
        content = path.read_text()
        assert content.startswith("---"), "Agent should start with YAML frontmatter"
        parts = content.split("---", 2)
        assert len(parts) >= 3, "Agent should have opening and closing --- delimiters"

    def test_agent_meta_name(self):
        path = BUNDLE_ROOT / "agents" / "typescript-dev.md"
        content = path.read_text()
        parts = content.split("---", 2)
        meta = yaml.safe_load(parts[1])
        assert meta["meta"]["name"] == "typescript-dev"

    def test_agent_has_description(self):
        path = BUNDLE_ROOT / "agents" / "typescript-dev.md"
        content = path.read_text()
        parts = content.split("---", 2)
        meta = yaml.safe_load(parts[1])
        description = meta["meta"]["description"]
        assert len(description) > 50
        assert "TypeScript" in description

    def test_agent_description_has_examples(self):
        path = BUNDLE_ROOT / "agents" / "typescript-dev.md"
        content = path.read_text()
        parts = content.split("---", 2)
        meta = yaml.safe_load(parts[1])
        description = meta["meta"]["description"]
        assert "<example>" in description
        assert "typescript-dev:typescript-dev" in description

    def test_agent_has_tool_typescript_check(self):
        path = BUNDLE_ROOT / "agents" / "typescript-dev.md"
        content = path.read_text()
        parts = content.split("---", 2)
        meta = yaml.safe_load(parts[1])
        tools = meta.get("tools", [])
        tool_modules = [t["module"] for t in tools]
        assert "tool-typescript-check" in tool_modules

    def test_agent_has_tool_lsp(self):
        path = BUNDLE_ROOT / "agents" / "typescript-dev.md"
        content = path.read_text()
        parts = content.split("---", 2)
        meta = yaml.safe_load(parts[1])
        tools = meta.get("tools", [])
        tool_modules = [t["module"] for t in tools]
        assert "tool-lsp" in tool_modules

    def test_agent_body_mentions_typescript_check(self):
        path = BUNDLE_ROOT / "agents" / "typescript-dev.md"
        content = path.read_text()
        parts = content.split("---", 2)
        body = parts[2]
        assert "typescript_check" in body

    def test_agent_body_mentions_lsp(self):
        path = BUNDLE_ROOT / "agents" / "typescript-dev.md"
        content = path.read_text()
        parts = content.split("---", 2)
        body = parts[2]
        assert "LSP" in body

    def test_agent_body_mentions_both_ts_and_js(self):
        path = BUNDLE_ROOT / "agents" / "typescript-dev.md"
        content = path.read_text()
        parts = content.split("---", 2)
        body = parts[2]
        assert "TypeScript" in body
        assert "JavaScript" in body

    def test_agent_body_mentions_prettier_eslint_tsc(self):
        path = BUNDLE_ROOT / "agents" / "typescript-dev.md"
        content = path.read_text()
        parts = content.split("---", 2)
        body = parts[2]
        assert "prettier" in body.lower()
        assert "eslint" in body.lower()
        assert "tsc" in body.lower()

    def test_agent_body_references_best_practices(self):
        path = BUNDLE_ROOT / "agents" / "typescript-dev.md"
        content = path.read_text()
        assert "TYPESCRIPT_BEST_PRACTICES" in content

    def test_agent_body_includes_common_base(self):
        path = BUNDLE_ROOT / "agents" / "typescript-dev.md"
        content = path.read_text()
        assert "@foundation:context/shared/common-agent-base.md" in content


class TestContextInstructionsFile:
    """Test the typescript-dev-instructions.md context file."""

    def test_file_exists(self):
        path = BUNDLE_ROOT / "context" / "typescript-dev-instructions.md"
        assert path.exists(), "context/typescript-dev-instructions.md should exist"

    def test_mentions_typescript_check_tool(self):
        path = BUNDLE_ROOT / "context" / "typescript-dev-instructions.md"
        content = path.read_text()
        assert "typescript_check" in content

    def test_mentions_lsp_tools(self):
        path = BUNDLE_ROOT / "context" / "typescript-dev-instructions.md"
        content = path.read_text()
        assert "LSP" in content
        assert "hover" in content
        assert "goToDefinition" in content

    def test_mentions_auto_checking_hook(self):
        path = BUNDLE_ROOT / "context" / "typescript-dev-instructions.md"
        content = path.read_text()
        assert "hook" in content.lower() or "Hook" in content
        assert "write_file" in content or "edit_file" in content

    def test_mentions_package_json_config(self):
        path = BUNDLE_ROOT / "context" / "typescript-dev-instructions.md"
        content = path.read_text()
        assert "package.json" in content
        assert "amplifier-typescript-dev" in content

    def test_mentions_supported_extensions(self):
        path = BUNDLE_ROOT / "context" / "typescript-dev-instructions.md"
        content = path.read_text()
        assert ".ts" in content
        assert ".tsx" in content
        assert ".js" in content
        assert ".jsx" in content

    def test_mentions_tool_installation(self):
        path = BUNDLE_ROOT / "context" / "typescript-dev-instructions.md"
        content = path.read_text()
        assert "npm install" in content
        assert "prettier" in content
        assert "eslint" in content

    def test_substantial_content(self):
        path = BUNDLE_ROOT / "context" / "typescript-dev-instructions.md"
        content = path.read_text()
        lines = content.strip().split("\n")
        assert len(lines) >= 50, f"Expected at least 50 lines, got {len(lines)}"


class TestBestPracticesFile:
    """Test the TYPESCRIPT_BEST_PRACTICES.md context file."""

    def test_file_exists(self):
        path = BUNDLE_ROOT / "context" / "TYPESCRIPT_BEST_PRACTICES.md"
        assert path.exists(), "context/TYPESCRIPT_BEST_PRACTICES.md should exist"

    def test_mentions_type_safety(self):
        path = BUNDLE_ROOT / "context" / "TYPESCRIPT_BEST_PRACTICES.md"
        content = path.read_text()
        assert "type safety" in content.lower() or "Type Safety" in content

    def test_mentions_strict_mode(self):
        path = BUNDLE_ROOT / "context" / "TYPESCRIPT_BEST_PRACTICES.md"
        content = path.read_text()
        assert "strict" in content.lower()
        assert "tsconfig" in content.lower()

    def test_mentions_no_any(self):
        path = BUNDLE_ROOT / "context" / "TYPESCRIPT_BEST_PRACTICES.md"
        content = path.read_text()
        assert "any" in content

    def test_mentions_interfaces(self):
        path = BUNDLE_ROOT / "context" / "TYPESCRIPT_BEST_PRACTICES.md"
        content = path.read_text()
        assert "interface" in content.lower()

    def test_mentions_error_handling(self):
        path = BUNDLE_ROOT / "context" / "TYPESCRIPT_BEST_PRACTICES.md"
        content = path.read_text()
        assert "error" in content.lower()

    def test_mentions_modern_patterns(self):
        path = BUNDLE_ROOT / "context" / "TYPESCRIPT_BEST_PRACTICES.md"
        content = path.read_text()
        assert "async" in content.lower() or "await" in content.lower()
        assert "const" in content.lower()

    def test_has_always_do_section(self):
        path = BUNDLE_ROOT / "context" / "TYPESCRIPT_BEST_PRACTICES.md"
        content = path.read_text()
        assert "Always Do" in content or "always do" in content.lower()

    def test_has_never_do_section(self):
        path = BUNDLE_ROOT / "context" / "TYPESCRIPT_BEST_PRACTICES.md"
        content = path.read_text()
        assert "Never Do" in content or "never do" in content.lower()

    def test_substantial_content(self):
        path = BUNDLE_ROOT / "context" / "TYPESCRIPT_BEST_PRACTICES.md"
        content = path.read_text()
        lines = content.strip().split("\n")
        assert len(lines) >= 60, f"Expected at least 60 lines, got {len(lines)}"
