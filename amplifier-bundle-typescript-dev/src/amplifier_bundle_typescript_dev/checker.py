"""Core TypeScript/JavaScript checking logic.

This module contains all the checking logic, shared by:
- Tool module (typescript_check tool for agents)
- Hook module (automatic checks on file events)

All external tools are invoked via npx. Each check handles
missing tools gracefully with a TOOL-NOT-FOUND issue.
"""

import json
import re
import subprocess
from pathlib import Path

from .config import load_config
from .models import ALL_EXTENSIONS
from .models import CheckConfig
from .models import CheckResult
from .models import Issue
from .models import Severity

# Timeout for external tool invocations (seconds)
_TOOL_TIMEOUT = 120


def _make_tool_not_found(tool_name: str, source: str, install_hint: str) -> CheckResult:
    """Create a TOOL-NOT-FOUND result for a missing tool."""
    return CheckResult(
        issues=[
            Issue(
                file="",
                line=0,
                column=0,
                code="TOOL-NOT-FOUND",
                message=f"{tool_name} not found. {install_hint}",
                severity=Severity.ERROR,
                source=source,
            )
        ],
        checks_run=[source],
    )


def _npx_not_found_result(source: str) -> CheckResult:
    """Create a result for when npx itself is not found."""
    return _make_tool_not_found("npx", source, "Install Node.js: https://nodejs.org/")


def _is_tool_missing(stderr: str) -> bool:
    """Check if npx stderr indicates the tool is not installed."""
    indicators = [
        "not found",
        "ERR_MODULE_NOT_FOUND",
        "Cannot find module",
        "command not found",
        "could not determine executable",
    ]
    stderr_lower = stderr.lower()
    return any(ind.lower() in stderr_lower for ind in indicators)


class TypeScriptChecker:
    """Main checker that orchestrates prettier, eslint, tsc, and stub detection."""

    def __init__(self, config: CheckConfig | None = None):
        """Initialize checker with optional config."""
        self.config = config or load_config()

    def check_files(self, paths: list[str | Path], fix: bool = False) -> CheckResult:
        """Run all enabled checks on the given paths.

        Args:
            paths: Files or directories to check
            fix: If True, auto-fix issues where possible

        Returns:
            CheckResult with all issues found
        """
        if not paths:
            paths = [Path.cwd()]

        path_strs = [str(p) for p in paths]
        results = CheckResult(files_checked=self._count_files(path_strs))

        if self.config.enable_prettier:
            results = results.merge(self._run_prettier(path_strs, fix=fix))

        if self.config.enable_eslint:
            results = results.merge(self._run_eslint(path_strs, fix=fix))

        if self.config.enable_tsc:
            results = results.merge(self._run_tsc(path_strs))

        if self.config.enable_stub_check:
            results = results.merge(self._run_stub_check(path_strs))

        return results

    def check_content(self, content: str, filename: str = "stdin.ts") -> CheckResult:
        """Check TypeScript/JavaScript content string.

        Args:
            content: Source code as string
            filename: Virtual filename for error reporting

        Returns:
            CheckResult with issues found

        Note:
            tsc is skipped for content checks (requires tsconfig.json context).
        """
        import tempfile

        suffix = Path(filename).suffix or ".ts"
        with tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            # Skip tsc for content checks — it needs project context
            saved_tsc = self.config.enable_tsc
            self.config.enable_tsc = False
            result = self.check_files([temp_path])
            self.config.enable_tsc = saved_tsc

            for issue in result.issues:
                if issue.file == temp_path:
                    issue.file = filename
            return result
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def _count_files(self, paths: list[str]) -> int:
        """Count TypeScript and JavaScript files in the given paths."""
        count = 0
        for path_str in paths:
            path = Path(path_str)
            if path.is_file() and path.suffix in ALL_EXTENSIONS:
                count += 1
            elif path.is_dir():
                for ext in ALL_EXTENSIONS:
                    count += len(list(path.rglob(f"*{ext}")))
        return count

    def _should_exclude(self, path: Path) -> bool:
        """Check if path matches any exclude pattern."""
        path_str = str(path)
        for pattern in self.config.exclude_patterns:
            if pattern.endswith("/**"):
                dir_pattern = pattern[:-3]
                if dir_pattern in path_str:
                    return True
            elif pattern in path_str:
                return True
        return False

    # -- Prettier ----------------------------------------------------------

    def _run_prettier(self, paths: list[str], fix: bool = False) -> CheckResult:
        """Run prettier format check.

        Uses --check mode (reports files needing formatting) or --write (auto-fix).
        Parses [warn] lines from stderr to identify files (Prettier v3+).
        """
        cmd = ["npx", "prettier"]
        if fix:
            cmd.append("--write")
        else:
            cmd.append("--check")
        cmd.extend(paths)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=_TOOL_TIMEOUT)
        except FileNotFoundError:
            return _npx_not_found_result("prettier")
        except subprocess.TimeoutExpired:
            return CheckResult(
                issues=[
                    Issue(
                        file="",
                        line=0,
                        column=0,
                        code="TIMEOUT",
                        message="prettier check timed out",
                        severity=Severity.ERROR,
                        source="prettier",
                    )
                ],
                checks_run=["prettier"],
            )

        if _is_tool_missing(result.stderr):
            return _make_tool_not_found(
                "prettier",
                "prettier",
                "Install with: npm install --save-dev prettier",
            )

        if result.returncode != 0 and not fix:
            return self._parse_prettier_output(result.stderr)

        return CheckResult(issues=[], checks_run=["prettier"])

    def _parse_prettier_output(self, output: str) -> CheckResult:
        """Parse prettier --check stdout output.

        Prettier --check outputs lines like:
          [warn] src/utils.ts
          [warn] Code style issues found in 2 files. Run Prettier to fix.

        We extract the file paths from [warn] lines, skipping the summary line.
        """
        issues = []

        for line in output.split("\n"):
            # prettier --check outputs: [warn] path/to/file.ts
            if line.startswith("[warn] ") and not line.startswith("[warn] Code style"):
                file_path = line[7:].strip()
                if file_path:
                    issues.append(
                        Issue(
                            file=file_path,
                            line=1,
                            column=1,
                            code="FORMAT",
                            message="File would be reformatted",
                            severity=Severity.WARNING,
                            source="prettier",
                            suggestion="Run with fix=True to auto-format",
                        )
                    )

        return CheckResult(issues=issues, checks_run=["prettier"])

    # -- ESLint -------------------------------------------------------------

    def _run_eslint(self, paths: list[str], fix: bool = False) -> CheckResult:
        """Run eslint linting check.

        Uses --format=json for structured output. Handles both ESLint v8 and v9
        (same JSON format). Maps ESLint severity (1=warning, 2=error) to our model.
        """
        cmd = ["npx", "eslint", "--format=json"]
        if fix:
            cmd.append("--fix")
        cmd.extend(paths)

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=_TOOL_TIMEOUT)
        except FileNotFoundError:
            return _npx_not_found_result("eslint")
        except subprocess.TimeoutExpired:
            return CheckResult(
                issues=[
                    Issue(
                        file="",
                        line=0,
                        column=0,
                        code="TIMEOUT",
                        message="eslint check timed out",
                        severity=Severity.ERROR,
                        source="eslint",
                    )
                ],
                checks_run=["eslint"],
            )

        if _is_tool_missing(result.stderr):
            return _make_tool_not_found(
                "eslint",
                "eslint",
                "Install with: npm install --save-dev eslint",
            )

        # ESLint --format=json outputs to stdout even on error
        return self._parse_eslint_output(result.stdout.strip())

    def _parse_eslint_output(self, output: str) -> CheckResult:
        """Parse eslint --format=json output.

        ESLint JSON format is an array of objects, each with:
          filePath: string
          messages: array of {ruleId, severity, message, line, column, ...}

        ESLint severity: 1=warning, 2=error.
        """
        issues = []

        if not output:
            return CheckResult(issues=[], checks_run=["eslint"])

        try:
            eslint_results = json.loads(output)
            for file_result in eslint_results:
                file_path = file_result.get("filePath", "")
                for msg in file_result.get("messages", []):
                    # ESLint severity: 1=warning, 2=error
                    eslint_sev = msg.get("severity", 2)
                    severity = Severity.WARNING if eslint_sev == 1 else Severity.ERROR

                    rule_id = msg.get("ruleId") or "eslint"
                    suggestion = None
                    if msg.get("fix"):
                        suggestion = "Auto-fixable with --fix"
                    elif msg.get("suggestions"):
                        suggestion = msg["suggestions"][0].get("desc", "Fix available")

                    issues.append(
                        Issue(
                            file=file_path,
                            line=msg.get("line", 0),
                            column=msg.get("column", 0),
                            code=rule_id,
                            message=msg.get("message", ""),
                            severity=severity,
                            source="eslint",
                            suggestion=suggestion,
                            end_line=msg.get("endLine"),
                            end_column=msg.get("endColumn"),
                        )
                    )
        except json.JSONDecodeError:
            pass  # Non-JSON output (config error, etc.) — skip

        return CheckResult(issues=issues, checks_run=["eslint"])

    # -- TSC ----------------------------------------------------------------

    def _run_tsc(self, paths: list[str]) -> CheckResult:
        """Run TypeScript compiler type checking.

        Always runs project-wide (tsc --noEmit) since tsc needs tsconfig.json
        context. The paths argument is ignored — tsc checks the whole project.
        Only applicable to TypeScript files (.ts/.tsx), not plain JavaScript.
        """
        cmd = ["npx", "tsc", "--noEmit", "--pretty", "false"]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=_TOOL_TIMEOUT)
        except FileNotFoundError:
            return _npx_not_found_result("tsc")
        except subprocess.TimeoutExpired:
            return CheckResult(
                issues=[
                    Issue(
                        file="",
                        line=0,
                        column=0,
                        code="TIMEOUT",
                        message="tsc check timed out",
                        severity=Severity.ERROR,
                        source="tsc",
                    )
                ],
                checks_run=["tsc"],
            )

        if _is_tool_missing(result.stderr):
            return _make_tool_not_found(
                "typescript",
                "tsc",
                "Install with: npm install --save-dev typescript",
            )

        # tsc outputs to stdout with --pretty false
        output = result.stdout if result.stdout else result.stderr
        return self._parse_tsc_output(output)

    def _parse_tsc_output(self, output: str) -> CheckResult:
        """Parse tsc --noEmit --pretty false output.

        Format: file(line,col): error TS1234: message
        """
        issues = []
        tsc_pattern = re.compile(r"^(.+)\((\d+),(\d+)\):\s+(error|warning)\s+(TS\d+):\s+(.+)$")

        for line in output.split("\n"):
            match = tsc_pattern.match(line.strip())
            if match:
                file_path, line_num, col, sev_str, code, message = match.groups()
                severity = Severity.ERROR if sev_str == "error" else Severity.WARNING
                issues.append(
                    Issue(
                        file=file_path,
                        line=int(line_num),
                        column=int(col),
                        code=code,
                        message=message,
                        severity=severity,
                        source="tsc",
                    )
                )

        return CheckResult(issues=issues, checks_run=["tsc"])

    # -- Stub Detection -----------------------------------------------------

    def _run_stub_check(self, paths: list[str]) -> CheckResult:
        """Check for TODOs, stubs, and placeholder code in TS/JS files."""
        issues = []

        for path_str in paths:
            path = Path(path_str)
            if path.is_file() and path.suffix in ALL_EXTENSIONS:
                issues.extend(self._check_file_for_stubs(path))
            elif path.is_dir():
                for ext in ALL_EXTENSIONS:
                    for ts_file in path.rglob(f"*{ext}"):
                        if self._should_exclude(ts_file):
                            continue
                        issues.extend(self._check_file_for_stubs(ts_file))

        return CheckResult(issues=issues, checks_run=["stub-check"])

    def _check_file_for_stubs(self, file_path: Path) -> list[Issue]:
        """Check a single file for stub patterns."""
        issues = []

        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")
        except Exception:
            return issues

        for line_num, line in enumerate(lines, 1):
            for pattern, description in self.config.stub_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    if self._is_legitimate_pattern(file_path, line_num, line, lines):
                        continue

                    issues.append(
                        Issue(
                            file=str(file_path),
                            line=line_num,
                            column=1,
                            code="STUB",
                            message=f"{description}: {line.strip()[:60]}",
                            severity=Severity.WARNING,
                            source="stub-check",
                            suggestion="Remove placeholder or implement functionality",
                        )
                    )

        return issues

    def _is_legitimate_pattern(self, file_path: Path, line_num: int, line: str, lines: list[str]) -> bool:
        """Check if a stub pattern is actually legitimate (TypeScript/JS-specific)."""
        file_str = str(file_path).lower()

        # Test files are allowed to have stubs and TODOs
        if any(marker in file_str for marker in [".test.", ".spec.", "__tests__", "__mocks__"]):
            return True

        # @ts-expect-error WITH an explanation is legitimate
        # Pattern only matches bare @ts-expect-error (no text after it)
        if "@ts-expect-error" in line and not line.strip().endswith("@ts-expect-error"):
            return True

        # @ts-ignore in type declaration files (.d.ts) is sometimes necessary
        if "@ts-ignore" in line and file_path.suffix == ".ts" and file_path.stem.endswith(".d"):
            return True

        # Abstract method stubs in TypeScript are legitimate
        stripped = line.strip()
        if stripped == "throw new Error('not implemented');" or stripped == 'throw new Error("not implemented");':
            for i in range(max(0, line_num - 3), line_num):
                if "abstract" in lines[i]:
                    return True

        return False


# Convenience functions for direct use
def check_files(paths: list[str | Path], config: CheckConfig | None = None, fix: bool = False) -> CheckResult:
    """Check TypeScript/JavaScript files for issues.

    Args:
        paths: Files or directories to check
        config: Optional config (defaults loaded from package.json)
        fix: If True, auto-fix issues where possible

    Returns:
        CheckResult with issues found
    """
    checker = TypeScriptChecker(config)
    return checker.check_files(paths, fix=fix)


def check_content(content: str, filename: str = "stdin.ts", config: CheckConfig | None = None) -> CheckResult:
    """Check TypeScript/JavaScript content string.

    Args:
        content: Source code as string
        filename: Virtual filename for error reporting
        config: Optional config

    Returns:
        CheckResult with issues found
    """
    checker = TypeScriptChecker(config)
    return checker.check_content(content, filename)
