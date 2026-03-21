"""Freshness scoring — how stale is the context for each file."""
import os
import json
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class FreshnessInfo:
    file: str
    analyzed_at: Optional[str]      # ISO timestamp when last analyzed
    commits_since: int               # commits to this file since last analysis
    days_since: float                # days since last analysis
    score: str                       # FRESH | STALE | OUTDATED | UNKNOWN
    icon: str                        # ⚡ | ⚠️ | ❌ | ❓


def get_commits_since(repo_root: str, filepath: str, since_timestamp: str) -> int:
    """Count commits to a file since a given ISO timestamp."""
    try:
        import git
        repo = git.Repo(repo_root, search_parent_directories=True)
        since_dt = datetime.fromisoformat(since_timestamp.replace('Z', '+00:00'))
        # git log since date
        log = repo.git.log(
            '--oneline',
            f'--after={since_dt.strftime("%Y-%m-%d %H:%M:%S")}',
            '--follow',
            '--',
            filepath
        )
        return len([l for l in log.strip().splitlines() if l.strip()])
    except Exception:
        return 0


def compute_freshness(analyzed_at: Optional[str], commits_since: int, days_since: float) -> tuple:
    """Return (score, icon) based on age and commits since analysis."""
    if analyzed_at is None:
        return 'UNKNOWN', '❓'

    # Fresh: analyzed < 1 day ago AND 0 commits since
    if days_since < 1 and commits_since == 0:
        return 'FRESH', '⚡'

    # Fresh: analyzed < 3 days ago AND <= 2 commits since
    if days_since < 3 and commits_since <= 2:
        return 'FRESH', '⚡'

    # Stale: 3-14 days OR 3-10 commits since
    if days_since < 14 and commits_since < 10:
        return 'STALE', '⚠️'

    # Outdated: 14+ days OR 10+ commits since
    return 'OUTDATED', '❌'


def get_file_freshness(repo_root: str, filepath: str, cache: dict) -> FreshnessInfo:
    """Get freshness info for a single file."""
    rel = os.path.relpath(filepath, repo_root) if os.path.isabs(filepath) else filepath

    file_cache = cache.get(rel, {})
    # file_cache may be a string (hash) or dict; handle both
    if isinstance(file_cache, dict):
        analyzed_at = file_cache.get('analyzed_at') or cache.get('_last_run')
    else:
        analyzed_at = cache.get('_last_run')

    if not analyzed_at:
        return FreshnessInfo(
            file=rel, analyzed_at=None, commits_since=0,
            days_since=999, score='UNKNOWN', icon='❓'
        )

    # Parse timestamp
    try:
        # Handle "2024-03-21 18:00" format from _last_run (16 chars, no T)
        if 'T' not in analyzed_at and len(analyzed_at) == 16:
            analyzed_at_iso = analyzed_at + ':00'
            analyzed_dt = datetime.strptime(analyzed_at_iso, '%Y-%m-%d %H:%M:%S')
        elif 'T' not in analyzed_at and len(analyzed_at) >= 19:
            analyzed_dt = datetime.strptime(analyzed_at[:19], '%Y-%m-%d %H:%M:%S')
        else:
            analyzed_dt = datetime.fromisoformat(analyzed_at.replace('Z', ''))
        analyzed_dt = analyzed_dt.replace(tzinfo=timezone.utc)
    except Exception:
        return FreshnessInfo(
            file=rel, analyzed_at=analyzed_at, commits_since=0,
            days_since=0, score='FRESH', icon='⚡'
        )

    now = datetime.now(timezone.utc)
    days_since = (now - analyzed_dt).total_seconds() / 86400
    commits_since = get_commits_since(repo_root, rel, analyzed_at)
    score, icon = compute_freshness(analyzed_at, commits_since, days_since)

    return FreshnessInfo(
        file=rel,
        analyzed_at=analyzed_at,
        commits_since=commits_since,
        days_since=days_since,
        score=score,
        icon=icon,
    )


def load_cortex_cache(repo_root: str) -> dict:
    cache_path = Path(repo_root) / '.cortex-cache.json'
    if cache_path.exists():
        try:
            return json.loads(cache_path.read_text())
        except Exception:
            pass
    return {}
