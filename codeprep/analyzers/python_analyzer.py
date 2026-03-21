"""Python AST analyzer."""
import ast
import os
import re
from pathlib import Path
from .base import BaseAnalyzer, FileAnalysis, CodeConstruct


class PythonAnalyzer(BaseAnalyzer):
    extensions = ('.py',)

    def analyze(self, filepath: str, repo_root: str) -> FileAnalysis:
        result = FileAnalysis(language="python")
        try:
            source = Path(filepath).read_text(encoding='utf-8', errors='ignore')
        except OSError:
            return result

        try:
            tree = ast.parse(source)
        except SyntaxError:
            return result

        # Extract constructs
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                doc = ast.get_docstring(node) or ""
                result.constructs.append(CodeConstruct(
                    name=node.name,
                    kind="function",
                    line=node.lineno,
                    docstring=doc[:120] if doc else "",
                ))
            elif isinstance(node, ast.ClassDef):
                doc = ast.get_docstring(node) or ""
                result.constructs.append(CodeConstruct(
                    name=node.name,
                    kind="class",
                    line=node.lineno,
                    docstring=doc[:120] if doc else "",
                ))

        # Extract imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    result.imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    result.imports.append(node.module)

        # Find test files
        module_name = Path(filepath).stem
        for root, dirs, files in os.walk(repo_root):
            dirs[:] = [d for d in dirs if d not in ('node_modules', '.git', '__pycache__', 'build', 'dist')]
            for f in files:
                if f.endswith('.py') and ('test' in f.lower() or 'spec' in f.lower()):
                    test_path = os.path.join(root, f)
                    try:
                        content = Path(test_path).read_text(encoding='utf-8', errors='ignore')
                        if module_name in content:
                            rel = os.path.relpath(test_path, repo_root)
                            result.test_files.append(rel)
                    except OSError:
                        pass

        if result.test_files:
            result.checklist.append(f"Run: pytest {' '.join(result.test_files[:3])} -v")

        return result
