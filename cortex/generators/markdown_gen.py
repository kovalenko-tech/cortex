"""Generate .claude/docs/<filepath>.md context files."""
import os
from datetime import datetime, timezone
from pathlib import Path
from ..miners.git_history import HistoricalInsight
from ..analyzers.base import FileAnalysis
from ..security.bandit_runner import SecurityIssue
from ..security.secrets_scanner import SecretFinding
from .llm_summary import generate_summary


def generate(
    filepath: str,
    repo_root: str,
    insights: list,
    related_files: list,
    analysis,
    security_issues: list,
    secret_findings: list,
    no_llm: bool = False,
    analyzed_at: str = "",
    risk_level: str = "",
    risk_score: int = 0,
    risk_reasons: list = None,
    pr_decisions: list = None,
) -> str:
    rel_path = os.path.relpath(filepath, repo_root)
    now_str = analyzed_at or datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    lines = [f"# {rel_path}", "", f"> ⚡ **Fresh** — analyzed {now_str}", ""]

    # Risk badge
    if risk_level:
        icon = '🔴' if risk_level == 'HIGH' else '🟡' if risk_level == 'MEDIUM' else '🟢'
        reasons_str = ' · '.join(risk_reasons or [])
        lines.append(f"> {icon} **{risk_level} RISK** (score: {risk_score}/100) — {reasons_str}")
        lines.append("")

    # Overview
    lines.append("## Overview")
    lang = analysis.language if analysis else "unknown"
    constructs_count = len(analysis.constructs) if analysis else 0
    lines.append(f"Language: {lang} | Constructs: {constructs_count}")
    if analysis and analysis.imports:
        lines.append(f"Key imports: {', '.join(analysis.imports[:5])}")

    # LLM-enhanced summary (requires ANTHROPIC_API_KEY)
    llm_summary = None if no_llm else generate_summary(
        filepath, repo_root,
        analysis.constructs if analysis else [],
        analysis.imports if analysis else [],
        insights,
        security_issues,
    )
    if llm_summary:
        lines.append("")
        lines.append(llm_summary)
    lines.append("")

    # Historical Insights
    if insights:
        lines.append("## Historical Insights")
        for ins in insights[:5]:
            label = "Bug Fix" if ins.type == "bug_fix" else "Refactor"
            lines.append(f"- [{label}] {ins.date}: {ins.message}")
            if ins.diff_summary:
                lines.append(f"  Change: {ins.diff_summary}")
        lines.append("")

    # PR Decisions
    if pr_decisions:
        lines.append("## Decisions & Context")
        lines.append("*Extracted from PR discussions:*")
        lines.append("")
        for d in pr_decisions[:5]:
            icon = {'chose': '✅', 'rejected': '❌', 'warning': '⚠️', 'reason': '💡', 'dont': '🚫'}.get(d.get('type', ''), '📝')
            pr_ref = f"[PR #{d['pr']}]({d['url']})" if d.get('url') else f"PR #{d['pr']}"
            lines.append(f"- {icon} {d['text']}")
            lines.append(f"  *{pr_ref} — @{d['author']}*")
        lines.append("")

    # Edit Checklist
    checklist = []
    if analysis and analysis.checklist:
        checklist.extend(analysis.checklist)
    if analysis and analysis.test_files:
        for tf in analysis.test_files[:2]:
            item = f"Review: {tf}"
            if item not in checklist:
                checklist.append(item)

    if checklist:
        lines.append("## Edit Checklist")
        for item in checklist:
            lines.append(f"- {item}")
        lines.append("")

    # Key Constructs
    if analysis and analysis.constructs:
        lines.append("## Key Constructs")
        for c in analysis.constructs[:8]:
            doc = f" — {c.docstring}" if c.docstring else ""
            lines.append(f"- **{c.name}** ({c.kind}, line {c.line}){doc}")
        lines.append("")

    # Related Files
    if related_files:
        lines.append("## Related Files")
        for related, score in related_files:
            lines.append(f"- `{related}` [co-change: {int(score*100)}%]")
        lines.append("")

    # Security Notes
    all_security = list(security_issues) + list(secret_findings)
    lines.append("## Security Notes")
    if not all_security:
        lines.append("- ✅ No issues found")
    else:
        for issue in security_issues[:5]:
            icon = "🔴" if issue.severity == "HIGH" else "⚠️"
            lines.append(f"- {icon} [{issue.severity}] Line {issue.line}: {issue.message} ({issue.rule})")
        for finding in secret_findings[:3]:
            lines.append(f"- 🔴 [HIGH] Potential secret in commit {finding.commit_hash}: {finding.pattern_name}")
    lines.append("")

    return "\n".join(lines)


def write_doc(content: str, filepath: str, repo_root: str) -> str:
    rel_path = os.path.relpath(filepath, repo_root)
    out_path = Path(repo_root) / ".claude" / "docs" / (rel_path + ".md")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding='utf-8')
    return str(out_path)
