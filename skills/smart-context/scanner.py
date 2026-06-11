#!/usr/bin/env python3
"""
Smart Context Scanner
Automatically detects project structure and creates a lightweight index.
Run this once when setting up, or let Claude run it dynamically.

Usage: python scanner.py [project_root]
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

class ProjectScanner:
    def __init__(self, root_path: str = "."):
        self.root = Path(root_path).resolve()
        self.index = {
            "generated": datetime.now().isoformat(),
            "root": str(self.root),
            "stack": {},
            "structure": {},
            "features": [],
            "patterns": {}
        }

    def scan(self) -> Dict:
        """Run full project scan."""
        print(f"Scanning: {self.root}")
        self._detect_stack()
        self._detect_structure()
        self._detect_features()
        self._detect_patterns()
        return self.index

    def _detect_stack(self):
        """Detect technology stack."""
        stack = {"frontend": None, "backend": None}

        # Frontend detection - search in root and subdirectories (for monorepos)
        package_files = list(self.root.rglob("package.json"))
        for pkg_path in package_files:
            if "node_modules" in str(pkg_path):
                continue
            try:
                with open(pkg_path) as f:
                    pkg = json.load(f)
                    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                    if "react" in deps:
                        stack["frontend"] = "react"
                        self.index["structure"]["frontend_root"] = str(pkg_path.parent.relative_to(self.root))
                        break
                    elif "vue" in deps:
                        stack["frontend"] = "vue"
                        self.index["structure"]["frontend_root"] = str(pkg_path.parent.relative_to(self.root))
                        break
                    elif "@angular/core" in deps:
                        stack["frontend"] = "angular"
                        self.index["structure"]["frontend_root"] = str(pkg_path.parent.relative_to(self.root))
                        break
                    elif "next" in deps:
                        stack["frontend"] = "nextjs"
                        self.index["structure"]["frontend_root"] = str(pkg_path.parent.relative_to(self.root))
                        break
            except:
                pass

        # Backend detection
        csproj_files = list(self.root.rglob("*.csproj"))
        if csproj_files:
            stack["backend"] = "dotnet"
            # Find the main API project
            for f in csproj_files:
                if "Api" in f.stem or "Web" in f.stem:
                    self.index["structure"]["backend_root"] = str(f.parent.relative_to(self.root))
                    break
        elif (self.root / "requirements.txt").exists() or (self.root / "pyproject.toml").exists():
            stack["backend"] = "python"
        elif (self.root / "go.mod").exists():
            stack["backend"] = "go"
        elif (self.root / "Cargo.toml").exists():
            stack["backend"] = "rust"
        elif (self.root / "pom.xml").exists() or (self.root / "build.gradle").exists():
            stack["backend"] = "java"

        self.index["stack"] = {k: v for k, v in stack.items() if v}

    def _detect_structure(self):
        """Detect project directory structure."""
        structure = {}

        # Common source directories
        src_patterns = ["src", "app", "lib", "packages", "source"]
        for pattern in src_patterns:
            for path in self.root.glob(f"*/{pattern}"):
                if path.is_dir():
                    rel_path = str(path.relative_to(self.root))
                    if "frontend" in rel_path.lower() or "react" in rel_path.lower() or "web" in rel_path.lower():
                        structure["frontend_src"] = rel_path
                    elif "backend" in rel_path.lower() or "api" in rel_path.lower() or "server" in rel_path.lower():
                        structure["backend_src"] = rel_path

        # Direct src folder
        if (self.root / "src").is_dir():
            structure["src"] = "src"

        # Look for src-prefixed backend roots (e.g., src-api, src-server)
        for path in self.root.glob("src-*"):
            if path.is_dir() and "backend_src" not in structure:
                structure["backend_src"] = path.name

        # Find controllers/services directories
        for path in self.root.rglob("Controllers"):
            if path.is_dir() and "bin" not in str(path) and "obj" not in str(path):
                structure["controllers"] = str(path.relative_to(self.root))
                break

        for path in self.root.rglob("Services"):
            if path.is_dir() and "bin" not in str(path) and "obj" not in str(path) and "node_modules" not in str(path):
                structure["services"] = str(path.relative_to(self.root))
                break

        self.index["structure"] = structure

    def _detect_features(self):
        """Detect feature/module names."""
        features = set()

        # Look for features/modules directories
        feature_dirs = ["features", "modules", "domains", "areas"]
        for dir_name in feature_dirs:
            for path in self.root.rglob(dir_name):
                if path.is_dir() and "node_modules" not in str(path) and "bin" not in str(path):
                    for child in path.iterdir():
                        if child.is_dir() and not child.name.startswith("."):
                            features.add(child.name)

        # Look for controller names (FeatureController.cs)
        for path in self.root.rglob("*Controller.cs"):
            if "bin" not in str(path) and "obj" not in str(path):
                name = path.stem.replace("Controller", "")
                if name and len(name) > 2:
                    features.add(name)

        # Clean up feature names
        self.index["features"] = sorted([f for f in features if len(f) > 2 and f[0].isupper()])[:50]

    def _detect_patterns(self):
        """Detect common file patterns in the project."""
        patterns = {}

        # Count file patterns
        pattern_counts = {}
        for ext in [".tsx", ".ts", ".cs", ".py", ".go", ".java", ".vue", ".svelte"]:
            for path in self.root.rglob(f"*{ext}"):
                if "node_modules" not in str(path) and "bin" not in str(path) and "obj" not in str(path):
                    name = path.stem
                    # Detect naming patterns
                    if name.endswith("Container"):
                        pattern_counts["container"] = pattern_counts.get("container", 0) + 1
                    elif name.endswith("Page"):
                        pattern_counts["page"] = pattern_counts.get("page", 0) + 1
                    elif name.endswith("Controller"):
                        pattern_counts["controller"] = pattern_counts.get("controller", 0) + 1
                    elif name.endswith("Service"):
                        pattern_counts["service"] = pattern_counts.get("service", 0) + 1
                    elif name.endswith(".hook") or name.endswith(".hooks"):
                        pattern_counts["hook"] = pattern_counts.get("hook", 0) + 1

        # Set patterns that appear frequently
        for pattern, count in pattern_counts.items():
            if count >= 3:
                patterns[pattern] = f"*{pattern.capitalize()}.*"

        self.index["patterns"] = patterns

    def save(self, output_path: Optional[str] = None):
        """Save index to file."""
        if output_path is None:
            cache_dir = self.root / ".claude" / "idev" / "smart-context"
            cache_dir.mkdir(parents=True, exist_ok=True)
            output_path = cache_dir / "index.json"
        else:
            output_path = Path(output_path)

        with open(output_path, "w") as f:
            json.dump(self.index, f, indent=2)

        print(f"Index saved to: {output_path}")
        return output_path


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    scanner = ProjectScanner(root)
    index = scanner.scan()

    print("\n=== Scan Results ===")
    print(f"Stack: {index['stack']}")
    print(f"Features found: {len(index['features'])}")
    print(f"Patterns: {index['patterns']}")

    scanner.save()


if __name__ == "__main__":
    main()
