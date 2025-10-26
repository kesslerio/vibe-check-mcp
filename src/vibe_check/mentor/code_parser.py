"""
Code parsing and structure extraction.

Provides language-specific parsers for extracting code structure,
functions, classes, and relevant context from various programming languages.
"""

import ast
import re
import logging
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)


class CodeParser:
    """Extract relevant context from code files"""

    @staticmethod
    def parse_python_file(content: str) -> Dict[str, Any]:
        """
        Parse Python file to extract structure.

        Returns:
            Dict with classes, functions, imports
        """
        result: Dict[str, Any] = {
            "classes": [],
            "functions": [],
            "imports": [],
            "docstrings": {},
        }

        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    result["classes"].append(node.name)
                    # Extract class docstring
                    docstring = ast.get_docstring(node)
                    if docstring:
                        result["docstrings"][f"class:{node.name}"] = docstring[:200]

                elif isinstance(node, ast.FunctionDef) or isinstance(
                    node, ast.AsyncFunctionDef
                ):
                    # Only top-level functions or class methods
                    result["functions"].append(node.name)
                    # Extract function docstring
                    docstring = ast.get_docstring(node)
                    if docstring:
                        result["docstrings"][f"func:{node.name}"] = docstring[:200]

                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        result["imports"].append(alias.name)

                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        result["imports"].append(node.module)

        except SyntaxError as e:
            logger.warning(f"Syntax error parsing Python file: {e}")
            # Fallback to regex-based extraction
            result["classes"] = re.findall(r"^class\s+(\w+)", content, re.MULTILINE)
            result["functions"] = re.findall(r"^def\s+(\w+)", content, re.MULTILINE)
            result["imports"] = re.findall(
                r"^(?:from|import)\s+([\w.]+)", content, re.MULTILINE
            )

        return result

    @staticmethod
    def parse_javascript_file(content: str) -> Dict[str, Any]:
        """
        Parse JavaScript/TypeScript file to extract structure.
        """
        result: Dict[str, Any] = {
            "classes": [],
            "functions": [],
            "imports": [],
            "exports": [],
            "interfaces": [],
            "types": [],
        }

        # Regex-based extraction for JS/TS
        result["classes"] = re.findall(r"class\s+(\w+)", content)
        result["functions"] = re.findall(
            r"(?:function|const|let|var)\s+(\w+)\s*=?\s*(?:\([^)]*\)|async)", content
        )
        result["imports"] = re.findall(
            r'import\s+.*?\s+from\s+["\']([^"\']+)["\']', content
        )
        result["exports"] = re.findall(
            r"export\s+(?:default\s+)?(?:class|function|const|let|var)\s+(\w+)", content
        )
        # TypeScript specific
        result["interfaces"] = re.findall(r"interface\s+(\w+)", content)
        result["types"] = re.findall(r"type\s+(\w+)\s*=", content)

        return result

    @staticmethod
    def parse_go_file(content: str) -> Dict[str, Any]:
        """
        Parse Go file to extract structure.
        """
        result: Dict[str, Any] = {
            "functions": [],
            "types": [],
            "interfaces": [],
            "imports": [],
            "packages": [],
        }

        # Go-specific patterns
        result["functions"] = re.findall(r"func\s+(?:\(.*?\)\s+)?(\w+)\s*\(", content)
        result["types"] = re.findall(r"type\s+(\w+)\s+struct", content)
        result["interfaces"] = re.findall(r"type\s+(\w+)\s+interface", content)
        result["imports"] = re.findall(
            r'import\s+(?:\(([^)]+)\)|"([^"]+)")', content, re.MULTILINE | re.DOTALL
        )
        result["packages"] = re.findall(r"^package\s+(\w+)", content, re.MULTILINE)

        return result

    @staticmethod
    def parse_rust_file(content: str) -> Dict[str, Any]:
        """
        Parse Rust file to extract structure.
        """
        result: Dict[str, Any] = {
            "functions": [],
            "structs": [],
            "enums": [],
            "traits": [],
            "impls": [],
            "mods": [],
            "uses": [],
        }

        # Rust-specific patterns
        result["functions"] = re.findall(r"(?:pub\s+)?fn\s+(\w+)", content)
        result["structs"] = re.findall(r"(?:pub\s+)?struct\s+(\w+)", content)
        result["enums"] = re.findall(r"(?:pub\s+)?enum\s+(\w+)", content)
        result["traits"] = re.findall(r"(?:pub\s+)?trait\s+(\w+)", content)
        result["impls"] = re.findall(r"impl(?:\s+<.*?>)?\s+(\w+)", content)
        result["mods"] = re.findall(r"(?:pub\s+)?mod\s+(\w+)", content)
        result["uses"] = re.findall(r"use\s+([^;]+);", content)

        return result

    @staticmethod
    def parse_java_file(content: str) -> Dict[str, Any]:
        """
        Parse Java file to extract structure.
        """
        result: Dict[str, Any] = {
            "classes": [],
            "interfaces": [],
            "methods": [],
            "imports": [],
            "packages": [],
        }

        # Java-specific patterns
        result["classes"] = re.findall(
            r"(?:public\s+)?(?:abstract\s+)?class\s+(\w+)", content
        )
        result["interfaces"] = re.findall(r"(?:public\s+)?interface\s+(\w+)", content)
        result["methods"] = re.findall(
            r"(?:public|private|protected)\s+(?:static\s+)?(?:\w+(?:<.*?>)?\s+)?(\w+)\s*\(",
            content,
        )
        result["imports"] = re.findall(r"import\s+([^;]+);", content)
        result["packages"] = re.findall(r"^package\s+([^;]+);", content, re.MULTILINE)

        return result

    @staticmethod
    def parse_generic_file(content: str) -> Dict[str, Any]:
        """
        Generic parser for other programming languages.
        Uses common patterns across many languages.
        """
        result: Dict[str, Any] = {
            "functions": [],
            "classes": [],
            "comments": [],
            "todos": [],
        }

        # Common patterns across languages
        # Functions: function, func, fn, def, sub
        result["functions"] = re.findall(
            r"(?:function|func|fn|def|sub)\s+(\w+)", content, re.IGNORECASE
        )
        # Classes: class, struct, type
        result["classes"] = re.findall(
            r"(?:class|struct|type)\s+(\w+)", content, re.IGNORECASE
        )
        # TODO comments
        result["todos"] = re.findall(
            r"(?://|#|/\*)\s*(TODO|FIXME|HACK|XXX|BUG|DEPRECATED)[:)]?\s*(.{0,100})",
            content,
            re.IGNORECASE,
        )

        return result

    @staticmethod
    def extract_relevant_context(
        content: str, query: str, language: str
    ) -> Dict[str, List[Tuple[int, str]]]:
        """
        Extract lines relevant to the query.

        Returns:
            Dict mapping relevance type to list of (line_number, line_content) tuples
        """
        relevant: Dict[str, List[Tuple[int, str]]] = {
            "direct_mentions": [],
            "related_functions": [],
            "related_classes": [],
            "potential_issues": [],
        }

        lines = content.split("\n")
        query_terms = set(query.lower().split())

        # Remove common words
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "as",
            "is",
            "was",
            "are",
            "were",
            "been",
            "be",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "must",
            "can",
            "could",
            "i",
            "you",
            "he",
            "she",
            "it",
            "we",
            "they",
            "what",
            "which",
            "who",
            "when",
            "where",
            "why",
            "how",
            "this",
            "that",
            "these",
            "those",
        }
        query_terms = query_terms - stop_words

        for i, line in enumerate(lines, 1):
            line_lower = line.lower()

            # Direct mentions of query terms
            if any(term in line_lower for term in query_terms if len(term) > 2):
                relevant["direct_mentions"].append((i, line))

            # Look for function/class definitions related to query
            if language == "python":
                if re.match(r"^(class|def)\s+\w+", line):
                    if any(term in line_lower for term in query_terms):
                        relevant["related_functions"].append((i, line))

            # Look for potential issues (TODO, FIXME, etc.)
            if re.search(r"(TODO|FIXME|HACK|XXX|BUG|DEPRECATED)", line, re.IGNORECASE):
                relevant["potential_issues"].append((i, line))

        # Limit results to most relevant
        for key in relevant:
            relevant[key] = relevant[key][:10]  # Max 10 lines per category

        return relevant
