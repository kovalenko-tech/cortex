"""CLI entry point."""
import os
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
@click.option("--level", type=click.Choice(['HIGH', 'MEDIUM', 'LOW', 'all']), default='all')
def risks(repo, level):
    """Show risk scores for all analyzed files."""
    import os
    import json
    from pathlib import Path
    from .risk import compute_risk_score, get_change_count

    repo_root = os.path.abspath(repo)
    cache_path = Path(repo_root) / '.cortex-cache.json'

    if not cache_path.exists():
        console.print("[yellow]No cache found.[/] Run: cortex analyze first.")
        return

    cache = json.loads(cache_path.read_text())
    files = [k for k in cache.keys() if not k.startswith('_')]

    if not files:
        console.print("[yellow]No files in cache.[/]")
        return

    console.print(f"\n[bold]Risk Analysis[/] — {repo_root}\n")

    results = []
    for rel_path in files:
        abs_path = os.path.join(repo_root, rel_path)
        if not os.path.exists(abs_path):
            continue

        # Get data from cache (supports both old hash-string format and new dict format)
        file_cache = cache.get(rel_path, {})
        if isinstance(file_cache, dict):
            bug_fix_count = file_cache.get('bug_fix_count', 0)
            change_count = file_cache.get('change_count', 0) or get_change_count(repo_root, rel_path)
            has_tests = file_cache.get('has_tests', False)
            security_count = file_cache.get('security_count', 0)
        else:
            bug_fix_count = 0
            change_count = get_change_count(repo_root, rel_path)
            has_tests = False
            security_count = 0

        risk = compute_risk_score(
            file=rel_path,
            bug_fix_count=bug_fix_count,
            change_count=change_count,
            has_tests=has_tests,
            security_issues=security_count,
            dependents_count=0,
            cochange_count=0,
        )
        results.append(risk)

    # Filter
    if level != 'all':
        results = [r for r in results if r.level == level]

    # Sort by score desc
    results.sort(key=lambda x: x.score, reverse=True)

    # Summary counts (always from full results for display)
    all_results = results if level == 'all' else results
    high = sum(1 for r in results if r.level == 'HIGH')
    medium = sum(1 for r in results if r.level == 'MEDIUM')
    low = sum(1 for r in results if r.level == 'LOW')
    console.print(f"  🔴 High risk:   [red]{high}[/]")
    console.print(f"  🟡 Medium risk: [yellow]{medium}[/]")
    console.print(f"  🟢 Low risk:    [green]{low}[/]")
    console.print()

    # Show high/medium risk files
    show = [r for r in results if r.level in ('HIGH', 'MEDIUM')][:20]
    if show:
        console.print("[bold]Files requiring attention:[/]")
        for r in show:
            reasons = ' · '.join(r.reasons[:2])
            console.print(f"  {r.icon} [cyan]{r.file}[/] [dim](score: {r.score}) {reasons}[/]")
        console.print()
    else:
        console.print("[green]No high-risk files found.[/]")
    console.print()


@cli.command()
@click.option("--repo", default=".", show_default=True)
@click.option("--stale-only", is_flag=True, help="Show only stale/outdated files")
def freshness(repo, stale_only):
    """Show how fresh the context is for each file."""
    import os
    from pathlib import Path
    from .freshness import load_cortex_cache, get_file_freshness

    repo_root = os.path.abspath(repo)
    docs_dir = Path(repo_root) / '.claude' / 'docs'

    if not docs_dir.exists():
        console.print("[yellow]No context found.[/] Run: cortex analyze")
        return

    cache = load_cortex_cache(repo_root)
    if not cache:
        console.print("[yellow]No cache found.[/] Run: cortex analyze to generate fresh context.")
        return

    # Get all analyzed files from cache
    files = [k for k in cache.keys() if not k.startswith('_')]

    if not files:
        console.print("[yellow]No files in cache.[/]")
        return

    fresh_count = stale_count = outdated_count = unknown_count = 0
    results = []

    for rel_path in sorted(files):
        info = get_file_freshness(repo_root, rel_path, cache)
        results.append(info)
        if info.score == 'FRESH':
            fresh_count += 1
        elif info.score == 'STALE':
            stale_count += 1
        elif info.score == 'OUTDATED':
            outdated_count += 1
        else:
            unknown_count += 1

    # Summary
    console.print()
    console.print(f"[bold]Context Freshness[/] — {repo_root}")
    console.print()
    console.print(f"  ⚡ Fresh:    [green]{fresh_count}[/]")
    console.print(f"  ⚠️  Stale:    [yellow]{stale_count}[/]")
    console.print(f"  ❌ Outdated: [red]{outdated_count}[/]")
    console.print()

    # Show stale/outdated files
    problem_files = [r for r in results if r.score in ('STALE', 'OUTDATED')]
    if problem_files:
        console.print("[bold]Files needing refresh:[/]")
        for info in sorted(problem_files, key=lambda x: x.days_since, reverse=True)[:20]:
            days = f"{info.days_since:.0f}d ago"
            commits = f"+{info.commits_since} commits" if info.commits_since else ""
            console.print(f"  {info.icon} [cyan]{info.file}[/] [dim]{days} {commits}[/]")
        console.print()
        max_commits = max(p.commits_since for p in problem_files)
        if max_commits > 0:
            console.print(f"  Run [cyan]cortex analyze --since HEAD~{max_commits}[/] to refresh")
        else:
            console.print(f"  Run [cyan]cortex analyze[/] to refresh")
    else:
        console.print("[green]All context is fresh! ✓[/]")
    console.print()


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


def _add_to_shell_rc(key: str, value: str, console) -> None:
    """Add an export line to .zshrc or .bashrc."""
    from pathlib import Path

    # Detect shell config file
    shell = os.environ.get('SHELL', '')
    if 'zsh' in shell:
        rc_file = Path.home() / '.zshrc'
    else:
        rc_file = Path.home() / '.bashrc'

    export_line = f'\nexport {key}="{value}"\n'

    # Check if already set
    if rc_file.exists() and key in rc_file.read_text():
        console.print(f"[yellow]⚠[/]  {key} already exists in {rc_file.name}, skipping")
        return

    with open(rc_file, 'a') as f:
        f.write(export_line)

    # Also set in current process
    os.environ[key] = value

    console.print(f"[green]✓[/] Added {key} to {rc_file}")
    console.print(f"[dim]  Run: source ~/{rc_file.name} to activate in current shell[/]")


@cli.command()
@click.option("--repo", default=".", show_default=True)
def setup(repo):
    """Interactive setup wizard — analyze project and configure Claude Code integration."""
    from pathlib import Path

    repo_root = os.path.abspath(repo)
    console.print()
    console.print("[bold]Cortex Setup[/]")
    console.print("[dim]Let's set up Cortex for your project.[/]")
    console.print()

    # Step 0: Environment setup
    console.print("[bold]Step 0:[/] Environment variables")
    console.print()

    anthropic_set = bool(os.environ.get('ANTHROPIC_API_KEY'))
    github_set = bool(os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN'))

    if anthropic_set and github_set:
        console.print("[green]✓[/] ANTHROPIC_API_KEY is set")
        console.print("[green]✓[/] GITHUB_TOKEN is set")
    else:
        if not anthropic_set:
            console.print("[yellow]○[/]  ANTHROPIC_API_KEY not set")
            console.print("  [dim]Used for AI-generated file summaries (optional)[/]")
            console.print("  Get one at: [cyan]https://console.anthropic.com/[/]")
            console.print()
            key = click.prompt("  Enter API key (or press Enter to skip)", default="", show_default=False)
            if key.strip():
                _add_to_shell_rc('ANTHROPIC_API_KEY', key.strip(), console)
            console.print()

        if not github_set:
            console.print("[yellow]○[/]  GITHUB_TOKEN not set")
            console.print("  [dim]Used for mining PR decisions (optional)[/]")
            console.print("  Get one at: [cyan]https://github.com/settings/tokens[/]")
            console.print()
            token = click.prompt("  Enter GitHub token (or press Enter to skip)", default="", show_default=False)
            if token.strip():
                _add_to_shell_rc('GITHUB_TOKEN', token.strip(), console)
            console.print()

    console.print()

    # Step 1: Check if already analyzed
    docs_dir = Path(repo_root) / '.claude' / 'docs'
    if docs_dir.exists() and list(docs_dir.rglob('*.md')):
        count = len(list(docs_dir.rglob('*.md')))
        console.print(f"[green]✓[/] Already analyzed ({count} context files found)")
    else:
        console.print("[bold]Step 1:[/] Analyze your project")
        console.print("[dim]This scans git history, code structure and security.[/]")
        console.print()
        if click.confirm("  Run cortex analyze now?", default=True):
            from .core import Cortex
            Cortex().analyze(repo_path=repo_root)
        else:
            console.print("[dim]  Skipped. Run cortex analyze manually later.[/]")

    console.print()

    # Step 2: CLAUDE.md
    claude_md = Path(repo_root) / 'CLAUDE.md'
    console.print("[bold]Step 2:[/] Generate CLAUDE.md")
    if claude_md.exists():
        console.print(f"[green]✓[/] CLAUDE.md already exists")
    else:
        console.print("[dim]CLAUDE.md tells Claude Code about your project structure and conventions.[/]")
        if click.confirm("  Generate CLAUDE.md?", default=True):
            from .generators.claude_md_gen import write_claude_md
            write_claude_md(repo_root)
            console.print(f"[green]✓[/] Generated CLAUDE.md")

    console.print()

    # Step 3: MCP or manual
    console.print("[bold]Step 3:[/] Claude Code integration")
    console.print()
    console.print("  How do you want to use Cortex with Claude Code?")
    console.print()
    console.print("  [1] MCP server [dim](automatic — context injected on every file open)[/]")
    console.print("  [2] Manual     [dim](run python .claude/get_context.py <file> yourself)[/]")
    console.print("  [3] Skip")
    console.print()

    choice = click.prompt("  Choice", type=click.Choice(['1', '2', '3']), default='1')

    if choice == '1':
        settings_path = Path(repo_root) / '.claude' / 'settings.json'
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        import json
        existing = {}
        if settings_path.exists():
            try:
                existing = json.loads(settings_path.read_text())
            except Exception:
                pass
        existing.setdefault('mcpServers', {})['cortex'] = {"command": "cortex", "args": ["mcp"]}
        settings_path.write_text(json.dumps(existing, indent=2))
        console.print(f"[green]✓[/] MCP server configured in .claude/settings.json")
        console.print("[dim]  Restart Claude Code to activate.[/]")

    elif choice == '2':
        # Add to CLAUDE.md if exists
        if claude_md.exists():
            content = claude_md.read_text()
            if 'get_context.py' not in content:
                content += '\n\n## Cortex Context\n\nBefore editing any file, run:\n```bash\npython .claude/get_context.py <file_path>\n```\n'
                claude_md.write_text(content)
                console.print(f"[green]✓[/] Added context instructions to CLAUDE.md")
        else:
            console.print("[dim]  Run cortex init first to create CLAUDE.md[/]")

    console.print()

    # Step 4: Auto-update hook
    console.print("[bold]Step 4:[/] Keep context fresh")
    console.print("[dim]Install a git hook to auto-update context on every commit.[/]")

    hook_path = Path(repo_root) / '.git' / 'hooks' / 'pre-commit'
    if hook_path.exists() and 'cortex' in hook_path.read_text():
        console.print(f"[green]✓[/] Pre-commit hook already installed")
    elif click.confirm("  Install pre-commit hook?", default=True):
        import stat
        hook_content = '#!/bin/bash\n# Cortex: update context for staged files\ncortex analyze --since HEAD --no-cache 2>/dev/null || true\ngit add .claude/docs/ 2>/dev/null || true\n'
        hook_path.write_text(hook_content)
        hook_path.chmod(hook_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
        console.print(f"[green]✓[/] Pre-commit hook installed")

    console.print()

    # Step 5: Commit
    console.print("[bold]Step 5:[/] Commit to your repo")
    console.print()
    console.print("  [cyan]git add .claude/ CLAUDE.md[/]")
    console.print("  [cyan]git commit -m 'add cortex context'[/]")
    console.print()
    console.print("[bold green]✓ Setup complete![/]")
    console.print("[dim]Claude Code now has full context for your project.[/]")
    console.print()


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

    # Freshness summary
    from .freshness import load_cortex_cache, get_file_freshness
    cache_data = load_cortex_cache(repo_root)
    cache_files = [k for k in cache_data.keys() if not k.startswith('_')]
    if cache_files:
        fresh = stale = outdated = 0
        for f in cache_files:
            info = get_file_freshness(repo_root, f, cache_data)
            if info.score == 'FRESH':
                fresh += 1
            elif info.score == 'STALE':
                stale += 1
            elif info.score == 'OUTDATED':
                outdated += 1
        console.print(f"  Freshness:     ⚡{fresh} fresh  ⚠️{stale} stale  ❌{outdated} outdated")

    # Risk summary from cache
    high_risk = sum(
        1 for k, v in cache_data.items()
        if not k.startswith('_') and isinstance(v, dict) and v.get('risk_level') == 'HIGH'
    )
    if high_risk > 0:
        console.print(f"  High-risk files: [red]{high_risk}[/] — run [cyan]cortex risks[/]")

    # Environment check
    console.print()
    console.print("  [bold dim]Environment:[/]")
    anthropic = "✅ set" if os.environ.get('ANTHROPIC_API_KEY') else "[yellow]not set[/] (AI summaries disabled)"
    github = "✅ set" if (os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')) else "[yellow]not set[/] (PR mining disabled)"
    console.print(f"  ANTHROPIC_API_KEY: {anthropic}")
    console.print(f"  GITHUB_TOKEN:      {github}")

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


@cli.command('mine-prs')
@click.option("--repo", default=".", show_default=True)
@click.option("--token", default="", help="GitHub token (or set GITHUB_TOKEN env var)")
@click.option("--max-prs", default=50, show_default=True, help="Max PRs to analyze")
def mine_prs(repo, token, max_prs):
    """Mine GitHub PRs for implicit decisions and architectural knowledge."""
    import os
    from .miners.github_prs import mine_pr_knowledge, save_pr_knowledge

    repo_root = os.path.abspath(repo)

    console.print(f"\n[dim]Mining PR knowledge from GitHub...[/]")

    decisions = mine_pr_knowledge(repo_root, token=token, max_prs=max_prs)

    if not decisions:
        console.print("[yellow]No PR decisions found.[/]")
        console.print("[dim]Make sure GITHUB_TOKEN is set and this repo has merged PRs with comments.[/]")
        return

    save_pr_knowledge(repo_root, decisions)

    total = sum(len(v) for v in decisions.values())
    console.print(f"[green]✓[/] Found [bold]{total}[/] decisions across [bold]{len(decisions)}[/] files")
    console.print()

    # Show sample
    for filepath, file_decisions in list(decisions.items())[:5]:
        console.print(f"  [cyan]{filepath}[/]")
        for d in file_decisions[:2]:
            icon = {'chose': '✅', 'warning': '⚠️', 'reason': '💡', 'dont': '🚫'}.get(d.decision_type, '📝')
            console.print(f"    {icon} {d.text[:80]}...")
        console.print()

    console.print(f"[dim]Saved to .claude/pr-knowledge.json[/]")
    console.print(f"[dim]Run cortex analyze to include in .claude/docs/ context files[/]")
    console.print()


if __name__ == "__main__":
    cli()
