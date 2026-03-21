"""Base analyzer interface."""
from dataclasses import dataclass, field


@dataclass
class CodeConstruct:
    name: str
    kind: str  # function | class | method
    line: int
    docstring: str = ""
    callers: list[str] = field(default_factory=list)


@dataclass
class FileAnalysis:
    language: str
    constructs: list[CodeConstruct] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    test_files: list[str] = field(default_factory=list)
    checklist: list[str] = field(default_factory=list)


class BaseAnalyzer:
    extensions: tuple[str, ...] = ()

    def can_analyze(self, filepath: str) -> bool:
        return any(filepath.endswith(ext) for ext in self.extensions)

    def analyze(self, filepath: str, repo_root: str) -> FileAnalysis:
        raise NotImplementedError
