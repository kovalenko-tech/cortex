"""Python security analysis using bandit."""
import json
import subprocess
import shutil
from dataclasses import dataclass


@dataclass
class SecurityIssue:
    severity: str  # HIGH | MEDIUM | LOW
    line: int
    message: str
    rule: str


def run_bandit(filepath: str) -> list[SecurityIssue]:
    """Run bandit on a Python file. Returns [] if bandit not installed."""
    if not shutil.which('bandit') and not _bandit_available():
        return []

    try:
        result = subprocess.run(
            ['python3', '-m', 'bandit', '-f', 'json', '-q', filepath],
            capture_output=True, text=True, timeout=30
        )
        data = json.loads(result.stdout or '{}')
        issues = []
        for r in data.get('results', []):
            issues.append(SecurityIssue(
                severity=r.get('issue_severity', 'LOW').upper(),
                line=r.get('line_number', 0),
                message=r.get('issue_text', ''),
                rule=r.get('test_id', ''),
            ))
        return issues
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return []


def _bandit_available() -> bool:
    try:
        import bandit  # noqa
        return True
    except ImportError:
        return False
