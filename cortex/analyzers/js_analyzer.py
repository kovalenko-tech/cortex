"""JavaScript/TypeScript analyzer using tree-sitter or regex fallback."""
import os
import re
from pathlib import Path
from .base import BaseAnalyzer, FileAnalysis, CodeConstruct


FUNC_RE = re.compile(
    r'(?:export\s+)?(?:async\s+)?(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s+)?\(|(\w+)\s*\([^)]*\)\s*\{)',
    re.MULTILINE
)
CLASS_RE = re.compile(r'(?:export\s+)?class\s+(\w+)', re.MULTILINE)
IMPORT_RE = re.compile(r"(?:import|require)\s*\(?['\"]([^'\"]+)['\"]", re.MULTILINE)


class JSAnalyzer(BaseAnalyzer):
    extensions = ('.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs')

    def analyze(self, filepath: str, repo_root: str) -> FileAnalysis:
        result = FileAnalysis(language="javascript" if filepath.endswith(('.js', '.jsx', '.mjs', '.cjs')) else "typescript")
        try:
            source = Path(filepath).read_text(encoding='utf-8', errors='ignore')
        except OSError:
            return result

        # Extract functions
        for m in FUNC_RE.finditer(source):
            name = m.group(1) or m.group(2) or m.group(3)
            if name and not name.startswith('_') and len(name) > 1:
                line = source[:m.start()].count('\n') + 1
                result.constructs.append(CodeConstruct(name=name, kind="function", line=line))

        # Extract classes
        for m in CLASS_RE.finditer(source):
            line = source[:m.start()].count('\n') + 1
            result.constructs.append(CodeConstruct(name=m.group(1), kind="class", line=line))

        # Extract imports
        for m in IMPORT_RE.finditer(source):
            result.imports.append(m.group(1))

        # Find test files
        stem = Path(filepath).stem
        for root, dirs, files in os.walk(repo_root):
            dirs[:] = [d for d in dirs if d not in ('node_modules', '.git', 'build', 'dist', '.next')]
            for f in files:
                if f.endswith(('.test.ts', '.test.js', '.spec.ts', '.spec.js', '.test.tsx', '.spec.tsx')):
                    if stem in f:
                        rel = os.path.relpath(os.path.join(root, f), repo_root)
                        result.test_files.append(rel)

        if result.test_files:
            result.checklist.append(f"Run: npx jest {result.test_files[0]}")

        return result
