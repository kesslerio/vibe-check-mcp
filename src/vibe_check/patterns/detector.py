"""Code pattern detector for source-level anti-patterns."""

from __future__ import annotations

import ast
import functools
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Set, Tuple

from ..models.severity import SeverityLevel, normalize_severity

MAGIC_NUMBER_PATTERN = re.compile(r"(?<![\w.])(-?\d+(?:\.\d+)?)")
MAGIC_STRING_PATTERN = re.compile(r"(['\"])(?P<value>[^'\"]{2,})\1")
COMMENT_PREFIXES: Tuple[str, ...] = ("#", "//")


@functools.lru_cache(maxsize=64)
def _parse_python_ast(source: str) -> Optional[ast.AST]:
    """Cache Python AST parsing to avoid repeated work."""

    try:
        return ast.parse(source)
    except SyntaxError:
        return None


@functools.lru_cache(maxsize=128)
def _split_lines_cached(source: str) -> Tuple[str, ...]:
    """Cache splitting logic to avoid repeated string scans."""

    return tuple(source.splitlines())


@functools.lru_cache(maxsize=128)
def _sanitize_lines_cached(source: str) -> Tuple[str, ...]:
    """Return normalized code lines cached by content."""

    sanitized: List[str] = []
    for raw in source.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith(COMMENT_PREFIXES):
            continue
        sanitized.append(re.sub(r"\s+", " ", stripped))
    return tuple(sanitized)


@dataclass
class PatternMatch:
    """Represents a detected anti-pattern."""

    pattern: str
    severity: str
    confidence: float
    details: Dict[str, object]


class PatternDetector:
    """Detects high-risk patterns inside source code."""

    def __init__(
        self,
        *,
        god_object_lines: int = 500,
        god_object_methods: int = 50,
        duplicate_window: int = 5,
        long_method_lines: int = 80,
        long_method_complexity: int = 10,
    ) -> None:
        self._god_line_threshold = god_object_lines
        self._god_method_threshold = god_object_methods
        self._duplicate_window = duplicate_window
        self._duplicate_min_occurrences = 2
        self._duplicate_report_limit = 3
        self._duplicate_confidence_divisor = 3
        self._magic_min_count = 4
        self._magic_sample_limit = 5
        self._magic_confidence_divisor = 6
        self._magic_elevated_threshold = 8
        self._allowed_magic_numbers = {"0", "1", "-1"}
        self._long_method_lines = long_method_lines
        self._long_method_complexity = long_method_complexity

    def analyze(self, code: str, language: str = "python") -> List[PatternMatch]:
        """Analyze code and return detected pattern matches."""

        if not isinstance(code, str):
            raise TypeError("code must be a string")

        sanitized = code.strip()
        if not sanitized:
            return []

        lang = (language or "python").lower()
        tree = _parse_python_ast(sanitized) if lang == "python" else None

        matches: List[PatternMatch] = []
        matches.extend(self._detect_god_object(tree))

        sanitized_lines = _sanitize_lines_cached(sanitized)
        if len(sanitized_lines) >= self._duplicate_window * self._duplicate_min_occurrences:
            matches.extend(self._detect_copy_paste(sanitized_lines))

        raw_lines = _split_lines_cached(sanitized)
        if len(raw_lines) >= self._magic_min_count:
            matches.extend(self._detect_magic_literals(raw_lines, tree))

        matches.extend(self._detect_long_methods(tree))
        return matches

    def _detect_god_object(self, tree: Optional[ast.AST]) -> List[PatternMatch]:
        """Detect oversized classes with too many responsibilities."""

        if tree is None:
            return []

        matches: List[PatternMatch] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue

            method_count = sum(isinstance(body_item, ast.FunctionDef) for body_item in node.body)
            if method_count < self._god_method_threshold:
                continue

            end = getattr(node, "end_lineno", None)
            class_length = self._estimate_span(node, end)
            if class_length < self._god_line_threshold:
                continue

            confidence = min(
                1.0,
                (class_length / self._god_line_threshold + method_count / self._god_method_threshold) / 2,
            )
            matches.append(
                PatternMatch(
                    pattern="god_object",
                    severity=normalize_severity(SeverityLevel.CRITICAL.value),
                    confidence=round(confidence, 2),
                    details={"class_name": node.name, "lines": class_length, "methods": method_count},
                )
            )
        return matches

    def _detect_copy_paste(self, lines: Sequence[str]) -> List[PatternMatch]:
        """Detect repeated code sequences indicative of duplication."""

        if len(lines) < self._duplicate_window * 2:
            return []

        windows: Dict[Tuple[str, ...], List[int]] = defaultdict(list)
        duplicates: List[Tuple[str, ...]] = []

        max_index = len(lines) - self._duplicate_window + 1
        for idx in range(max_index):
            window = tuple(lines[idx : idx + self._duplicate_window])
            if len(set(window)) <= 1:
                continue
            occurrences = windows[window]
            occurrences.append(idx)
            if len(occurrences) == self._duplicate_min_occurrences:
                duplicates.append(window)
            if len(duplicates) >= self._duplicate_report_limit:
                break

        if not duplicates:
            return []

        confidence = min(1.0, len(duplicates) / self._duplicate_confidence_divisor)
        examples = ["\n".join(window) for window in duplicates[: self._duplicate_report_limit]]
        return [
            PatternMatch(
                pattern="copy_paste_programming",
                severity=normalize_severity(SeverityLevel.WARNING.value),
                confidence=round(confidence, 2),
                details={"examples": examples},
            )
        ]

    def _detect_magic_literals(
        self,
        raw_lines: Sequence[str],
        tree: Optional[ast.AST],
    ) -> List[PatternMatch]:
        """Detect repeated magic numbers or strings."""

        numeric_hits: List[Tuple[int, str]]
        string_hits: List[Tuple[int, str]]

        if tree is not None:
            numeric_hits, string_hits = self._collect_literals_from_ast(tree)
        else:
            numeric_hits, string_hits = self._collect_literals_from_text(raw_lines)

        total = len(numeric_hits) + len(string_hits)
        if total < self._magic_min_count:
            return []

        confidence = min(1.0, total / self._magic_confidence_divisor)
        samples = [
            f"{value!r} (line {line})"
            for line, value in (numeric_hits + string_hits)[: self._magic_sample_limit]
        ]
        severity = SeverityLevel.CAUTION if total < self._magic_elevated_threshold else SeverityLevel.WARNING
        return [
            PatternMatch(
                pattern="magic_literals",
                severity=normalize_severity(severity.value),
                confidence=round(confidence, 2),
                details={"occurrences": total, "samples": samples},
            )
        ]

    def _detect_long_methods(self, tree: Optional[ast.AST]) -> List[PatternMatch]:
        """Detect complex functions that exceed maintainability thresholds."""

        if tree is None:
            return []

        matches: List[PatternMatch] = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            end = getattr(node, "end_lineno", None)
            if end is None:
                continue

            length = end - node.lineno + 1
            complexity = self._estimate_complexity(node)
            if length < self._long_method_lines and complexity < self._long_method_complexity:
                continue

            severity = SeverityLevel.WARNING
            if complexity >= self._long_method_complexity * 1.5 or length >= self._long_method_lines * 2:
                severity = SeverityLevel.CRITICAL

            confidence = min(
                1.0,
                (length / self._long_method_lines + complexity / self._long_method_complexity) / 2,
            )
            matches.append(
                PatternMatch(
                    pattern="long_method",
                    severity=normalize_severity(severity.value),
                    confidence=round(confidence, 2),
                    details={"function_name": node.name, "lines": length, "complexity": complexity},
                )
            )
        return matches

    def _collect_literals_from_ast(
        self, tree: ast.AST
    ) -> Tuple[List[Tuple[int, str]], List[Tuple[int, str]]]:
        """Return numeric and string literal hits derived from the AST."""

        docstring_lines = self._docstring_lines(tree)
        numeric_hits: List[Tuple[int, str]] = []
        string_hits: List[Tuple[int, str]] = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant):
                continue

            lineno = getattr(node, "lineno", None)
            if lineno is None or lineno in docstring_lines:
                continue

            value = node.value
            if isinstance(value, bool) or value is None:
                continue

            if isinstance(value, (int, float)):
                literal = str(value)
                if literal not in self._allowed_magic_numbers:
                    numeric_hits.append((lineno, literal))
                continue

            if isinstance(value, str):
                if len(value.strip()) <= 1 or "\n" in value:
                    continue
                string_hits.append((lineno, value))

        return numeric_hits, string_hits

    def _collect_literals_from_text(
        self, raw_lines: Sequence[str]
    ) -> Tuple[List[Tuple[int, str]], List[Tuple[int, str]]]:
        """Fallback literal detection using regex scanning."""

        numeric_hits: List[Tuple[int, str]] = []
        string_hits: List[Tuple[int, str]] = []

        for line_no, raw in enumerate(raw_lines, 1):
            stripped = raw.strip()
            if (
                not stripped
                or stripped.startswith(COMMENT_PREFIXES)
                or stripped.startswith(("\"\"\"", "'''"))
                or self._looks_like_constant(stripped)
            ):
                continue

            for match in MAGIC_NUMBER_PATTERN.finditer(stripped):
                value = match.group(1)
                if value not in self._allowed_magic_numbers:
                    numeric_hits.append((line_no, value))

            for match in MAGIC_STRING_PATTERN.finditer(stripped):
                string_hits.append((line_no, match.group("value")))

        return numeric_hits, string_hits

    def _docstring_lines(self, tree: ast.AST) -> Set[int]:
        """Return line numbers that belong to docstrings."""

        doc_lines: Set[int] = set()
        docstring_parents = (
            ast.Module,
            ast.ClassDef,
            ast.FunctionDef,
            ast.AsyncFunctionDef,
        )

        for node in ast.walk(tree):
            if not isinstance(node, docstring_parents):
                continue
            body = getattr(node, "body", [])
            if not body:
                continue
            first_stmt = body[0]
            if not isinstance(first_stmt, ast.Expr):
                continue
            value = getattr(first_stmt, "value", None)
            if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
                continue
            start = getattr(value, "lineno", None)
            end = getattr(value, "end_lineno", start)
            if start is None or end is None:
                continue
            doc_lines.update(range(start, end + 1))

        return doc_lines

    def _looks_like_constant(self, line: str) -> bool:
        """Return True if the line resembles a constant assignment."""

        return bool(re.match(r"^[A-Z0-9_]+\s*=", line))

    def _estimate_span(self, node: ast.AST, end_lineno: Optional[int]) -> int:
        """Estimate the line span of a node when end line metadata is missing."""

        if end_lineno is not None:
            return end_lineno - getattr(node, "lineno", end_lineno) + 1

        max_line = getattr(node, "lineno", 0)
        for child in ast.walk(node):
            child_line = getattr(child, "end_lineno", getattr(child, "lineno", max_line))
            max_line = max(max_line, child_line)
        return max_line - getattr(node, "lineno", max_line) + 1

    def _estimate_complexity(self, node: ast.AST) -> int:
        """Estimate cyclomatic complexity using branch counts."""

        complexity = 1
        branch_nodes = (
            ast.If,
            ast.For,
            ast.AsyncFor,
            ast.While,
            ast.Try,
            ast.With,
            ast.AsyncWith,
            ast.BoolOp,
            ast.IfExp,
        )
        for child in ast.walk(node):
            if isinstance(child, branch_nodes):
                complexity += 1
        return complexity


__all__ = ["PatternDetector", "PatternMatch"]

