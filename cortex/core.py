"""Main orchestrator."""
import os
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

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

CACHE_FILE = '.cortex-cache.json'


def load_cache(repo_root: str) -> dict:
    cache_path = Path(repo_root) / CACHE_FILE
    if cache_path.exists():
        try:
            return json.loads(cache_path.read_text())
        except Exception:
            pass
    return {}


def save_cache(repo_root: str, cache: dict) -> None:
    from datetime import datetime
    cache['_last_run'] = datetime.now().strftime('%Y-%m-%d %H:%M')
    cache_path = Path(repo_root) / CACHE_FILE
    cache_path.write_text(json.dumps(cache, indent=2))


def file_hash(filepath: str) -> str:
    try:
        return hashlib.md5(Path(filepath).read_bytes()).hexdigest()
    except Exception:
        return ""


def get_changed_files(repo_path: str, since: str) -> set[str]:
    """Return set of relative file paths changed since `since`.
    
    Supports:
    - HEAD~10 (last 10 commits)
    - main...HEAD (diff vs branch)  
    - main (diff vs branch, shorthand)
    - 2024-01-01 (since date)
    """
    import git
    repo = git.Repo(repo_path, search_parent_directories=True)
    try:
        # If format is "branch...HEAD" or "branch..HEAD", use as-is (three-dot diff)
        if '...' in since or '..' in since:
            diff = repo.git.diff('--name-only', since)
        else:
            # Otherwise treat as "since this ref" — get files changed after it
            diff = repo.git.diff('--name-only', since, 'HEAD')
        return set(line.strip() for line in diff.splitlines() if line.strip())
    except git.GitCommandError:
        return set()


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
    def _analyze_file(self, filepath, repo_root, cochange_map, no_llm=False):
        """Analyze a single file — runs in thread pool."""
        from . import risk as risk_module

        rel = os.path.relpath(filepath, repo_root)

        analyzer = next((a for a in ANALYZERS if a.can_analyze(filepath)), None)
        analysis = analyzer.analyze(filepath, repo_root) if analyzer else None

        try:
            insights = git_history.get_insights(repo_root, rel)
        except Exception:
            insights = []

        related = cochange.get_related_files(cochange_map, rel)

        security_issues = []
        secret_findings = []
        if filepath.endswith('.py'):
            security_issues = run_bandit(filepath)
        security_issues += run_semgrep(filepath)
        try:
            secret_findings = scan_git_history(repo_root, rel)
        except Exception:
            pass

        from .analyzers.base import FileAnalysis
        from datetime import datetime, timezone
        if analysis is None:
            analysis = FileAnalysis(language="unknown")

        # Compute change count and bug fix count
        change_count = risk_module.get_change_count(repo_root, rel)
        bug_fix_count = len([i for i in insights if i.type == 'bug_fix'])
        security_count = len(security_issues) + len(secret_findings)
        has_tests = bool(analysis.test_files)

        # Compute risk score (dependents_count=0 here; updated later in analyze())
        risk = risk_module.compute_risk_score(
            file=rel,
            bug_fix_count=bug_fix_count,
            change_count=change_count,
            has_tests=has_tests,
            security_issues=security_count,
            dependents_count=0,
            cochange_count=0,
        )

        analyzed_at = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
        content = markdown_gen.generate(
            filepath, repo_root, insights, related,
            analysis, security_issues, secret_findings,
            no_llm=no_llm,
            analyzed_at=analyzed_at,
            risk_level=risk.level,
            risk_score=risk.score,
            risk_reasons=risk.reasons,
        )
        markdown_gen.write_doc(content, filepath, repo_root)

        return {
            'file': rel,
            'language': analysis.language,
            'constructs': len(analysis.constructs),
            'security_count': security_count,
            'has_tests': has_tests,
            'change_count': change_count,
            'bug_fix_count': bug_fix_count,
            'risk_level': risk.level,
            'risk_score': risk.score,
            'risk_reasons': risk.reasons,
            'risk_icon': risk.icon,
            'security_issues': [
                {'file': rel, 'severity': i.severity, 'line': i.line, 'message': i.message}
                for i in security_issues
            ],
        }

    def _print_completion(self, repo_root, file_results, security_items, start_time):
        import time
        from pathlib import Path

        elapsed = time.time() - start_time
        is_first_run = not (Path(repo_root) / '.cortex-cache.json').exists()

        console.print()
        console.rule("[bold green]Analysis Complete[/]")
        console.print()

        # Stats
        console.print(f"  [green]✓[/] [bold]{len(file_results)}[/] files analyzed in {elapsed:.1f}s")

        lang_counts = {}
        for r in file_results:
            lang = r.get('language', 'unknown')
            lang_counts[lang] = lang_counts.get(lang, 0) + 1
        lang_str = '  '.join(f"[cyan]{lang}[/] {count}" for lang, count in sorted(lang_counts.items()) if lang != 'unknown')
        if lang_str:
            console.print(f"  [green]✓[/] Languages: {lang_str}")

        files_without_tests = sum(1 for r in file_results if not r.get('has_tests'))
        if files_without_tests > 0:
            console.print(f"  [yellow]⚠[/]  {files_without_tests} files without tests")

        if security_items:
            high = sum(1 for i in security_items if i.get('severity') == 'HIGH')
            console.print(f"  [red]⚠[/]  {len(security_items)} security issues ({high} high) — run [bold]cortex security[/]")
        else:
            console.print(f"  [green]✓[/] No security issues found")

        console.print()
        console.print(f"  Context written to [cyan].claude/docs/[/]")
        console.print()

        # Next steps — show on first run
        if is_first_run:
            console.rule("[bold]Next Steps[/]")
            console.print()
            console.print("  [bold]Option A — Manual (works now):[/]")
            console.print("  Add to your CLAUDE.md:")
            console.print()
            console.print('  [dim]Before editing any file, run:[/]')
            console.print('  [cyan]python .claude/get_context.py <file_path>[/]')
            console.print()
            console.print("  [bold]Option B — Automatic via MCP:[/]")
            console.print("  Add to [cyan].claude/settings.json[/]:")
            console.print()
            console.print('  [dim]{"mcpServers": {"cortex": {"command": "cortex", "args": ["mcp"]}}}[/]')
            console.print()
            console.print("  [bold]Commit to your repo:[/]")
            console.print("  [cyan]git add .claude/ && git commit -m 'add cortex context'[/]")
            console.print()
            console.print("  [bold]Keep context fresh:[/]")
            console.print("  [cyan]cortex install-hook[/]  [dim]# auto-update on every commit[/]")
            console.print()
        else:
            console.print("  Run [cyan]cortex status[/] for details")
            console.print()

    def analyze(self, repo_path: str = '.', since: str | None = None,
                languages: list[str] | None = None, no_cache: bool = False,
                no_llm: bool = False, max_files: int = 0) -> None:
        import time
        start_time = time.time()
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

        # Limit files if requested
        if max_files > 0:
            files = files[:max_files]

        # Load cache
        cache = {} if no_cache else load_cache(repo_root)

        # Filter out unchanged files (cache hit)
        files_to_analyze = []
        skipped = 0
        for f in files:
            rel = os.path.relpath(f, repo_root)
            h = file_hash(f)
            cached = cache.get(rel)
            # cached may be a plain hash string (old format) or a dict (new format)
            cached_hash = cached if isinstance(cached, str) else (cached.get('_hash', '') if isinstance(cached, dict) else '')
            if not no_cache and cached_hash == h:
                skipped += 1
            else:
                files_to_analyze.append((f, rel, h))

        if skipped:
            console.print(f"[dim]Cache: skipping {skipped} unchanged files[/]")

        # Build co-change map once
        console.print(f"[dim]Mining git history...[/]")
        try:
            cochange_map = cochange.get_cochange_map(repo_root)
        except Exception:
            cochange_map = {}

        file_results = []
        security_items = []

        max_workers = min(8, os.cpu_count() or 4)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Analyzing files...", total=len(files_to_analyze))

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(self._analyze_file, f, repo_root, cochange_map, no_llm): (f, rel, h)
                    for f, rel, h in files_to_analyze
                }
                for future in as_completed(futures):
                    progress.advance(task)
                    f, rel, h = futures[future]
                    try:
                        result = future.result()
                        file_results.append(result)
                        security_items.extend(result.pop('security_issues', []))
                        # Store hash temporarily; full dict written after risk recompute
                        cache[rel] = h
                    except Exception:
                        pass  # skip failed files silently

        # Recompute risk with dependents map (full picture after all files analyzed)
        from .risk import build_dependents_map, compute_risk_score as _compute_risk
        abs_files = [os.path.join(repo_root, r['file']) for r in file_results]
        dependents_map = build_dependents_map(repo_root, abs_files)
        for result in file_results:
            abs_path = os.path.join(repo_root, result['file'])
            dependents = dependents_map.get(abs_path, 0)
            if dependents > 0:
                # Recompute with actual dependents count
                risk = _compute_risk(
                    file=result['file'],
                    bug_fix_count=result.get('bug_fix_count', 0),
                    change_count=result.get('change_count', 0),
                    has_tests=result.get('has_tests', False),
                    security_issues=result.get('security_count', 0),
                    dependents_count=dependents,
                    cochange_count=0,
                )
                result['risk_level'] = risk.level
                result['risk_score'] = risk.score
                result['risk_reasons'] = risk.reasons
                result['risk_icon'] = risk.icon

        # Save cache — include risk data per file
        for result in file_results:
            rel = result['file']
            if rel in cache:
                # cache[rel] is a hash string; upgrade to dict
                cache[rel] = {
                    '_hash': cache[rel] if isinstance(cache[rel], str) else cache.get(rel, {}).get('_hash', ''),
                    'bug_fix_count': result.get('bug_fix_count', 0),
                    'change_count': result.get('change_count', 0),
                    'has_tests': result.get('has_tests', False),
                    'security_count': result.get('security_count', 0),
                    'risk_level': result.get('risk_level', 'LOW'),
                    'risk_score': result.get('risk_score', 0),
                    'risk_reasons': result.get('risk_reasons', []),
                    'risk_icon': result.get('risk_icon', '🟢'),
                }
        save_cache(repo_root, cache)

        # Write summary files
        summary_gen.write_summary(repo_root, file_results)
        summary_gen.write_security_report(repo_root, security_items)
        self._write_helper(repo_root)

        self._print_completion(repo_root, file_results, security_items, start_time)

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
