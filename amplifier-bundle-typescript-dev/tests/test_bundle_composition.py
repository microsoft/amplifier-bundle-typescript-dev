"""Validate typescript-dev bundle composition.

Tests for behavior YAML structure, deep merge configuration,
namespace consistency, agent frontmatter, and file structure.
Both TypeScript AND JavaScript language configs are validated.
"""

from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent


def deep_merge(base, overlay):
    result = base.copy()
    for key, value in overlay.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _load_behavior(name: str) -> dict:
    """Load a behavior YAML file."""
    path = ROOT / "behaviors" / f"{name}.yaml"
    assert path.exists(), f"Behavior file not found: {path}"
    with open(path) as f:
        return yaml.safe_load(f)


# -- LSP behavior tests (adapted from lsp-typescript) ---------------------


class TestTypescriptLspBehavior:
    """Tests for the typescript-lsp behavior (absorbed from lsp-typescript)."""

    def test_behavior_has_bundle_metadata(self):
        data = _load_behavior("typescript-lsp")
        assert "bundle" in data
        assert data["bundle"]["name"] == "behavior-typescript-lsp"

    def test_includes_lsp_core(self):
        data = _load_behavior("typescript-lsp")
        includes = data.get("includes", [])
        assert len(includes) >= 1
        lsp_core_url = includes[0]["bundle"]
        assert "amplifier-bundle-lsp" in lsp_core_url
        assert "lsp-core" in lsp_core_url

    def test_configures_tool_lsp(self):
        data = _load_behavior("typescript-lsp")
        tools = data.get("tools", [])
        assert len(tools) >= 1
        assert tools[0]["module"] == "tool-lsp"

    def test_typescript_language_config(self):
        """TypeScript language config has correct extensions and server."""
        data = _load_behavior("typescript-lsp")
        languages = data["tools"][0]["config"]["languages"]
        assert "typescript" in languages

        ts = languages["typescript"]
        assert ".ts" in ts["extensions"]
        assert ".tsx" in ts["extensions"]
        assert ".mts" in ts["extensions"]
        assert ".cts" in ts["extensions"]
        assert "tsconfig.json" in ts["workspace_markers"]
        assert ts["server"]["command"] == ["typescript-language-server", "--stdio"]

    def test_javascript_language_config(self):
        """JavaScript language config has correct extensions and server."""
        data = _load_behavior("typescript-lsp")
        languages = data["tools"][0]["config"]["languages"]
        assert "javascript" in languages

        js = languages["javascript"]
        assert ".js" in js["extensions"]
        assert ".jsx" in js["extensions"]
        assert ".mjs" in js["extensions"]
        assert ".cjs" in js["extensions"]
        assert "jsconfig.json" in js["workspace_markers"]
        assert js["server"]["command"] == ["typescript-language-server", "--stdio"]

    def test_both_languages_use_same_server(self):
        """TypeScript and JavaScript must use the same server command."""
        data = _load_behavior("typescript-lsp")
        languages = data["tools"][0]["config"]["languages"]
        ts_cmd = languages["typescript"]["server"]["command"]
        js_cmd = languages["javascript"]["server"]["command"]
        assert ts_cmd == js_cmd, "TypeScript and JavaScript must use the same server"

    def test_typescript_config_merges(self):
        """TypeScript language config merges into lsp-core's empty languages slot."""
        data = _load_behavior("typescript-lsp")
        ts_config = next(t["config"] for t in data["tools"] if t["module"] == "tool-lsp")
        core_config = {"languages": {}, "timeout_seconds": 30}
        merged = deep_merge(core_config, ts_config)
        assert "typescript" in merged["languages"]
        assert "javascript" in merged["languages"]
        assert merged["timeout_seconds"] == 30

    def test_typescript_has_inlay_hint_options(self):
        data = _load_behavior("typescript-lsp")
        ts = data["tools"][0]["config"]["languages"]["typescript"]
        prefs = ts["initialization_options"]["preferences"]
        assert prefs["includeInlayParameterNameHints"] == "all"
        assert prefs["includeInlayFunctionParameterTypeHints"] is True
        assert prefs["includeInlayVariableTypeHints"] is True

    def test_typescript_capabilities_declared(self):
        """TypeScript language declares goToImplementation: true."""
        data = _load_behavior("typescript-lsp")
        caps = data["tools"][0]["config"]["languages"]["typescript"]["capabilities"]
        assert caps.get("diagnostics") is True
        assert caps.get("rename") is True
        assert caps.get("codeAction") is True
        assert caps.get("inlayHints") is True
        assert caps.get("goToImplementation") is True

    def test_javascript_capabilities_declared(self):
        """JavaScript language declares goToImplementation: true."""
        data = _load_behavior("typescript-lsp")
        caps = data["tools"][0]["config"]["languages"]["javascript"]["capabilities"]
        assert caps.get("diagnostics") is True
        assert caps.get("rename") is True
        assert caps.get("codeAction") is True
        assert caps.get("inlayHints") is True
        assert caps.get("goToImplementation") is True

    def test_typescript_server_config_complete(self):
        """TypeScript server config has all required fields."""
        data = _load_behavior("typescript-lsp")
        ts = data["tools"][0]["config"]["languages"]["typescript"]
        assert "extensions" in ts
        assert "workspace_markers" in ts
        assert "server" in ts
        assert "command" in ts["server"]
        assert "install_check" in ts["server"]
        assert "install_hint" in ts["server"]

    def test_javascript_server_config_complete(self):
        """JavaScript server config has all required fields."""
        data = _load_behavior("typescript-lsp")
        js = data["tools"][0]["config"]["languages"]["javascript"]
        assert "extensions" in js
        assert "workspace_markers" in js
        assert "server" in js
        assert "command" in js["server"]
        assert "install_check" in js["server"]
        assert "install_hint" in js["server"]

    def test_lsp_behavior_references_typescript_dev_namespace(self):
        """LSP behavior should reference typescript-dev namespace, not lsp-typescript."""
        data = _load_behavior("typescript-lsp")
        # Context should reference typescript-dev:
        context_includes = data.get("context", {}).get("include", [])
        assert any("typescript-dev:" in c for c in context_includes)
        assert not any("lsp-typescript:" in c for c in context_includes)
        # Agent should reference typescript-dev:
        agent_includes = data.get("agents", {}).get("include", [])
        assert any("typescript-dev:" in a for a in agent_includes)

    def test_registers_code_intel_agent(self):
        data = _load_behavior("typescript-lsp")
        agents = data.get("agents", {}).get("include", [])
        assert "typescript-dev:code-intel" in agents

    def test_includes_lsp_context(self):
        data = _load_behavior("typescript-lsp")
        context = data.get("context", {}).get("include", [])
        assert "typescript-dev:context/typescript-lsp.md" in context


# -- Quality behavior tests -----------------------------------------


class TestTypescriptQualityBehavior:
    """Tests for the typescript-quality behavior."""

    def test_behavior_has_bundle_metadata(self):
        data = _load_behavior("typescript-quality")
        assert data["bundle"]["name"] == "behavior-typescript-quality"

    def test_quality_behavior_has_tool(self):
        """Quality behavior declares tool-typescript-check."""
        data = _load_behavior("typescript-quality")
        tools = data.get("tools", [])
        assert any(t["module"] == "tool-typescript-check" for t in tools)

    def test_quality_behavior_has_hook(self):
        """Quality behavior declares hooks-typescript-check."""
        data = _load_behavior("typescript-quality")
        hooks = data.get("hooks", [])
        assert any(h["module"] == "hooks-typescript-check" for h in hooks)

    def test_hook_file_patterns_cover_ts_and_js(self):
        """Hook file patterns include both TypeScript and JavaScript extensions."""
        data = _load_behavior("typescript-quality")
        hooks = data.get("hooks", [])
        hook_config = hooks[0]["config"]
        patterns = hook_config["file_patterns"]
        # TypeScript patterns
        assert "*.ts" in patterns
        assert "*.tsx" in patterns
        assert "*.mts" in patterns
        assert "*.cts" in patterns
        # JavaScript patterns
        assert "*.js" in patterns
        assert "*.jsx" in patterns
        assert "*.mjs" in patterns
        assert "*.cjs" in patterns

    def test_registers_typescript_dev_agent(self):
        """Quality behavior registers the typescript-dev agent."""
        data = _load_behavior("typescript-quality")
        agents = data.get("agents", {}).get("include", [])
        assert "typescript-dev:typescript-dev" in agents

    def test_includes_instructions_context(self):
        """Quality behavior includes instructions context."""
        data = _load_behavior("typescript-quality")
        context = data.get("context", {}).get("include", [])
        assert "typescript-dev:context/typescript-dev-instructions.md" in context

    def test_tool_has_git_source(self):
        """Tool module has a git source URL."""
        data = _load_behavior("typescript-quality")
        tool = next(t for t in data["tools"] if t["module"] == "tool-typescript-check")
        assert "source" in tool
        assert "amplifier-bundle-typescript-dev" in tool["source"]

    def test_hook_has_git_source(self):
        """Hook module has a git source URL."""
        data = _load_behavior("typescript-quality")
        hook = next(h for h in data["hooks"] if h["module"] == "hooks-typescript-check")
        assert "source" in hook
        assert "amplifier-bundle-typescript-dev" in hook["source"]


# -- Composite behavior tests ---------------------------------------


class TestTypescriptDevBehavior:
    """Tests for the typescript-dev composite behavior."""

    def test_behavior_has_bundle_metadata(self):
        data = _load_behavior("typescript-dev")
        assert data["bundle"]["name"] == "behavior-typescript-dev"

    def test_composite_includes_lsp(self):
        """Composite behavior includes typescript-lsp behavior."""
        data = _load_behavior("typescript-dev")
        includes = [i["bundle"] for i in data.get("includes", [])]
        assert "typescript-dev:behaviors/typescript-lsp" in includes

    def test_composite_includes_quality(self):
        """Composite behavior includes typescript-quality behavior."""
        data = _load_behavior("typescript-dev")
        includes = [i["bundle"] for i in data.get("includes", [])]
        assert "typescript-dev:behaviors/typescript-quality" in includes

    def test_composite_has_no_direct_tools(self):
        """Composite behavior should only include sub-behaviors, not define tools."""
        data = _load_behavior("typescript-dev")
        assert "tools" not in data or data.get("tools") is None, "Composite should not define tools directly"
        assert "hooks" not in data or data.get("hooks") is None, "Composite should not define hooks directly"

    def test_composite_has_no_agents(self):
        """Composite behavior delegates agent registration to sub-behaviors."""
        data = _load_behavior("typescript-dev")
        assert "agents" not in data or data.get("agents") is None

    def test_composite_has_no_context(self):
        """Composite behavior delegates context to sub-behaviors."""
        data = _load_behavior("typescript-dev")
        assert "context" not in data or data.get("context") is None


# -- Bundle metadata tests ------------------------------------------


class TestBundleMetadata:
    """Tests for the root bundle.yaml."""

    def test_bundle_yaml_exists(self):
        assert (ROOT / "bundle.yaml").exists()

    def test_bundle_name(self):
        """Root bundle has correct name."""
        bundle = yaml.safe_load((ROOT / "bundle.yaml").read_text())
        assert bundle["bundle"]["name"] == "typescript-dev"

    def test_bundle_has_version(self):
        """Root bundle has a version."""
        bundle = yaml.safe_load((ROOT / "bundle.yaml").read_text())
        assert "version" in bundle["bundle"]

    def test_bundle_includes_composite(self):
        """Root bundle includes the composite behavior."""
        bundle = yaml.safe_load((ROOT / "bundle.yaml").read_text())
        includes = bundle.get("includes", [])
        assert any("typescript-dev" in str(i) for i in includes)

    def test_bundle_uses_internal_composite(self):
        """bundle.yaml includes the internal composite behavior."""
        bundle = yaml.safe_load((ROOT / "bundle.yaml").read_text())
        includes = bundle["includes"]
        assert len(includes) == 1
        assert includes[0]["bundle"] == "typescript-dev:behaviors/typescript-dev"


# -- Agent tests -----------------------------------------------------


class TestAgents:
    """Tests for agent files."""

    def test_code_intel_agent_name(self):
        """code-intel agent has correct name in frontmatter."""
        content = (ROOT / "agents" / "code-intel.md").read_text()
        parts = content.split("---", 2)
        assert len(parts) >= 3
        meta = yaml.safe_load(parts[1])
        assert meta["meta"]["name"] == "code-intel"

    def test_code_intel_agent_mentions_lsp(self):
        """code-intel agent description mentions LSP capabilities."""
        content = (ROOT / "agents" / "code-intel.md").read_text()
        parts = content.split("---", 2)
        meta = yaml.safe_load(parts[1])
        desc = meta["meta"]["description"].lower()
        assert "lsp" in desc or "language server" in desc

    def test_typescript_dev_agent_name(self):
        """typescript-dev agent has correct name in frontmatter."""
        content = (ROOT / "agents" / "typescript-dev.md").read_text()
        parts = content.split("---", 2)
        meta = yaml.safe_load(parts[1])
        assert meta["meta"]["name"] == "typescript-dev"

    def test_typescript_dev_agent_has_both_tools(self):
        """typescript-dev agent declares both tool-typescript-check and tool-lsp."""
        content = (ROOT / "agents" / "typescript-dev.md").read_text()
        parts = content.split("---", 2)
        meta = yaml.safe_load(parts[1])
        modules = [t["module"] for t in meta["tools"]]
        assert "tool-typescript-check" in modules
        assert "tool-lsp" in modules

    def test_typescript_dev_agent_description_mentions_quality(self):
        """typescript-dev agent description mentions code quality."""
        content = (ROOT / "agents" / "typescript-dev.md").read_text()
        parts = content.split("---", 2)
        meta = yaml.safe_load(parts[1])
        desc = meta["meta"]["description"].lower()
        assert "quality" in desc or "linting" in desc or "formatting" in desc


# -- Namespace consistency tests ----------------------------------------


class TestNamespaceConsistency:
    """No stale lsp-typescript: namespace references."""

    def test_no_lsp_typescript_namespace_in_behaviors(self):
        """No behavior file should reference the old lsp-typescript: namespace."""
        for yaml_file in (ROOT / "behaviors").glob("*.yaml"):
            content = yaml_file.read_text()
            assert "lsp-typescript:" not in content, f"{yaml_file.name} still references lsp-typescript: namespace"

    def test_no_lsp_typescript_namespace_in_agents(self):
        """No agent file should reference the old lsp-typescript: namespace."""
        for md_file in (ROOT / "agents").glob("*.md"):
            content = md_file.read_text()
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = parts[1]
                assert "lsp-typescript:" not in frontmatter, (
                    f"{md_file.name} frontmatter references lsp-typescript: namespace"
                )

    def test_no_lsp_typescript_namespace_in_bundle(self):
        """bundle.yaml should not reference the old lsp-typescript: namespace."""
        content = (ROOT / "bundle.yaml").read_text()
        assert "lsp-typescript:" not in content


# -- Context file tests -----------------------------------------------


class TestContext:
    """Tests for context files."""

    def test_typescript_lsp_context_exists(self):
        assert (ROOT / "context" / "typescript-lsp.md").exists()

    def test_typescript_dev_instructions_exists(self):
        assert (ROOT / "context" / "typescript-dev-instructions.md").exists()

    def test_typescript_best_practices_exists(self):
        assert (ROOT / "context" / "TYPESCRIPT_BEST_PRACTICES.md").exists()

    def test_typescript_lsp_context_no_old_namespace(self):
        """typescript-lsp.md should not reference old lsp-typescript namespace."""
        content = (ROOT / "context" / "typescript-lsp.md").read_text()
        assert "typescript-code-intel" not in content


# -- YAML validity tests ------------------------------------------------


class TestYamlValidity:
    """All YAML files should parse without error."""

    def test_all_yaml_valid(self):
        """All YAML files in the bundle parse correctly."""
        for yaml_file in ROOT.rglob("*.yaml"):
            # Skip hidden dirs and caches
            if any(part.startswith(".") or part == "node_modules" for part in yaml_file.parts):
                continue
            content = yaml.safe_load(yaml_file.read_text())
            assert content is not None, f"{yaml_file} is empty or invalid"


# -- File structure tests ------------------------------------------------


class TestFileStructure:
    """All expected files from the bundle are present."""

    def test_expected_files_exist(self):
        """All expected files are present."""
        expected = [
            "bundle.yaml",
            "pyproject.toml",
            "behaviors/typescript-dev.yaml",
            "behaviors/typescript-lsp.yaml",
            "behaviors/typescript-quality.yaml",
            "agents/typescript-dev.md",
            "agents/code-intel.md",
            "context/typescript-dev-instructions.md",
            "context/typescript-lsp.md",
            "context/TYPESCRIPT_BEST_PRACTICES.md",
            "examples/combined-bundle.yaml",
            "docs/ROADMAP.md",
        ]
        for path in expected:
            assert (ROOT / path).exists(), f"Missing expected file: {path}"
