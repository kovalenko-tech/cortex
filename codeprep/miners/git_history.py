"""Git history mining — extract bug fixes, refactors, and historical insights per file."""
import re
from dataclasses import dataclass, field
from typing import Optional
import git


@dataclass
class HistoricalInsight:
    commit_hash: str
    type: str  # bug_fix | refactor | feature
    date: str
    message: str
    diff_summary: str = ""


BUG_KEYWORDS = re.compile(r'\b(fix|bug|hotfix|patch|resolve|crash|error|issue|broken)\b', re.I)
REFACTOR_KEYWORDS = re.compile(r'\b(refactor|cleanup|clean up|improve|simplify|rename|move|reorganize)\b', re.I)


def classify_commit(message: str) -> str:
    if BUG_KEYWORDS.search(message):
        return "bug_fix"
    if REFACTOR_KEYWORDS.search(message):
        return "refactor"
    return "feature"


def get_insights(repo_path: str, filepath: str, max_commits: int = 30) -> list[HistoricalInsight]:
    """Return historical insights for a file from git log."""
    try:
        repo = git.Repo(repo_path, search_parent_directories=True)
    except git.InvalidGitRepositoryError:
        return []

    insights = []
    try:
        log = repo.git.log(
            '--follow', f'--max-count={max_commits}',
            '--diff-filter=M', '--format=%H|%s|%ad', '--date=short',
            '--', filepath
        )
    except git.GitCommandError:
        return []

    for line in log.strip().splitlines():
        if not line.strip():
            continue
        parts = line.split('|', 2)
        if len(parts) < 3:
            continue
        commit_hash, message, date = parts

        commit_type = classify_commit(message)
        if commit_type == "feature":
            continue  # only keep bug fixes and refactors

        # Get a brief diff summary
        diff_summary = ""
        try:
            diff = repo.git.show('--stat', '--format=', commit_hash, '--', filepath)
            lines = [l for l in diff.strip().splitlines() if filepath.split('/')[-1] in l]
            diff_summary = lines[0].strip() if lines else ""
        except Exception:
            pass

        insights.append(HistoricalInsight(
            commit_hash=commit_hash[:8],
            type=commit_type,
            date=date,
            message=message,
            diff_summary=diff_summary,
        ))

    return insights
