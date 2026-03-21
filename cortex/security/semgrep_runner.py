"""Universal SAST using semgrep (optional)."""
import json
import subprocess
import shutil
from dataclasses import dataclass


@dataclass
class SemgrepIssue:
    severity: str
    line: int
    message: str
    rule: str


def run_semgrep(filepath: str) -> list[SemgrepIssue]:
    """Run semgrep if available. Returns [] otherwise."""
    if not shutil.which('semgrep'):
        return []

    try:
        result = subprocess.run(
            ['semgrep', '--config', 'auto', '--json', '--quiet', filepath],
            capture_output=True, text=True, timeout=60
        )
        data = json.loads(result.stdout or '{}')
        issues = []
        for r in data.get('results', []):
            issues.append(SemgrepIssue(
                severity=r.get('extra', {}).get('severity', 'WARNING').upper(),
                line=r.get('start', {}).get('line', 0),
                message=r.get('extra', {}).get('message', ''),
                rule=r.get('check_id', ''),
            ))
        return issues
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return []
