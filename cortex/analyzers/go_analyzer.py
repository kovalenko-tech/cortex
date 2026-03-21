"""Go analyzer using regex."""
import os
import re
from pathlib import Path
from .base import BaseAnalyzer, FileAnalysis, CodeConstruct


FUNC_RE = re.compile(r'^func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)\s*\(', re.MULTILINE)
IMPORT_RE = re.compile(r'"([^"]+)"', re.MULTILINE)
IMPORT_BLOCK_RE = re.compile(r'import\s*\(([^)]+)\)', re.DOTALL)


class GoAnalyzer(BaseAnalyzer):
    extensions = ('.go',)

    def analyze(self, filepath: str, repo_root: str) -> FileAnalysis:
        result = FileAnalysis(language="go")
        try:
            source = Path(filepath).read_text(encoding='utf-8', errors='ignore')
        except OSError:
            return result

        for m in FUNC_RE.finditer(source):
            line = source[:m.start()].count('\n') + 1
            result.constructs.append(CodeConstruct(name=m.group(1), kind="function", line=line))

        for block in IMPORT_BLOCK_RE.finditer(source):
            for m in IMPORT_RE.finditer(block.group(1)):
                result.imports.append(m.group(1))

        # Find test files
        stem = Path(filepath).stem
        if not stem.endswith('_test'):
            test_file = os.path.join(os.path.dirname(filepath), f"{stem}_test.go")
            if os.path.exists(test_file):
                result.test_files.append(os.path.relpath(test_file, repo_root))
                result.checklist.append(f"Run: go test ./...")

        return result
