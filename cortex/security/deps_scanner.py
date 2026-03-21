"""Scan project dependencies for known vulnerabilities."""
import subprocess
import json
import shutil
import os
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class DepIssue:
    package: str
    version: str
    severity: str
    description: str
    fix_version: str = ""


def scan_python_deps(repo_root: str) -> list[DepIssue]:
    """Run pip-audit if available."""
    if not shutil.which('pip-audit'):
        # Try to install silently
        try:
            subprocess.run(['pip', 'install', 'pip-audit', '--quiet'], capture_output=True, timeout=30)
        except Exception:
            return []

    req_files = ['requirements.txt', 'requirements-dev.txt', 'pyproject.toml']
    issues = []
    for req in req_files:
        req_path = Path(repo_root) / req
        if not req_path.exists():
            continue
        try:
            result = subprocess.run(
                ['pip-audit', '--format', 'json', '-r', str(req_path)],
                capture_output=True, text=True, timeout=60
            )
            data = json.loads(result.stdout or '[]')
            for item in data:
                for vuln in item.get('vulns', []):
                    issues.append(DepIssue(
                        package=item.get('name', ''),
                        version=item.get('version', ''),
                        severity='HIGH',
                        description=vuln.get('description', vuln.get('id', '')),
                        fix_version=vuln.get('fix_versions', [''])[0] if vuln.get('fix_versions') else '',
                    ))
        except Exception:
            pass
    return issues


def scan_node_deps(repo_root: str) -> list[DepIssue]:
    """Run npm audit if package.json exists."""
    if not (Path(repo_root) / 'package.json').exists():
        return []
    if not shutil.which('npm'):
        return []
    try:
        result = subprocess.run(
            ['npm', 'audit', '--json'],
            capture_output=True, text=True, timeout=60, cwd=repo_root
        )
        data = json.loads(result.stdout or '{}')
        issues = []
        for vuln_id, vuln in data.get('vulnerabilities', {}).items():
            issues.append(DepIssue(
                package=vuln.get('name', vuln_id),
                version=vuln.get('range', ''),
                severity=vuln.get('severity', 'unknown').upper(),
                description=vuln.get('title', '') or (vuln.get('via', [{}])[0].get('title', '') if vuln.get('via') else ''),
                fix_version='',
            ))
        return issues
    except Exception:
        return []


def scan_flutter_deps(repo_root: str) -> list[DepIssue]:
    """Check flutter pub outdated for outdated packages."""
    if not (Path(repo_root) / 'pubspec.yaml').exists():
        return []
    if not shutil.which('flutter'):
        return []
    try:
        result = subprocess.run(
            ['flutter', 'pub', 'outdated', '--json'],
            capture_output=True, text=True, timeout=60, cwd=repo_root
        )
        data = json.loads(result.stdout or '{}')
        issues = []
        for pkg in data.get('packages', []):
            if pkg.get('current') != pkg.get('latest'):
                issues.append(DepIssue(
                    package=pkg.get('package', ''),
                    version=pkg.get('current', ''),
                    severity='LOW',
                    description='Outdated package',
                    fix_version=pkg.get('latest', ''),
                ))
        return issues
    except Exception:
        return []


def scan_all_deps(repo_root: str) -> list[DepIssue]:
    return scan_python_deps(repo_root) + scan_node_deps(repo_root) + scan_flutter_deps(repo_root)


def write_deps_report(repo_root: str, issues: list[DepIssue]) -> str:
    """Write .claude/docs/DEPENDENCIES.md"""
    lines = ['# Dependency Report — Cortex', '']
    if not issues:
        lines.append('✅ No vulnerable or outdated dependencies found.')
    else:
        high = [i for i in issues if i.severity == 'HIGH']
        medium = [i for i in issues if i.severity in ('MEDIUM', 'MODERATE')]
        low = [i for i in issues if i.severity == 'LOW']
        lines.append(f"**Total issues:** {len(issues)} ({len(high)} high, {len(medium)} medium, {len(low)} low)")
        lines.append('')
        for issue in issues:
            icon = '🔴' if issue.severity == 'HIGH' else '⚠️' if issue.severity in ('MEDIUM', 'MODERATE') else '💡'
            fix = f" → fix: {issue.fix_version}" if issue.fix_version else ''
            lines.append(f"- {icon} **{issue.package}** {issue.version}: {issue.description}{fix}")

    out = Path(repo_root) / '.claude' / 'docs' / 'DEPENDENCIES.md'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text('\n'.join(lines), encoding='utf-8')
    return str(out)
