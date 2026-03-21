"""Mine GitHub PR comments and discussions for implicit knowledge."""
import re
import os
import json
import urllib.request
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class PRDecision:
    pr_number: int
    pr_title: str
    file: str
    decision_type: str  # 'chose', 'rejected', 'warning', 'reason', 'dont'
    text: str
    author: str
    url: str = ""


# Patterns that indicate an architectural/design decision in a PR comment
DECISION_PATTERNS = [
    # "we chose X because Y"
    (re.compile(r'\b(chose?|decided|going with|picked|selected|using)\b.{5,80}\b(because|since|due to|as|for)\b', re.I), 'chose'),
    # "don't do X" / "avoid X"
    (re.compile(r"\b(don't|do not|avoid|never|shouldn't|should not)\s+\w+.{5,60}", re.I), 'dont'),
    # "this will break if..." / "careful with..."
    (re.compile(r'\b(will break|can break|might break|careful|watch out|be careful|note:|warning:|important:)\b.{5,80}', re.I), 'warning'),
    # "the reason is..." / "this is because..."
    (re.compile(r'\b(the reason|this is because|this happened because|root cause|we need this because)\b.{5,100}', re.I), 'reason'),
    # "intentionally X" — explains why something looks weird
    (re.compile(r'\b(intentionally|on purpose|by design|this is intentional)\b.{5,80}', re.I), 'reason'),
]


def get_github_token() -> str:
    """Get GitHub token from environment or git config."""
    token = os.environ.get('GITHUB_TOKEN', '') or os.environ.get('GH_TOKEN', '')
    if not token:
        # Try git credential
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'config', '--get', 'github.token'],
                capture_output=True, text=True
            )
            token = result.stdout.strip()
        except Exception:
            pass
    return token


def get_repo_info(repo_root: str) -> tuple[str, str]:
    """Extract owner/repo from git remote URL."""
    try:
        import subprocess
        result = subprocess.run(
            ['git', 'remote', 'get-url', 'origin'],
            capture_output=True, text=True, cwd=repo_root
        )
        url = result.stdout.strip()
        # Parse: https://github.com/owner/repo.git or git@github.com:owner/repo.git
        match = re.search(r'github\.com[:/]([^/]+)/([^/.]+)', url)
        if match:
            return match.group(1), match.group(2)
    except Exception:
        pass
    return '', ''


def github_api(path: str, token: str) -> dict:
    """Make GitHub API request."""
    url = f"https://api.github.com{path}"
    req = urllib.request.Request(
        url,
        headers={
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'cortex-ai/0.1',
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except Exception:
        return {}


def get_pr_files(owner: str, repo: str, pr_number: int, token: str) -> list[str]:
    """Get list of files changed in a PR."""
    data = github_api(f'/repos/{owner}/{repo}/pulls/{pr_number}/files', token)
    if isinstance(data, list):
        return [f.get('filename', '') for f in data]
    return []


def extract_decisions_from_text(text: str, pr_number: int, pr_title: str,
                                  file: str, author: str, pr_url: str) -> list[PRDecision]:
    """Extract decision patterns from a comment text."""
    decisions = []
    # Split into sentences
    sentences = re.split(r'[.!?]\s+', text)
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 20 or len(sentence) > 300:
            continue
        # Skip code blocks
        if sentence.startswith('`') or sentence.startswith('    '):
            continue
        for pattern, decision_type in DECISION_PATTERNS:
            if pattern.search(sentence):
                decisions.append(PRDecision(
                    pr_number=pr_number,
                    pr_title=pr_title,
                    file=file,
                    decision_type=decision_type,
                    text=sentence[:200],
                    author=author,
                    url=pr_url,
                ))
                break  # one decision type per sentence
    return decisions


def mine_pr_knowledge(repo_root: str, token: str = '', max_prs: int = 50) -> dict[str, list[PRDecision]]:
    """
    Mine PRs for implicit knowledge. Returns {filepath: [PRDecision]}.

    Args:
        repo_root: path to git repo
        token: GitHub API token (optional, uses env var if not set)
        max_prs: max number of recent PRs to analyze
    """
    if not token:
        token = get_github_token()

    if not token:
        return {}  # No token, skip silently

    owner, repo = get_repo_info(repo_root)
    if not owner or not repo:
        return {}

    # Get recent merged PRs
    prs_data = github_api(f'/repos/{owner}/{repo}/pulls?state=closed&per_page={max_prs}&sort=updated', token)
    if not isinstance(prs_data, list):
        return {}

    # Filter to merged only
    merged_prs = [pr for pr in prs_data if pr.get('merged_at')]

    file_decisions: dict[str, list[PRDecision]] = {}

    for pr in merged_prs[:max_prs]:
        pr_number = pr.get('number', 0)
        pr_title = pr.get('title', '')
        pr_url = pr.get('html_url', '')

        # Get files changed in this PR
        pr_files = get_pr_files(owner, repo, pr_number, token)
        if not pr_files:
            continue

        # Get PR review comments (inline comments on code)
        comments_data = github_api(f'/repos/{owner}/{repo}/pulls/{pr_number}/comments', token)
        if isinstance(comments_data, list):
            for comment in comments_data:
                text = comment.get('body', '')
                file = comment.get('path', '')
                author = comment.get('user', {}).get('login', '')
                if text and file:
                    decisions = extract_decisions_from_text(text, pr_number, pr_title, file, author, pr_url)
                    if decisions:
                        file_decisions.setdefault(file, []).extend(decisions)

        # Get PR issue comments (general discussion)
        issue_comments = github_api(f'/repos/{owner}/{repo}/issues/{pr_number}/comments', token)
        if isinstance(issue_comments, list):
            for comment in issue_comments:
                text = comment.get('body', '')
                author = comment.get('user', {}).get('login', '')
                if text:
                    # Associate with all files in this PR
                    for file in pr_files[:5]:  # limit to 5 files per PR
                        decisions = extract_decisions_from_text(text, pr_number, pr_title, file, author, pr_url)
                        if decisions:
                            file_decisions.setdefault(file, []).extend(decisions[:2])  # max 2 per file per comment

    return file_decisions


def save_pr_knowledge(repo_root: str, file_decisions: dict[str, list[PRDecision]]) -> None:
    """Save mined PR knowledge to .claude/pr-knowledge.json"""
    output = {}
    for filepath, decisions in file_decisions.items():
        output[filepath] = [
            {
                'pr': d.pr_number,
                'title': d.pr_title,
                'type': d.decision_type,
                'text': d.text,
                'author': d.author,
                'url': d.url,
            }
            for d in decisions[:10]  # max 10 per file
        ]

    out_path = Path(repo_root) / '.claude' / 'pr-knowledge.json'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))


def load_pr_knowledge(repo_root: str) -> dict[str, list[dict]]:
    """Load saved PR knowledge."""
    path = Path(repo_root) / '.claude' / 'pr-knowledge.json'
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            pass
    return {}
