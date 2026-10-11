"""Runtime Anki version checker.

Detects the running Anki version, compares it with the distribution's
target version, and reports incompatibilities for individual addons.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AddonStatus:
    name: str
    deploy_dir: str
    compatible: bool
    reason: str = ""


@dataclass
class CompatibilityReport:
    anki_version: str
    target_version: str
    is_compatible: bool
    addon_issues: list[AddonStatus] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class VersionChecker:
    """Checks Anki version compatibility for the addon distribution."""

    def __init__(self, config_dir: Path | None = None):
        if config_dir is None:
            config_dir = self._find_config_dir()
        self._config_dir = config_dir
        self._compat_config = self._load_json("anki_compatibility.json")
        self._registry = self._load_json("addon_registry.json")

    @staticmethod
    def _find_config_dir() -> Path:
        candidates = [
            Path(__file__).resolve().parents[2] / "config",
            Path(__file__).resolve().parents[3] / "config",
        ]
        for candidate in candidates:
            if (candidate / "anki_compatibility.json").exists():
                return candidate
        return candidates[0]

    def _load_json(self, filename: str) -> dict:
        filepath = self._config_dir / filename
        if not filepath.exists():
            return {}
        with open(filepath, encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def get_anki_version() -> str:
        """Return the currently running Anki version string."""
        try:
            import anki
            return anki.version
        except (ImportError, AttributeError):
            return "unknown"

    @staticmethod
    def parse_version(version_str: str) -> tuple[int, ...]:
        """Parse version string into comparable tuple.

        Handles both old (2.1.XX) and new (YY.MM.X) schemes.
        """
        try:
            parts = version_str.replace("-", ".").split(".")
            return tuple(int(p) for p in parts if p.isdigit())
        except (ValueError, AttributeError):
            return (0,)

    def check(self) -> CompatibilityReport:
        """Run full compatibility check against current Anki."""
        anki_version = self.get_anki_version()
        target = self._compat_config.get("target_anki_version", "unknown")
        min_version = self._compat_config.get("min_anki_version", "0")

        anki_parsed = self.parse_version(anki_version)
        min_parsed = self.parse_version(min_version)

        is_compatible = anki_parsed >= min_parsed or anki_version == "unknown"

        report = CompatibilityReport(
            anki_version=anki_version,
            target_version=target,
            is_compatible=is_compatible,
        )

        if not is_compatible:
            report.warnings.append(
                f"Anki {anki_version} is below minimum {min_version}"
            )

        overrides = self._compat_config.get("addon_overrides", {})
        for deploy_dir, override in overrides.items():
            if not override.get("enabled", True):
                report.addon_issues.append(
                    AddonStatus(
                        name=deploy_dir,
                        deploy_dir=deploy_dir,
                        compatible=False,
                        reason=override.get("reason", "Disabled by override"),
                    )
                )

        return report

    def format_report(self, report: CompatibilityReport | None = None) -> str:
        """Return a human-readable compatibility summary."""
        if report is None:
            report = self.check()

        lines = [
            f"Anki version: {report.anki_version}",
            f"Target version: {report.target_version}",
            f"Compatible: {'yes' if report.is_compatible else 'NO'}",
        ]

        if report.warnings:
            lines.append("")
            lines.append("Warnings:")
            for w in report.warnings:
                lines.append(f"  - {w}")

        if report.addon_issues:
            lines.append("")
            lines.append("Disabled addons:")
            for issue in report.addon_issues:
                lines.append(f"  - {issue.deploy_dir}: {issue.reason}")

        return "\n".join(lines)


def check_compatibility(config_dir: Path | None = None) -> CompatibilityReport:
    """Convenience function: run a compatibility check and return the report."""
    checker = VersionChecker(config_dir=config_dir)
    return checker.check()
