"""Amplifier TypeScript/JavaScript Development Bundle.

Provides comprehensive TypeScript and JavaScript development tools including:
- Code formatting checks (prettier)
- Linting (eslint)
- Type checking (tsc)
- Stub/placeholder detection
- Integration with Amplifier as tool and hook modules
"""

from .checker import TypeScriptChecker, check_content, check_files
from .models import ALL_EXTENSIONS, CheckConfig, CheckResult, Issue, Severity

__version__ = "0.1.0"

__all__ = [
    "TypeScriptChecker",
    "check_files",
    "check_content",
    "CheckResult",
    "Issue",
    "Severity",
    "CheckConfig",
    "ALL_EXTENSIONS",
]
