"""Auto-generate CLAUDE.md for a project."""
import os
import json
from pathlib import Path
from collections import Counter


def detect_project_type(repo_root: str) -> dict:
    """Detect languages, frameworks, package managers."""
    root = Path(repo_root)
    info = {
        'languages': [],
        'frameworks': [],
        'package_managers': [],
        'test_runners': [],
        'build_commands': [],
        'lint_commands': [],
        'entry_points': [],
    }

    # Python
    if (root / 'pyproject.toml').exists() or (root / 'setup.py').exists() or (root / 'requirements.txt').exists():
        info['languages'].append('Python')
        if (root / 'pyproject.toml').exists():
            info['package_managers'].append('pip')
            content = (root / 'pyproject.toml').read_text(errors='ignore')
            if 'fastapi' in content.lower(): info['frameworks'].append('FastAPI')
            if 'django' in content.lower(): info['frameworks'].append('Django')
            if 'flask' in content.lower(): info['frameworks'].append('Flask')
        if (root / 'pytest.ini').exists() or any(root.glob('tests/')):
            info['test_runners'].append('pytest')
            info['build_commands'].append('pip install -e .')
            info['lint_commands'].append('ruff check .')

    # Node.js / TypeScript
    pkg = root / 'package.json'
    if pkg.exists():
        try:
            data = json.loads(pkg.read_text(errors='ignore'))
            deps = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
            info['languages'].append('TypeScript' if (root / 'tsconfig.json').exists() else 'JavaScript')
            info['package_managers'].append('npm' if (root / 'package-lock.json').exists() else 'yarn' if (root / 'yarn.lock').exists() else 'pnpm')
            if 'next' in deps: info['frameworks'].append('Next.js')
            if 'react' in deps: info['frameworks'].append('React')
            if 'express' in deps: info['frameworks'].append('Express')
            if 'jest' in deps or '@jest/core' in deps: info['test_runners'].append('jest')
            if 'vitest' in deps: info['test_runners'].append('vitest')
            scripts = data.get('scripts', {})
            if 'build' in scripts: info['build_commands'].append(f"npm run build")
            if 'test' in scripts: info['test_runners'] = info['test_runners'] or ['npm test']
            if 'lint' in scripts: info['lint_commands'].append('npm run lint')
            if 'dev' in scripts: info['build_commands'].append('npm run dev')
        except Exception:
            pass

    # Flutter/Dart
    if (root / 'pubspec.yaml').exists():
        info['languages'].append('Dart')
        info['frameworks'].append('Flutter')
        info['package_managers'].append('pub')
        info['test_runners'].append('flutter test')
        info['build_commands'].append('flutter pub get')
        info['lint_commands'].append('flutter analyze')

    # Go
    if (root / 'go.mod').exists():
        info['languages'].append('Go')
        info['package_managers'].append('go mod')
        info['test_runners'].append('go test ./...')
        info['build_commands'].append('go build ./...')
        info['lint_commands'].append('go vet ./...')

    # Find entry points
    for entry in ['main.py', 'app.py', 'server.py', 'index.ts', 'index.js', 'main.go', 'lib/main.dart', 'cmd/main.go']:
        if (root / entry).exists():
            info['entry_points'].append(entry)

    return info


def detect_architecture(repo_root: str) -> dict:
    """Detect project structure patterns."""
    root = Path(repo_root)
    arch = {'pattern': 'unknown', 'key_dirs': [], 'description': ''}

    dirs = [d.name for d in root.iterdir() if d.is_dir() and not d.name.startswith('.')]

    if 'src' in dirs and 'tests' in dirs:
        arch['pattern'] = 'src-layout'
        arch['key_dirs'] = ['src/', 'tests/']
    elif 'lib' in dirs and 'test' in dirs:
        arch['pattern'] = 'lib-layout'
        arch['key_dirs'] = ['lib/', 'test/']
    elif 'api' in dirs or 'routes' in dirs:
        arch['pattern'] = 'api-first'
        arch['key_dirs'] = [d for d in ['api/', 'routes/', 'models/', 'services/'] if (root / d.rstrip('/')).exists()]
    elif 'packages' in dirs or 'apps' in dirs:
        arch['pattern'] = 'monorepo'
        arch['key_dirs'] = [d for d in ['packages/', 'apps/', 'libs/'] if (root / d.rstrip('/')).exists()]
    elif 'lib' in dirs:
        arch['pattern'] = 'flutter-standard'
        arch['key_dirs'] = ['lib/', 'test/', 'assets/']

    arch['description'] = {
        'src-layout': 'Source code in src/, tests in tests/',
        'lib-layout': 'Source code in lib/, tests in test/',
        'api-first': 'API-first structure with routes, models, services',
        'monorepo': 'Monorepo with multiple packages/apps',
        'flutter-standard': 'Flutter standard layout',
        'unknown': 'Custom project structure',
    }.get(arch['pattern'], '')

    return arch


def generate_claude_md(repo_root: str, project_info: dict, arch: dict) -> str:
    """Generate CLAUDE.md content."""
    lines = ['# CLAUDE.md', '']
    lines.append('This file provides context for Claude Code working in this repository.')
    lines.append('')

    # Project overview
    lines.append('## Project Overview')
    if project_info['languages']:
        lines.append(f"**Languages:** {', '.join(project_info['languages'])}")
    if project_info['frameworks']:
        lines.append(f"**Frameworks:** {', '.join(project_info['frameworks'])}")
    if arch['pattern'] != 'unknown':
        lines.append(f"**Structure:** {arch['description']}")
    if project_info['entry_points']:
        lines.append(f"**Entry points:** {', '.join(project_info['entry_points'])}")
    lines.append('')

    # Key directories
    if arch['key_dirs']:
        lines.append('## Key Directories')
        for d in arch['key_dirs']:
            lines.append(f'- `{d}`')
        lines.append('')

    # Commands
    lines.append('## Commands')
    lines.append('')

    if project_info['build_commands']:
        lines.append('### Setup')
        lines.append('```bash')
        for cmd in project_info['build_commands'][:2]:
            lines.append(cmd)
        lines.append('```')
        lines.append('')

    if project_info['test_runners']:
        lines.append('### Tests')
        lines.append('```bash')
        for cmd in project_info['test_runners'][:2]:
            lines.append(cmd)
        lines.append('```')
        lines.append('')

    if project_info['lint_commands']:
        lines.append('### Lint')
        lines.append('```bash')
        for cmd in project_info['lint_commands'][:2]:
            lines.append(cmd)
        lines.append('```')
        lines.append('')

    # Context
    lines.append('## Project Context')
    lines.append('')
    lines.append('Before editing any file, get its full context:')
    lines.append('```bash')
    lines.append('python .claude/get_context.py <file_path>')
    lines.append('```')
    lines.append('')
    lines.append('This shows historical bugs, pitfalls, related files and security notes.')
    lines.append('')

    # Guidelines
    lines.append('## Guidelines')
    lines.append('')
    lines.append('- Always run tests after making changes')
    lines.append('- Check `.claude/docs/` for context before editing a file')
    lines.append('- Run `cortex analyze --since HEAD~1` after significant changes to update context')
    lines.append('')

    return '\n'.join(lines)


def write_claude_md(repo_root: str) -> str:
    """Generate and write CLAUDE.md. Returns path."""
    project_info = detect_project_type(repo_root)
    arch = detect_architecture(repo_root)
    content = generate_claude_md(repo_root, project_info, arch)

    output_path = Path(repo_root) / 'CLAUDE.md'
    output_path.write_text(content, encoding='utf-8')
    return str(output_path)
