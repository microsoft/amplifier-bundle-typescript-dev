"""Data models for TypeScript/JavaScript checking results."""

from dataclasses import dataclass, field
from enum import Enum


class Severity(Enum):
    """Issue severity levels."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class Issue:
    """A single issue found during checking."""

    file: str
    line: int
    column: int
    code: str  # E.g., "TS2322", "no-unused-vars", "STUB"
    message: str
    severity: Severity
    source: str  # "prettier", "eslint", "tsc", "stub-check"
    suggestion: str | None = None
    end_line: int | None = None
    end_column: int | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "file": self.file,
            "line": self.line,
            "column": self.column,
            "code": self.code,
            "message": self.message,
            "severity": self.severity.value,
            "source": self.source,
            "suggestion": self.suggestion,
        }

    def format_location(self) -> str:
        """Format as file:line:column."""
        return f"{self.file}:{self.line}:{self.column}"

    def format_short(self) -> str:
        """Format as a short one-liner."""
        return f"{self.format_location()}: [{self.code}] {self.message}"


# TypeScript + JavaScript file extensions
TS_EXTENSIONS = {".ts", ".tsx", ".mts", ".cts"}
JS_EXTENSIONS = {".js", ".jsx", ".mjs", ".cjs"}
ALL_EXTENSIONS = TS_EXTENSIONS | JS_EXTENSIONS


@dataclass
class CheckConfig:
    """Configuration for TypeScript/JavaScript checks."""

    # What to run
    enable_prettier: bool = True
    enable_eslint: bool = True
    enable_tsc: bool = True
    enable_stub_check: bool = True

    # Filtering
    exclude_patterns: list[str] = field(
        default_factory=lambda: [
            "node_modules/**",
            "dist/**",
            "build/**",
            "coverage/**",
            ".next/**",
            ".git/**",
        ]
    )

    # Behavior
    fail_on_warning: bool = False
    auto_fix: bool = False

    # Stub check patterns: (regex, description)
    stub_patterns: list[tuple[str, str]] = field(
        default_factory=lambda: [
            (r"\bTODO\b", "TODO comment"),
            (r"\bFIXME\b", "FIXME comment"),
            (r"\bHACK\b", "HACK comment"),
            (
                r'throw\s+new\s+Error\(\s*["\']not\s+implemented',
                "Not implemented error",
            ),
            (r"//\s*@ts-ignore\s*$", "@ts-ignore without explanation"),
            (r"//\s*@ts-expect-error\s*$", "@ts-expect-error without explanation"),
        ]
    )

    # Hook-specific
    hook_enabled: bool = True
    hook_file_patterns: list[str] = field(
        default_factory=lambda: [
            "*.ts",
            "*.tsx",
            "*.mts",
            "*.cts",
            "*.js",
            "*.jsx",
            "*.mjs",
            "*.cjs",
        ]
    )
    hook_report_level: str = "warning"  # error | warning | info
    hook_auto_inject: bool = True

    @classmethod
    def from_dict(cls, data: dict) -> "CheckConfig":
        """Create config from dictionary."""
        return cls(
            enable_prettier=data.get("enable_prettier", True),
            enable_eslint=data.get("enable_eslint", True),
            enable_tsc=data.get("enable_tsc", True),
            enable_stub_check=data.get("enable_stub_check", True),
            exclude_patterns=data.get("exclude_patterns", cls().exclude_patterns),
            fail_on_warning=data.get("fail_on_warning", False),
            auto_fix=data.get("auto_fix", False),
            hook_enabled=data.get("hook", {}).get("enabled", True),
            hook_file_patterns=data.get("hook", {}).get(
                "file_patterns", cls().hook_file_patterns
            ),
            hook_report_level=data.get("hook", {}).get("report_level", "warning"),
            hook_auto_inject=data.get("hook", {}).get("auto_inject", True),
        )


@dataclass
class CheckResult:
    """Result of running TypeScript/JavaScript checks."""

    issues: list[Issue] = field(default_factory=list)
    files_checked: int = 0
    checks_run: list[str] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        """Count of error-severity issues."""
        return sum(1 for i in self.issues if i.severity == Severity.ERROR)

    @property
    def warning_count(self) -> int:
        """Count of warning-severity issues."""
        return sum(1 for i in self.issues if i.severity == Severity.WARNING)

    @property
    def info_count(self) -> int:
        """Count of info-severity issues."""
        return sum(1 for i in self.issues if i.severity == Severity.INFO)

    @property
    def exit_code(self) -> int:
        """Exit code: 0=clean, 1=warnings only, 2=errors."""
        if self.error_count > 0:
            return 2
        if self.warning_count > 0:
            return 1
        return 0

    @property
    def success(self) -> bool:
        """True if no errors (warnings are acceptable)."""
        return self.error_count == 0

    @property
    def clean(self) -> bool:
        """True if no issues at all."""
        return len(self.issues) == 0

    @property
    def summary(self) -> str:
        """Human-readable summary."""
        if self.clean:
            return f"All checks passed ({self.files_checked} files)"

        parts = []
        if self.error_count:
            parts.append(
                f"{self.error_count} error{'s' if self.error_count != 1 else ''}"
            )
        if self.warning_count:
            parts.append(
                f"{self.warning_count} warning{'s' if self.warning_count != 1 else ''}"
            )
        if self.info_count:
            parts.append(f"{self.info_count} info")

        return f"Found {', '.join(parts)} in {self.files_checked} files"

    def to_tool_output(self) -> dict:
        """Format for Amplifier tool response."""
        return {
            "success": self.success,
            "clean": self.clean,
            "summary": self.summary,
            "files_checked": self.files_checked,
            "checks_run": self.checks_run,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "issues": [i.to_dict() for i in self.issues],
        }

    def to_hook_output(self) -> dict:
        """Format for hook context injection."""
        if self.clean:
            return {}

        issue_lines = []
        for issue in self.issues[:10]:
            issue_lines.append(f"- {issue.format_short()}")

        if len(self.issues) > 10:
            issue_lines.append(f"  ... and {len(self.issues) - 10} more issues")

        return {
            "summary": self.summary,
            "issues_text": "\n".join(issue_lines),
            "error_count": self.error_count,
            "warning_count": self.warning_count,
        }

    def merge(self, other: "CheckResult") -> "CheckResult":
        """Merge another result into this one."""
        return CheckResult(
            issues=self.issues + other.issues,
            files_checked=max(self.files_checked, other.files_checked),
            checks_run=list(set(self.checks_run + other.checks_run)),
        )
