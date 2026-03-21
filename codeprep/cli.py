"""CLI entry point."""
import click
from rich.console import Console

console = Console()


@click.group()
@click.version_option()
def cli():
    """CodePrep — generates .claude/docs/ context for Claude Code."""
    pass


@cli.command()
@click.option("--repo", default=".", show_default=True, help="Path to repository")
@click.option("--since", default=None, help="Analyze commits since (e.g. HEAD~50)")
@click.option("--lang", multiple=True, help="Filter languages: python, js, ts, dart, go")
def analyze(repo, since, lang):
    """Analyze repository and generate .claude/docs/ context."""
    from .core import CodePrep
    CodePrep().analyze(repo_path=repo, since=since, languages=list(lang) or None)


@cli.command()
@click.argument("file_path")
def context(file_path):
    """Print context for a specific file."""
    import pathlib
    doc = pathlib.Path(f".claude/docs/{file_path}.md")
    if doc.exists():
        console.print(doc.read_text())
    else:
        console.print(f"[yellow]No context for {file_path}. Run: codeprep analyze[/]")


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


if __name__ == "__main__":
    cli()
