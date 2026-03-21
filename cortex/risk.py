"""Risk and complexity scoring for files."""
import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RiskScore:
    file: str
    level: str          # HIGH | MEDIUM | LOW
    score: int          # 0-100
    icon: str           # 🔴 | 🟡 | 🟢
    reasons: list[str] = field(default_factory=list)
    dependents_count: int = 0   # how many files import this file
    bug_fix_count: int = 0
    change_count: int = 0
    has_tests: bool = False
    security_issues: int = 0


def compute_risk_score(
    file: str,
    bug_fix_count: int,
    change_count: int,
    has_tests: bool,
    security_issues: int,
    dependents_count: int,
    cochange_count: int,
) -> RiskScore:
    """Compute risk score 0-100 based on multiple factors."""
    score = 0
    reasons = []

    # Bug history (0-30 points)
    if bug_fix_count >= 10:
        score += 30
        reasons.append(f"{bug_fix_count} bug fixes in history")
    elif bug_fix_count >= 5:
        score += 20
        reasons.append(f"{bug_fix_count} bug fixes in history")
    elif bug_fix_count >= 2:
        score += 10
        reasons.append(f"{bug_fix_count} bug fixes in history")

    # No tests (0-25 points)
    if not has_tests:
        score += 25
        reasons.append("no test coverage")

    # Security issues (0-25 points)
    if security_issues >= 3:
        score += 25
        reasons.append(f"{security_issues} security issues")
    elif security_issues >= 1:
        score += 15
        reasons.append(f"{security_issues} security issue(s)")

    # High churn — changed frequently (0-10 points)
    if change_count >= 50:
        score += 10
        reasons.append(f"high churn ({change_count} changes)")
    elif change_count >= 20:
        score += 5
        reasons.append(f"moderate churn ({change_count} changes)")

    # Many dependents — breaking this breaks others (0-10 points)
    if dependents_count >= 10:
        score += 10
        reasons.append(f"{dependents_count} files depend on this")
    elif dependents_count >= 5:
        score += 5
        reasons.append(f"{dependents_count} files depend on this")

    # Determine level
    if score >= 50:
        level, icon = 'HIGH', '🔴'
    elif score >= 25:
        level, icon = 'MEDIUM', '🟡'
    else:
        level, icon = 'LOW', '🟢'

    return RiskScore(
        file=file,
        level=level,
        score=score,
        icon=icon,
        reasons=reasons,
        dependents_count=dependents_count,
        bug_fix_count=bug_fix_count,
        change_count=change_count,
        has_tests=has_tests,
        security_issues=security_issues,
    )


def get_change_count(repo_root: str, filepath: str) -> int:
    """Count total number of commits that touched this file."""
    try:
        import git
        repo = git.Repo(repo_root, search_parent_directories=True)
        log = repo.git.log('--oneline', '--follow', '--', filepath)
        return len([line for line in log.strip().splitlines() if line.strip()])
    except Exception:
        return 0


def build_dependents_map(repo_root: str, files: list[str]) -> dict[str, int]:
    """Build a map of {file: number_of_other_files_that_import_it}."""
    # Map from module name to file path
    module_to_file = {}
    for f in files:
        rel = os.path.relpath(f, repo_root) if os.path.isabs(f) else f
        stem = Path(rel).stem
        # Use relative path without extension as module key
        module_key = rel.replace('/', '.').replace('\\', '.').rsplit('.', 1)[0]
        module_to_file[stem] = rel
        module_to_file[module_key] = rel

    dependents_count = {f: 0 for f in files}

    # Simple approach: search for imports of each module name
    for source_file in files:
        try:
            content = Path(source_file).read_text(encoding='utf-8', errors='ignore')
            for stem, target_file in module_to_file.items():
                source_rel = os.path.relpath(source_file, repo_root) if os.path.isabs(source_file) else source_file
                if target_file != source_rel:
                    # Check if this file imports the target
                    patterns = [
                        f'import {stem}',
                        f'from {stem}',
                        f'require("{stem}")',
                        f"require('{stem}')",
                        f'import "{stem}"',
                        f"import '{stem}'",
                    ]
                    if any(p in content for p in patterns):
                        # Find the actual file
                        for f in files:
                            rel = os.path.relpath(f, repo_root) if os.path.isabs(f) else f
                            if Path(rel).stem == stem or rel == target_file:
                                dependents_count[f] = dependents_count.get(f, 0) + 1
                                break
        except Exception:
            pass

    return dependents_count
