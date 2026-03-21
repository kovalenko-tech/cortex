"""CLI entry point."""
import click
from pathlib import Path
from rich.console import Console

console = Console()


@click.group()
@click.version_option()
def cli():
    """Cortex — generates .claude/docs/ context for Claude Code."""
    pass


@cli.command()
@click.option("--repo", default=".", show_default=True, help="Path to repository")
@click.option("--since", default=None, help="Analyze commits since (e.g. HEAD~50)")
@click.option("--lang", multiple=True, help="Filter languages: python, js, ts, dart, go")
@click.option("--no-cache", is_flag=True, help="Force full re-analysis ignoring cache")
@click.option("--no-llm", is_flag=True, help="Skip LLM summaries (faster, no API key needed)")
@click.option("--max-files", default=0, type=int, help="Limit number of files analyzed (0 = no limit)")
def analyze(repo, since, lang, no_cache, no_llm, max_files):
    """Analyze repository and generate .claude/docs/ context."""
    from .core import Cortex
    Cortex().analyze(
        repo_path=repo, since=since, languages=list(lang) or None,
        no_cache=no_cache, no_llm=no_llm, max_files=max_files,
    )


@cli.command()
@click.argument("file_path")
def context(file_path):
    """Print context for a specific file."""
    import pathlib
    doc = pathlib.Path(f".claude/docs/{file_path}.md")
    if doc.exists():
        console.print(doc.read_text())
    else:
        console.print(f"[yellow]No context for {file_path}. Run: cortex analyze[/]")


@cli.command()
@click.option("--repo", default=".", show_default=True)
def security(repo):
    """Run security audit only."""
    import os
    from .core import discover_files
    from .security.bandit_runner import run_bandit
    from .security.semgrep_runner import run_semgrep

    repo_root = os.path.abspath(repo)
    files = discover_files(repo_root, ['python'])
    issues_total = 0
    for f in files:
        issues = run_bandit(f) + run_semgrep(f)
        if issues:
            rel = os.path.relpath(f, repo_root)
            for issue in issues:
                console.print(f"[red]{rel}:{issue.line}[/] [{issue.severity}] {issue.message}")
                issues_total += 1
    if issues_total == 0:
        console.print("[green]✅ No security issues found.[/]")


@cli.command()
@click.option("--repo", default=".", show_default=True)
def install_hook(repo):
    """Install git pre-commit hook to auto-update .claude/docs/ on each commit."""
    import stat
    hook_path = Path(repo) / ".git" / "hooks" / "pre-commit"
    hook_content = """#!/bin/bash
# Cortex: update context for staged files
STAGED=$(git diff --cached --name-only --diff-filter=ACM)
if [ -n "$STAGED" ]; then
    cortex analyze --since HEAD 2>/dev/null || true
    git add .claude/docs/ 2>/dev/null || true
fi
"""
    hook_path.write_text(hook_content)
    hook_path.chmod(hook_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    console.print(f"[green]✓[/] Pre-commit hook installed at {hook_path}")
    console.print("[dim]Now .claude/docs/ will auto-update on every commit.[/]")


@cli.command()
@click.option("--repo", default=".", show_default=True)
@click.option("--interval", default=30, show_default=True, help="Poll interval in seconds")
def watch(repo, interval):
    """Watch for file changes and auto-update context."""
    import time
    console.print(f"[blue]Watching[/] {repo} every {interval}s... (Ctrl+C to stop)")
    last_hash = ""
    while True:
        try:
            import git
            r = git.Repo(repo, search_parent_directories=True)
            current_hash = r.head.commit.hexsha
            if current_hash != last_hash:
                if last_hash:
                    console.print(f"[dim]New commit detected, updating...[/]")
                    from .core import Cortex
                    Cortex().analyze(repo_path=repo, since=f"{last_hash[:8]}..HEAD")
                last_hash = current_hash
            time.sleep(interval)
        except KeyboardInterrupt:
            console.print("\n[yellow]Watch stopped.[/]")
            break
        except Exception:
            time.sleep(interval)


@cli.command()
@click.option("--repo", default=".", show_default=True, help="Path to repository")
@click.option("--force", is_flag=True, help="Overwrite existing CLAUDE.md")
def init(repo, force):
    """Generate CLAUDE.md for your project."""
    import os
    from pathlib import Path
    from .generators.claude_md_gen import write_claude_md

    repo_root = os.path.abspath(repo)
    claude_md = Path(repo_root) / 'CLAUDE.md'

    if claude_md.exists() and not force:
        console.print(f"[yellow]CLAUDE.md already exists.[/] Use --force to overwrite.")
        return

    path = write_claude_md(repo_root)
    console.print(f"[green]✓[/] Generated [cyan]CLAUDE.md[/]")
    console.print(f"[dim]Review and customize it, then commit to your repo.[/]")


@cli.command()
def mcp():
    """Start Cortex MCP server (for Claude Code integration)."""
    from .mcp_server import run_mcp_server
    run_mcp_server()


@cli.command()
@click.option("--repo", default=".", show_default=True)
def status(repo):
    """Show analysis status for the current project."""
    import os
    import json
    from pathlib import Path

    repo_root = os.path.abspath(repo)
    docs_dir = Path(repo_root) / '.claude' / 'docs'
    cache_path = Path(repo_root) / '.cortex-cache.json'

    console.print(f"\n[bold]Cortex Status[/] — {repo_root}\n")

    if not docs_dir.exists():
        console.print("[yellow]Not analyzed yet.[/] Run: cortex analyze")
        return

    # Count docs
    doc_files = list(docs_dir.rglob('*.md'))
    console.print(f"  Context files: [bold]{len(doc_files)}[/]")

    # Cache info
    if cache_path.exists():
        cache = json.loads(cache_path.read_text())
        last_run = cache.get('_last_run', '')
        if last_run:
            console.print(f"  Last analysis: [bold]{last_run}[/]")
        console.print(f"  Cached files:  [bold]{len([k for k in cache if not k.startswith('_')])}[/]")
    else:
        console.print(f"  Cache: [yellow]none[/]")

    # Security summary
    security_path = docs_dir / 'SECURITY_REPORT.md'
    if security_path.exists():
        content = security_path.read_text()
        if 'No security issues' in content:
            console.print(f"  Security:      [green]✅ clean[/]")
        else:
            console.print(f"  Security:      [red]⚠️  issues found[/] — run: cortex security")

    console.print()


@cli.command()
@click.option("--repo", default=".", show_default=True)
@click.confirmation_option(prompt="Delete .claude/docs/ and cache?")
def clean(repo):
    """Remove all generated context files."""
    import os
    import shutil
    from pathlib import Path

    repo_root = os.path.abspath(repo)
    docs_dir = Path(repo_root) / '.claude' / 'docs'
    cache_path = Path(repo_root) / '.cortex-cache.json'

    removed = 0
    if docs_dir.exists():
        shutil.rmtree(docs_dir)
        removed += 1
        console.print(f"[green]✓[/] Removed .claude/docs/")
    if cache_path.exists():
        cache_path.unlink()
        removed += 1
        console.print(f"[green]✓[/] Removed .cortex-cache.json")

    if removed == 0:
        console.print("[dim]Nothing to clean.[/]")
    else:
        console.print("[dim]Run cortex analyze to regenerate.[/]")


@cli.command()
@click.option("--repo", default=".", show_default=True)
def deps(repo):
    """Scan dependencies for vulnerabilities."""
    import os
    from .security.deps_scanner import scan_all_deps, write_deps_report
    repo_root = os.path.abspath(repo)
    console.print("[dim]Scanning dependencies...[/]")
    issues = scan_all_deps(repo_root)
    path = write_deps_report(repo_root, issues)
    if issues:
        for issue in issues[:10]:
            icon = '🔴' if issue.severity == 'HIGH' else '⚠️'
            console.print(f"  {icon} [bold]{issue.package}[/] {issue.version}: {issue.description}")
        console.print(f"\n[dim]Full report: {path}[/]")
    else:
        console.print("[green]✅ No issues found.[/]")


@cli.command()
@click.argument("branch", default="main")
@click.option("--repo", default=".", show_default=True)
def diff(branch, repo):
    """Update context only for files changed vs a branch."""
    import os
    from .core import Cortex
    repo_root = os.path.abspath(repo)
    console.print(f"[dim]Analyzing changes vs {branch}...[/]")
    Cortex().analyze(repo_path=repo_root, since=f"{branch}...HEAD")


if __name__ == "__main__":
    cli()
