"""Scan git history for accidentally committed secrets."""
import re
import git
from dataclasses import dataclass


SECRET_PATTERNS = [
    (re.compile(r'ghp_[A-Za-z0-9]{36}'), "GitHub token"),
    (re.compile(r'sk-[A-Za-z0-9]{48}'), "OpenAI API key"),
    (re.compile(r'AKIA[0-9A-Z]{16}'), "AWS Access Key"),
    (re.compile(r'[Pp]assword\s*=\s*["\'][^"\']{8,}["\']'), "Hardcoded password"),
    (re.compile(r'[Ss]ecret\s*=\s*["\'][^"\']{8,}["\']'), "Hardcoded secret"),
    (re.compile(r'api[_-]?key\s*=\s*["\'][A-Za-z0-9_\-]{16,}["\']', re.I), "API key"),
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
            for pattern, name in SECRET_PATTERNS:
                if pattern.search(line):
                    findings.append(SecretFinding(
                        pattern_name=name,
                        commit_hash=current_commit,
                        message=current_msg,
                    ))
                    break

    return findings
