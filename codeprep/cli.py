"""CLI entry point."""
import click

@click.group()
def cli():
    """CodePrep — generates .claude/docs/ context for Claude Code."""
    pass

@cli.command()
@click.option("--repo", default=".", help="Path to repository")
@click.option("--since", default=None, help="Analyze commits since (e.g. HEAD~50)")
def analyze(repo, since):
    """Analyze repository and generate .claude/docs/ context."""
    click.echo(f"Analyzing {repo}...")
    # TODO: implement

@cli.command()
@click.argument("file_path")
def context(file_path):
    """Print context for a specific file."""
    import pathlib
    doc = pathlib.Path(f".claude/docs/{file_path}.md")
    if doc.exists():
        click.echo(doc.read_text())
    else:
        click.echo(f"No context for {file_path}. Run: codeprep analyze")

@cli.command()
def security():
    """Run security audit only."""
    click.echo("Running security audit...")
    # TODO: implement

if __name__ == "__main__":
    cli()
