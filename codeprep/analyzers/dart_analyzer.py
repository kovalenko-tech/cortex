"""Dart/Flutter analyzer using regex."""
import os
import re
from pathlib import Path
from .base import BaseAnalyzer, FileAnalysis, CodeConstruct


CLASS_RE = re.compile(r'(?:abstract\s+)?class\s+(\w+)', re.MULTILINE)
FUNC_RE = re.compile(r'^\s+(?:static\s+)?(?:Future<[^>]+>|void|String|int|bool|Widget|[\w<>?]+)\s+(\w+)\s*\(', re.MULTILINE)
IMPORT_RE = re.compile(r"import\s+'([^']+)'", re.MULTILINE)


class DartAnalyzer(BaseAnalyzer):
    extensions = ('.dart',)

    def analyze(self, filepath: str, repo_root: str) -> FileAnalysis:
        result = FileAnalysis(language="dart")
        try:
            source = Path(filepath).read_text(encoding='utf-8', errors='ignore')
        except OSError:
            return result

        for m in CLASS_RE.finditer(source):
            line = source[:m.start()].count('\n') + 1
            result.constructs.append(CodeConstruct(name=m.group(1), kind="class", line=line))

        for m in FUNC_RE.finditer(source):
            name = m.group(1)
            if name not in ('build', 'main') or True:
                line = source[:m.start()].count('\n') + 1
                result.constructs.append(CodeConstruct(name=name, kind="function", line=line))

        for m in IMPORT_RE.finditer(source):
            result.imports.append(m.group(1))

        # Find test files
        stem = Path(filepath).stem
        test_dir = os.path.join(repo_root, 'test')
        if os.path.isdir(test_dir):
            for root, _, files in os.walk(test_dir):
                for f in files:
                    if f.endswith('_test.dart') and stem in f:
                        rel = os.path.relpath(os.path.join(root, f), repo_root)
                        result.test_files.append(rel)

        if result.test_files:
            result.checklist.append(f"Run: flutter test {result.test_files[0]}")
        else:
            result.checklist.append("Run: flutter test")

        return result
