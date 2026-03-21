"""Generate human-readable file summaries using Claude Haiku via Anthropic API."""
import os
import json
import urllib.request
from pathlib import Path


def generate_summary(
    filepath: str,
    repo_root: str,
    constructs: list,
    imports: list,
    insights: list,
    security_issues: list,
) -> str:
    """
    Generate a human-readable summary for a file using Claude Haiku.
    Returns empty string if API key not set or call fails.
    """
    api_key = os.environ.get('ANTHROPIC_API_KEY', '')
    if not api_key:
        return ""

    rel_path = os.path.relpath(filepath, repo_root)

    # Build a compact prompt
    construct_names = [f"{c.kind} {c.name}" for c in constructs[:10]]
    import_names = imports[:8]
    bug_fixes = [i.message for i in insights if i.type == 'bug_fix'][:3]

    prompt = f"""Analyze this code file and write a 2-3 sentence technical summary for a coding agent.

File: {rel_path}
Constructs: {', '.join(construct_names) if construct_names else 'none'}
Imports: {', '.join(import_names) if import_names else 'none'}
Recent bug fixes: {'; '.join(bug_fixes) if bug_fixes else 'none'}
Security issues: {len(security_issues)} found

Write a concise technical overview: what this file does, its main responsibility, and any notable risk areas. Be specific, not generic."""

    try:
        payload = json.dumps({
            "model": "claude-haiku-4-5",
            "max_tokens": 150,
            "messages": [{"role": "user", "content": prompt}]
        }).encode()

        req = urllib.request.Request(
            'https://api.anthropic.com/v1/messages',
            data=payload,
            headers={
                'x-api-key': api_key,
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json',
            }
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            return data['content'][0]['text'].strip()
    except Exception:
        return ""
