#!/usr/bin/env python3
"""
Simple duplicate code detector for Python projects.
Detects similar code blocks based on AST comparison.
"""

import ast
import sys
from pathlib import Path
from collections import defaultdict


def get_python_files(directory):
    """Get all Python files in a directory."""
    return list(Path(directory).rglob("*.py"))


def get_function_bodies(file_path):
    """Extract function bodies from a Python file."""
    functions = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Get the source lines of the function body
                source_lines = []
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                    start = node.lineno - 1
                    end = node.end_lineno if node.end_lineno else start + 1
                    source_lines = lines[start:end]
                    source = "".join(source_lines)
                    functions.append(
                        {
                            "file": file_path,
                            "name": node.name,
                            "lineno": node.lineno,
                            "source": source,
                            "lines": len(source_lines),
                        }
                    )
                except:
                    pass
    except SyntaxError:
        pass

    return functions


def similarity_score(source1, source2):
    """Calculate similarity between two code blocks."""
    if source1 == source2:
        return 1.0

    # Normalize code by removing comments and extra whitespace
    lines1 = [
        line.strip()
        for line in source1.split("\n")
        if line.strip() and not line.strip().startswith("#")
    ]
    lines2 = [
        line.strip()
        for line in source2.split("\n")
        if line.strip() and not line.strip().startswith("#")
    ]

    if not lines1 or not lines2:
        return 0.0

    # Simple similarity: count matching lines
    matches = sum(1 for l1, l2 in zip(lines1, lines2) if l1 == l2)
    max_len = max(len(lines1), len(lines2))

    return matches / max_len


def detect_duplicates(directory, min_lines=5, min_similarity=0.8):
    """Detect duplicate code in a directory."""
    duplicates = []
    python_files = get_python_files(directory)

    all_functions = []
    for file_path in python_files:
        # Skip migrations
        if "migrations" in str(file_path):
            continue
        all_functions.extend(get_function_bodies(file_path))

    # Compare all pairs
    for i, func1 in enumerate(all_functions):
        for func2 in all_functions[i + 1 :]:
            # Skip same function
            if func1["file"] == func2["file"] and func1["name"] == func2["name"]:
                continue

            # Check if lines match minimum requirement
            min_lines_check = min(func1["lines"], func2["lines"]) >= min_lines
            if not min_lines_check:
                continue

            # Calculate similarity
            similarity = similarity_score(func1["source"], func2["source"])

            if similarity >= min_similarity:
                duplicates.append({"func1": func1, "func2": func2, "similarity": similarity})

    return duplicates


def main():
    directory = sys.argv[1] if len(sys.argv) > 1 else "medsystem/core"
    min_lines = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    min_similarity = float(sys.argv[3]) if len(sys.argv) > 3 else 0.8

    duplicates = detect_duplicates(directory, min_lines, min_similarity)

    if duplicates:
        print(f"\n❌ Found {len(duplicates)} duplicate code blocks:\n")
        for dup in duplicates:
            f1 = dup["func1"]
            f2 = dup["func2"]
            print(f"Duplicate found (similarity: {dup['similarity']*100:.1f}%):")
            print(f"  {f1['file']}:{f1['lineno']} ({f1['name']})")
            print(f"  {f2['file']}:{f2['lineno']} ({f2['name']})")
            print()
        return 1
    else:
        print("✅ No duplicate code found")
        return 0


if __name__ == "__main__":
    sys.exit(main())
