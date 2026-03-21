"""Generate SUMMARY.md and SECURITY_REPORT.md."""
from pathlib import Path


def build_mermaid_diagram(file_results: list[dict], repo_root: str) -> str:
    """Build a Mermaid module dependency diagram from import data."""
    # Group files by top-level directory
    modules: dict[str, list[str]] = {}
    for r in file_results:
        f = r.get('file', '')
        parts = f.split('/')
        if len(parts) > 1:
            module = parts[0]
            modules.setdefault(module, []).append(f)

    if len(modules) < 2:
        return ""

    lines = ['```mermaid', 'graph TD']
    # Add nodes for each module
    for mod in list(modules.keys())[:10]:  # limit to 10 modules
        safe = mod.replace('-', '_').replace('.', '_')
        count = len(modules[mod])
        lines.append(f'    {safe}["{mod}/\\n{count} files"]')
    lines.append('```')
    return '\n'.join(lines)


def write_summary(repo_root: str, file_results: list[dict]) -> None:
    lines = ["# Project Summary — Cortex Analysis", ""]
    lines.append(f"**Files analyzed:** {len(file_results)}")

    by_lang: dict[str, int] = {}
    total_constructs = 0
    total_security = 0

    for r in file_results:
        lang = r.get('language', 'unknown')
        by_lang[lang] = by_lang.get(lang, 0) + 1
        total_constructs += r.get('constructs', 0)
        total_security += r.get('security_count', 0)

    lines.append(f"**Total constructs:** {total_constructs}")
    lines.append(f"**Security issues:** {total_security}")
    lines.append("")
    lines.append("## Languages")
    for lang, count in sorted(by_lang.items()):
        lines.append(f"- {lang}: {count} files")
    lines.append("")

    # Mermaid architecture diagram
    diagram = build_mermaid_diagram(file_results, repo_root)
    if diagram:
        lines.append("## Architecture")
        lines.append(diagram)
        lines.append("")

    # Files with no test coverage
    uncovered = [r for r in file_results if not r.get('has_tests', False)]
    if uncovered:
        lines.append("## Files Without Tests")
        lines.append(f"**{len(uncovered)} files** have no associated test files:")
        lines.append("")
        for r in uncovered[:15]:
            lines.append(f"- `{r['file']}`")
        lines.append("")

    out = Path(repo_root) / ".claude" / "docs" / "SUMMARY.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding='utf-8')


def write_security_report(repo_root: str, security_items: list[dict]) -> None:
    lines = ["# Security Report — Cortex", ""]

    if not security_items:
        lines.append("✅ No security issues found.")
    else:
        lines.append(f"**Total issues:** {len(security_items)}")
        lines.append("")
        for item in security_items:
            lines.append(f"### {item['file']}")
            lines.append(f"- [{item['severity']}] Line {item.get('line', '?')}: {item['message']}")
            lines.append("")

    out = Path(repo_root) / ".claude" / "docs" / "SECURITY_REPORT.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding='utf-8')
