"""Configuration loading for TypeScript/JavaScript checks.

Loads config from package.json "amplifier-typescript-dev" key,
with environment variable and explicit override support.
"""

import json
import os
from pathlib import Path

from .models import CheckConfig


def find_package_json(start_path: Path | None = None) -> Path | None:
    """Find package.json by walking up from start_path."""
    current = start_path or Path.cwd()

    while current != current.parent:
        candidate = current / "package.json"
        if candidate.exists():
            return candidate
        current = current.parent

    return None


def load_config(
    config_path: Path | None = None,
    overrides: dict | None = None,
) -> CheckConfig:
    """Load configuration from package.json with optional overrides.

    Config is loaded from (in order of priority):
    1. Explicit overrides dict
    2. Environment variables (AMPLIFIER_TYPESCRIPT_*)
    3. package.json "amplifier-typescript-dev" key
    4. Default values

    Args:
        config_path: Explicit path to package.json (auto-discovered if None)
        overrides: Dict of config values to override

    Returns:
        Merged CheckConfig
    """
    config_data: dict = {}

    # Load from package.json
    pkg_path = config_path or find_package_json()
    if pkg_path and pkg_path.exists():
        try:
            with open(pkg_path, encoding="utf-8") as f:
                package = json.load(f)
                config_data = package.get("amplifier-typescript-dev", {})
        except (json.JSONDecodeError, OSError):
            pass  # Graceful fallback to defaults

    # Apply environment variables
    env_mapping = {
        "AMPLIFIER_TYPESCRIPT_ENABLE_PRETTIER": "enable_prettier",
        "AMPLIFIER_TYPESCRIPT_ENABLE_ESLINT": "enable_eslint",
        "AMPLIFIER_TYPESCRIPT_ENABLE_TSC": "enable_tsc",
        "AMPLIFIER_TYPESCRIPT_ENABLE_STUB_CHECK": "enable_stub_check",
        "AMPLIFIER_TYPESCRIPT_FAIL_ON_WARNING": "fail_on_warning",
        "AMPLIFIER_TYPESCRIPT_AUTO_FIX": "auto_fix",
    }

    for env_var, config_key in env_mapping.items():
        value = os.environ.get(env_var)
        if value is not None:
            if value.lower() in ("true", "1", "yes"):
                config_data[config_key] = True
            elif value.lower() in ("false", "0", "no"):
                config_data[config_key] = False

    # Apply explicit overrides
    if overrides:
        config_data.update(overrides)

    return CheckConfig.from_dict(config_data)
