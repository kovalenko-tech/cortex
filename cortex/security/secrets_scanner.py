"""Scan git history for accidentally committed secrets."""
import re
import git
from dataclasses import dataclass


SECRET_PATTERNS = [
    # Real tokens with specific prefixes
    (re.compile(r'ghp_[A-Za-z0-9]{36}'), "GitHub token"),
    (re.compile(r'ghs_[A-Za-z0-9]{36}'), "GitHub Actions token"),
    (re.compile(r'sk-[A-Za-z0-9]{48}'), "OpenAI API key"),
    (re.compile(r'sk-ant-[A-Za-z0-9\-_]{90,}'), "Anthropic API key"),
    (re.compile(r'AKIA[0-9A-Z]{16}'), "AWS Access Key"),
    (re.compile(r'nvapi-[A-Za-z0-9\-_]{50,}'), "NVIDIA API key"),
    # Hardcoded passwords — require quotes and minimum length, skip test/example patterns
    (re.compile(r'(?<![_a-zA-Z])password\s*=\s*["\'][^"\']{12,}["\'](?!\s*#\s*example)', re.I), "Hardcoded password"),
    (re.compile(r'(?<![_a-zA-Z])secret_key\s*=\s*["\'][^"\']{12,}["\']', re.I), "Hardcoded secret key"),
    # Database URLs with credentials
    (re.compile(r'(?:postgres|mysql|mongodb)://[^:]+:[^@]{8,}@'), "Database URL with credentials"),
]

# Skip lines that are clearly tests/examples/comments
SKIP_PATTERNS = [
    re.compile(r'#.*example', re.I),
    re.compile(r'#.*test', re.I),
    re.compile(r'#.*placeholder', re.I),
    re.compile(r'test_password|example_password|fake_password|mock_password', re.I),
    re.compile(r'your[-_](?:api[-_])?key|<your[-_]key>', re.I),
]


@dataclass
class SecretFinding:
    pattern_name: str
    commit_hash: str
    message: str


def scan_git_history(repo_path: str, filepath: str, max_commits: int = 50) -> list[SecretFinding]:
    try:
        repo = git.Repo(repo_path, search_parent_directories=True)
    except git.InvalidGitRepositoryError:
        return []

    findings = []
    try:
        log = repo.git.log('--follow', f'--max-count={max_commits}',
                           '--format=%H|%s', '-p', '--', filepath)
    except git.GitCommandError:
        return []

    current_commit = ""
    current_msg = ""
    for line in log.splitlines():
        if '|' in line and len(line) < 200 and not line.startswith('+') and not line.startswith('-'):
            parts = line.split('|', 1)
            if len(parts[0]) == 40:
                current_commit = parts[0][:8]
                current_msg = parts[1]
        elif line.startswith('+') and not line.startswith('+++'):
            # Skip lines matching skip patterns
            if any(skip.search(line) for skip in SKIP_PATTERNS):
                continue
            for pattern, name in SECRET_PATTERNS:
                if pattern.search(line):
                    findings.append(SecretFinding(
                        pattern_name=name,
                        commit_hash=current_commit,
                        message=current_msg,
                    ))
                    break

    return findings
