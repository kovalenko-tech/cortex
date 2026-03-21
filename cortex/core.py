"""Main orchestrator."""
import os
from pathlib import Path


def get_changed_files(repo_path: str, since: str) -> set[str]:
    """Return set of relative file paths changed since `since` (e.g. HEAD~10, 2024-01-01)."""
    import git
    repo = git.Repo(repo_path, search_parent_directories=True)
    try:
        diff = repo.git.diff('--name-only', since, 'HEAD')
        return set(line.strip() for line in diff.splitlines() if line.strip())
    except git.GitCommandError:
        return set()

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from .miners import git_history, cochange
from .analyzers.python_analyzer import PythonAnalyzer
from .analyzers.js_analyzer import JSAnalyzer
from .analyzers.dart_analyzer import DartAnalyzer
from .analyzers.go_analyzer import GoAnalyzer
from .security.bandit_runner import run_bandit
from .security.semgrep_runner import run_semgrep
from .security.secrets_scanner import scan_git_history
from .generators import markdown_gen, summary_gen

console = Console()

SKIP_DIRS = {
    'node_modules', '.git', '__pycache__', 'build', 'dist', '.next',
    'vendor', 'venv', '.venv', 'env', '.env', 'target', 'out', '.idea',
    '.gradle', 'Pods', '.dart_tool', '.pub-cache',
}

SKIP_FILES = {
    'package-lock.json', 'yarn.lock', 'pubspec.lock', 'go.sum',
    'Podfile.lock', '.flutter-plugins', '.flutter-plugins-dependencies',
}

ANALYZERS = [PythonAnalyzer(), JSAnalyzer(), DartAnalyzer(), GoAnalyzer()]


def discover_files(repo_root: str, languages: list[str] | None = None) -> list[str]:
    """Find all analyzable source files in repo."""
    all_exts = set()
    active = ANALYZERS
    if languages:
        lang_map = {
            'python': ('.py',), 'js': ('.js', '.jsx', '.mjs'), 'ts': ('.ts', '.tsx'),
            'dart': ('.dart',), 'go': ('.go',),
        }
        active_exts = set()
        for lang in languages:
            active_exts.update(lang_map.get(lang.lower(), ()))
        active = [a for a in ANALYZERS if any(e in active_exts for e in a.extensions)]

    for a in active:
        all_exts.update(a.extensions)

    files = []
    for root, dirs, filenames in os.walk(repo_root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')]
        for f in filenames:
            if f in SKIP_FILES:
                continue
            if any(f.endswith(ext) for ext in all_exts):
                full = os.path.join(root, f)
                if os.path.getsize(full) < 500_000:
                    files.append(full)

    # Load .cortexignore patterns
    import fnmatch
    ignore_patterns = []
    cortexignore = Path(repo_root) / '.cortexignore'
    if cortexignore.exists():
        for line in cortexignore.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith('#'):
                ignore_patterns.append(line)

    # Filter files
    if ignore_patterns:
        filtered = []
        for f in files:
            rel = os.path.relpath(f, repo_root)
            if not any(fnmatch.fnmatch(rel, p) for p in ignore_patterns):
                filtered.append(f)
        files = filtered

    return files


class Cortex:
    def analyze(self, repo_path: str = '.', since: str | None = None,
                languages: list[str] | None = None) -> None:
        repo_root = os.path.abspath(repo_path)
        console.print(f"\n[bold blue]Cortex[/] analyzing [cyan]{repo_root}[/]\n")

        files = discover_files(repo_root, languages)
        if not files:
            console.print("[yellow]No source files found.[/]")
            return

        # Incremental mode: filter to only changed files
        if since:
            changed = get_changed_files(repo_root, since)
            before = len(files)
            files = [f for f in files if os.path.relpath(f, repo_root) in changed]
            console.print(f"[dim]Incremental mode: {len(files)} files changed since {since}[/]")

        # Build co-change map once
        console.print(f"[dim]Mining git history...[/]")
        try:
            cochange_map = cochange.get_cochange_map(repo_root)
        except Exception:
            cochange_map = {}

        file_results = []
        security_items = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Analyzing files...", total=len(files))

            for filepath in files:
                rel = os.path.relpath(filepath, repo_root)
                progress.update(task, description=f"[dim]{rel[:50]}[/]", advance=1)

                # Find right analyzer
                analyzer = next((a for a in ANALYZERS if a.can_analyze(filepath)), None)
                analysis = analyzer.analyze(filepath, repo_root) if analyzer else None

                # Git history
                try:
                    insights = git_history.get_insights(repo_root, rel)
                except Exception:
                    insights = []

                # Co-change
                related = cochange.get_related_files(cochange_map, rel)

                # Security
                security_issues = []
                secret_findings = []
                if filepath.endswith('.py'):
                    security_issues = run_bandit(filepath)
                security_issues += run_semgrep(filepath)
                try:
                    secret_findings = scan_git_history(repo_root, rel)
                except Exception:
                    pass

                # Generate markdown
                from .analyzers.base import FileAnalysis
                if analysis is None:
                    analysis = FileAnalysis(language="unknown")

                content = markdown_gen.generate(
                    filepath, repo_root, insights, related,
                    analysis, security_issues, secret_findings
                )
                markdown_gen.write_doc(content, filepath, repo_root)

                # Collect stats
                file_results.append({
                    'file': rel,
                    'language': analysis.language,
                    'constructs': len(analysis.constructs),
                    'security_count': len(security_issues) + len(secret_findings),
                    'has_tests': bool(analysis.test_files),
                })
                for issue in security_issues:
                    security_items.append({
                        'file': rel, 'severity': issue.severity,
                        'line': issue.line, 'message': issue.message,
                    })

        # Write summary files
        summary_gen.write_summary(repo_root, file_results)
        summary_gen.write_security_report(repo_root, security_items)
        self._write_helper(repo_root)

        docs_path = os.path.join(repo_root, '.claude', 'docs')
        console.print(f"\n[green]✓[/] Done! Context written to [cyan].claude/docs/[/]")
        console.print(f"  Files analyzed: [bold]{len(files)}[/]")
        console.print(f"  Security issues: [bold]{len(security_items)}[/]")
        console.print(f"\n[dim]Commit .claude/ to your repo so Claude Code always has context.[/]\n")

    def _write_helper(self, repo_root: str) -> None:
        helper = Path(repo_root) / ".claude" / "get_context.py"
        helper.parent.mkdir(parents=True, exist_ok=True)
        helper.write_text(
            '#!/usr/bin/env python3\n'
            '"""Print context for a file — used by Claude Code."""\n'
            'import sys, pathlib\n'
            'file = sys.argv[1] if len(sys.argv) > 1 else "."\n'
            'doc = pathlib.Path(f".claude/docs/{file}.md")\n'
            'if doc.exists():\n'
            '    print(doc.read_text())\n'
            'else:\n'
            '    print(f"No context for {file}. Run: cortex analyze")\n'
        )
