#!/usr/bin/env python3
"""
Smart Context Scanner
Automatically detects project structure and creates a lightweight index.
Run this once when setting up, or let Claude run it dynamically.

Usage: python3 scanner.py [project_root]
Writes <project_root>/.claude/idev/smart-context/index.json
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

# Directories pruned during traversal (never descended into)
IGNORED_DIRS = {
    "node_modules", ".git", "bin", "obj", "dist", "build",
    ".next", "venv", ".venv", "__pycache__", "coverage",
}


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
        self._files = []
        self._dirs = []

    def _walk(self):
        """Single os.walk pass, pruning ignored dirs; caches files and dirs."""
        files, dirs = [], []
        for dirpath, dirnames, filenames in os.walk(self.root):
            dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS]
            base = Path(dirpath)
            for d in dirnames:
                dirs.append(base / d)
            for f in filenames:
                files.append(base / f)
        self._files = files
        self._dirs = dirs

    def scan(self) -> Dict:
        """Run full project scan."""
        print(f"Scanning: {self.root}")
        self._walk()
        self._detect_stack()
        self._detect_structure()
        self._detect_features()
        self._detect_patterns()
        return self.index

    def _detect_stack(self):
        """Detect technology stack."""
        stack = {"frontend": None, "backend": None}

        # Frontend detection — deterministic: sort candidates by path depth,
        # prefer the shallowest package.json (root before monorepo subpackages)
        package_files = sorted(
            (p for p in self._files if p.name == "package.json"),
            key=lambda p: (len(p.relative_to(self.root).parts), str(p)),
        )
        for pkg_path in package_files:
            try:
                with open(pkg_path) as f:
                    pkg = json.load(f)
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            except Exception:
                continue
            # Check next BEFORE react: Next.js apps also depend on react
            if "next" in deps:
                stack["frontend"] = "nextjs"
            elif "react" in deps:
                stack["frontend"] = "react"
            elif "vue" in deps:
                stack["frontend"] = "vue"
            elif "@angular/core" in deps:
                stack["frontend"] = "angular"
            else:
                continue
            self.index["structure"]["frontend_root"] = str(
                pkg_path.parent.relative_to(self.root))
            break

        # Backend detection
        csproj_files = sorted(p for p in self._files if p.suffix == ".csproj")
        if csproj_files:
            stack["backend"] = "dotnet"
            # Find the main API project
            for f in csproj_files:
                if "Api" in f.stem or "Web" in f.stem:
                    self.index["structure"]["backend_root"] = str(
                        f.parent.relative_to(self.root))
                    break
        else:
            # Check the root AND one level of subdirectories (backend/, server/,
            # api/, ...) for backend markers
            markers = [
                (("requirements.txt", "pyproject.toml"), "python"),
                (("go.mod",), "go"),
                (("Cargo.toml",), "rust"),
                (("pom.xml", "build.gradle"), "java"),
            ]
            candidates = [self.root] + sorted(
                p for p in self.root.iterdir()
                if p.is_dir() and p.name not in IGNORED_DIRS
                and not p.name.startswith(".")
            )
            for d in candidates:
                for names, lang in markers:
                    if any((d / n).exists() for n in names):
                        stack["backend"] = lang
                        if d != self.root:
                            self.index["structure"]["backend_root"] = str(
                                d.relative_to(self.root))
                        break
                if stack["backend"]:
                    break

        self.index["stack"] = {k: v for k, v in stack.items() if v}

    def _detect_structure(self):
        """Detect project directory structure."""
        structure = self.index["structure"]

        # Common source directories one level down (e.g. frontend/src)
        src_patterns = {"src", "app", "lib", "packages", "source"}
        for path in self._dirs:
            rel = path.relative_to(self.root)
            if len(rel.parts) != 2 or rel.parts[1] not in src_patterns:
                continue
            rel_path = str(rel)
            lower = rel_path.lower()
            if any(k in lower for k in ("frontend", "react", "web")):
                structure.setdefault("frontend_src", rel_path)
            elif any(k in lower for k in ("backend", "api", "server")):
                structure.setdefault("backend_src", rel_path)

        # Direct src folder
        if (self.root / "src").is_dir():
            structure["src"] = "src"

        # Look for src-prefixed backend roots (e.g., src-api, src-server)
        for path in sorted(self.root.glob("src-*")):
            if path.is_dir() and "backend_src" not in structure:
                structure["backend_src"] = path.name

        # Find controllers/services directories (shallowest first)
        def shallowest(name: str) -> Optional[Path]:
            matches = sorted(
                (p for p in self._dirs if p.name == name),
                key=lambda p: (len(p.parts), str(p)),
            )
            return matches[0] if matches else None

        controllers = shallowest("Controllers")
        if controllers:
            structure["controllers"] = str(controllers.relative_to(self.root))
        services = shallowest("Services")
        if services:
            structure["services"] = str(services.relative_to(self.root))

        self.index["structure"] = structure

    def _detect_features(self):
        """Detect feature/module names."""
        features = set()

        # Look for features/modules directories
        feature_dirs = {"features", "modules", "domains", "areas"}
        for path in self._dirs:
            if path.name not in feature_dirs:
                continue
            try:
                for child in path.iterdir():
                    if child.is_dir() and not child.name.startswith("."):
                        features.add(child.name)
            except OSError:
                continue

        # Look for controller names (FeatureController.cs)
        for path in self._files:
            if path.name.endswith("Controller.cs"):
                name = path.stem.replace("Controller", "")
                if name and len(name) > 2:
                    features.add(name)

        # Clean up feature names
        self.index["features"] = sorted(
            f for f in features if len(f) > 2 and f[0].isupper())[:50]

    def _detect_patterns(self):
        """Detect common file patterns in the project."""
        exts = {".tsx", ".ts", ".cs", ".py", ".go", ".java", ".vue", ".svelte"}
        pattern_counts = {}
        for path in self._files:
            if path.suffix not in exts:
                continue
            name = path.stem
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

        # Globs matching the conventions actually counted above
        pattern_globs = {
            "container": "*Container.*",
            "page": "*Page.*",
            "controller": "*Controller.*",
            "service": "*Service.*",
            "hook": "*.hook.*",
        }

        # Set patterns that appear frequently
        patterns = {}
        for pattern, count in pattern_counts.items():
            if count >= 3:
                patterns[pattern] = pattern_globs[pattern]

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
