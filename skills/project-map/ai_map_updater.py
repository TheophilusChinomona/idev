import os
import re
import sys
from datetime import datetime

# -----------------------------
# FILTER RULES
# -----------------------------
IGNORE_DIRS = {
    'node_modules', 'dist', 'build', 'obj', 'bin', '.git', '.vs', '__pycache__',
    'Migrations', 'wwwroot'
}

IGNORE_FILE_PATTERNS = (
    '.dll', '.pdb', '.vsidx', '.wsuo',
    '.ttf', '.woff', '.png', '.jpg', '.svg', '.webp',
    '.css', '.lock', '.ico',
    'index.ts', '.test.tsx', '.Test.cs'
)

ALLOW_JSON_FILES = ('tsconfig.json', 'package.json', 'appsettings.json')

# Generic source extensions scanned in split mode (FE and BE trees)
GENERIC_SOURCE_EXTENSIONS = (
    '.ts', '.tsx', '.js', '.jsx', '.py', '.go', '.rb', '.java',
    '.cs', '.php', '.vue', '.svelte', '.json'
)

# Blazor/Razor file extensions (UI layer in a unified project)
UNIFIED_UI_EXTENSIONS = ('.razor', '.razor.cs', '.cshtml', '.cshtml.cs')

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def should_ignore_file(file_path):
    """Return True if the file should be ignored."""
    for d in IGNORE_DIRS:
        if d in file_path.split(os.sep):
            return True

    fname = os.path.basename(file_path)

    if fname in ALLOW_JSON_FILES:
        return False

    for pat in IGNORE_FILE_PATTERNS:
        if fname.endswith(pat) or fname == pat:
            return True

    return False


def scan_directory(root_path, allowed_extensions=None):
    """Scan a directory recursively and return included files."""
    files = []
    if not root_path or not os.path.exists(root_path):
        return files
    for dirpath, dirnames, filenames in os.walk(root_path):
        for f in filenames:
            full_path = os.path.join(dirpath, f)
            if should_ignore_file(full_path):
                continue
            if allowed_extensions:
                if not any(f.endswith(ext) for ext in allowed_extensions):
                    continue
            files.append(os.path.relpath(full_path, root_path))
    return files


def discover_referenced_projects(csproj_path):
    """
    Parse a .csproj file and return absolute paths to all referenced project directories.
    Follows ProjectReference elements recursively.
    """
    if not os.path.exists(csproj_path):
        return []

    referenced_dirs = []
    # Seed with the starting project's own dir so circular refs never re-add it
    added_dirs = {os.path.dirname(os.path.abspath(csproj_path))}
    visited = set()

    def _follow_refs(csproj):
        csproj = os.path.abspath(csproj)
        if csproj in visited:
            return
        visited.add(csproj)

        if not os.path.exists(csproj):
            return

        try:
            with open(csproj, 'r', encoding='utf-8-sig') as f:
                content = f.read()
        except Exception:
            return

        # Find all ProjectReference Include="relative\path\to\project.csproj"
        refs = re.findall(r'<ProjectReference\s+Include="([^"]+)"', content)
        parent_dir = os.path.dirname(os.path.abspath(csproj))

        for ref in refs:
            # Normalize path separators
            ref_normalized = ref.replace('\\', os.sep).replace('/', os.sep)
            ref_abs = os.path.normpath(os.path.join(parent_dir, ref_normalized))
            ref_dir = os.path.dirname(ref_abs)

            if os.path.isdir(ref_dir) and ref_dir not in added_dirs:
                added_dirs.add(ref_dir)
                referenced_dirs.append(ref_dir)
                # Recursively follow that project's references too
                _follow_refs(ref_abs)

    _follow_refs(csproj_path)
    return referenced_dirs


def find_csproj(directory):
    """Find the first .csproj file in a directory."""
    if not directory or not os.path.exists(directory):
        return None
    for f in os.listdir(directory):
        if f.endswith('.csproj'):
            return os.path.join(directory, f)
    return None


def categorize_files(file_list, label_prefix=""):
    """
    Categorize a list of relative file paths into layers.
    Returns dict with pages, services, domain, infrastructure, other.
    """
    categories = {
        'pages': [],
        'services': [],
        'domain': [],
        'infrastructure': [],
        'other': []
    }

    for f in file_list:
        parts = f.replace('\\', '/').split('/')

        if any(f.endswith(ext) for ext in UNIFIED_UI_EXTENSIONS):
            categories['pages'].append(label_prefix + f)
        elif any(p.lower() in ('services', 'interfaces', 'servicedtos') for p in parts):
            categories['services'].append(label_prefix + f)
        elif any(p.lower() in ('domain', 'entities', 'constants') for p in parts):
            categories['domain'].append(label_prefix + f)
        elif any(p.lower() in ('data', 'infrastructure', 'appcontext', 'repositories') for p in parts):
            categories['infrastructure'].append(label_prefix + f)
        else:
            categories['other'].append(label_prefix + f)

    return categories


def merge_categories(target, source):
    """Merge source categories into target."""
    for key in target:
        target[key].extend(source.get(key, []))


def categorize_unified_files(root_path):
    """
    For unified projects (Blazor Server, MVC), categorize files into layers.
    Automatically discovers and includes referenced sibling projects by
    parsing .csproj ProjectReference elements.
    """
    all_categories = {
        'pages': [],
        'services': [],
        'domain': [],
        'infrastructure': [],
        'other': []
    }

    # 1. Scan the main project directory
    main_files = scan_directory(root_path,
        allowed_extensions=UNIFIED_UI_EXTENSIONS + GENERIC_SOURCE_EXTENSIONS)
    main_cats = categorize_files(main_files)
    merge_categories(all_categories, main_cats)

    # 2. Discover referenced projects from .csproj
    csproj = find_csproj(root_path)
    if csproj:
        ref_dirs = discover_referenced_projects(csproj)
        for ref_dir in ref_dirs:
            # Create a short label from the project folder name
            project_name = os.path.basename(ref_dir)
            label = f"[{project_name}] "

            ref_files = scan_directory(ref_dir,
                allowed_extensions=('.cs', '.json'))
            ref_cats = categorize_files(ref_files, label_prefix=label)
            merge_categories(all_categories, ref_cats)

    return all_categories


def summarize_domain_entities(domain_path):
    """Return summary of domain entities instead of full list."""
    if not os.path.exists(domain_path):
        return "Domain path does not exist."
    count = 0
    for dirpath, _, filenames in os.walk(domain_path):
        for f in filenames:
            if f.endswith('.cs'):
                count += 1
    return f"Domain contains ~{count} entity classes."


def detect_project_type(config):
    """
    Detect project type from config.
    Returns: 'split', 'unified', or 'none'
    """
    project_type = config.get("project_type")
    if project_type:
        return project_type

    fe_path = config.get("frontend_path")
    be_path = config.get("backend_path")
    unified_path = config.get("unified_path")

    if unified_path:
        return "unified"
    if fe_path and be_path:
        return "split"
    if be_path and not fe_path:
        if be_path and os.path.exists(be_path):
            for dirpath, _, filenames in os.walk(be_path):
                for f in filenames:
                    if f.endswith('.razor'):
                        return "unified"
                break
        return "split"
    return "none"


def autodetect_split_dirs(root):
    """Look for conventional FE/BE subdirectories under root."""
    fe_names = ('frontend', 'client', 'web', 'ui')
    be_names = ('backend', 'server', 'api')
    fe = next((os.path.join(root, n) for n in fe_names
               if os.path.isdir(os.path.join(root, n))), None)
    be = next((os.path.join(root, n) for n in be_names
               if os.path.isdir(os.path.join(root, n))), None)
    return fe, be


def create_project_map(fe_path=None, be_path=None, unified_path=None,
                       project_type=None, output_path=None, config=None):
    """
    Scan project folders and create a clean project map.
    Supports three modes:
    - split: separate FE + BE paths (React + API)
    - unified: single path for Blazor Server / MVC / monolith
      (auto-discovers referenced sibling projects via .csproj)
    - auto-detect from config
    """
    if config:
        fe_path = fe_path or config.get("frontend_path")
        be_path = be_path or config.get("backend_path")
        unified_path = unified_path or config.get("unified_path")
        project_type = project_type or detect_project_type(config)

    if not config and not fe_path and not be_path and not unified_path:
        if not sys.stdin.isatty():
            # Non-interactive: never prompt — fall back to sane defaults.
            if project_type == "split":
                fe_path, be_path = autodetect_split_dirs(os.getcwd())
                if not fe_path and not be_path:
                    project_type = "unified"
                    unified_path = os.getcwd()
            else:
                project_type = project_type or "unified"
                unified_path = os.getcwd()
        else:
            print("Select project type:")
            print("  1. Split (separate FE + BE projects, e.g. React + .NET API)")
            print("  2. Unified (single project, e.g. Blazor Server, MVC)")
            choice = input("Enter 1 or 2: ").strip()

            if choice == "2":
                project_type = "unified"
                unified_path = input("Enter project root path: ").strip()
                if unified_path == "":
                    unified_path = None
            else:
                project_type = "split"
                fe_path = input("Enter Frontend root path (or leave blank if none): ").strip()
                if fe_path == "":
                    fe_path = None
                be_path = input("Enter Backend root path (or leave blank if none): ").strip()
                if be_path == "":
                    be_path = None

    if output_path is None:
        output_path = os.path.join('.claude', 'idev', 'project-map', 'project.map.md')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    map_lines = [
        "="*80,
        "PROJECT MAP",
        f"Generated: {now}",
        f"Project Type: {project_type or 'split'}",
        "="*80,
        ""
    ]

    # -----------------------------
    # Unified project (Blazor Server, MVC, etc.)
    # -----------------------------
    if project_type == "unified" and unified_path:
        # Show which projects were discovered
        csproj = find_csproj(unified_path)
        if csproj:
            ref_dirs = discover_referenced_projects(csproj)
            if ref_dirs:
                map_lines.append("REFERENCED PROJECTS:")
                map_lines.append(f"- {os.path.basename(unified_path)} (active project)")
                for rd in ref_dirs:
                    map_lines.append(f"- {os.path.basename(rd)}")
                map_lines.append("")

        categories = categorize_unified_files(unified_path)

        if categories['pages']:
            map_lines.append("PAGES / UI COMPONENTS:")
            for f in sorted(categories['pages']):
                map_lines.append(f"- {f}")
            map_lines.append("")

        if categories['services']:
            map_lines.append("SERVICES / INTERFACES:")
            # Summarize if too many
            if len(categories['services']) > 100:
                map_lines.append(f"~{len(categories['services'])} service/interface files")
            else:
                for f in sorted(categories['services']):
                    map_lines.append(f"- {f}")
            map_lines.append("")

        if categories['domain']:
            map_lines.append("DOMAIN / ENTITIES:")
            if len(categories['domain']) > 50:
                map_lines.append(f"~{len(categories['domain'])} domain files (entities, constants, etc.)")
            else:
                for f in sorted(categories['domain']):
                    map_lines.append(f"- {f}")
            map_lines.append("")

        if categories['infrastructure']:
            map_lines.append("INFRASTRUCTURE / DATA:")
            if len(categories['infrastructure']) > 50:
                map_lines.append(f"~{len(categories['infrastructure'])} infrastructure files")
            else:
                for f in sorted(categories['infrastructure']):
                    map_lines.append(f"- {f}")
            map_lines.append("")

        if categories['other']:
            map_lines.append("OTHER FILES:")
            for f in sorted(categories['other']):
                map_lines.append(f"- {f}")
            map_lines.append("")

    else:
        # -----------------------------
        # Split project: Frontend
        # -----------------------------
        if fe_path:
            map_lines.append("FRONTEND FILES:")
            fe_files = scan_directory(fe_path, allowed_extensions=GENERIC_SOURCE_EXTENSIONS)
            if fe_files:
                for f in fe_files:
                    map_lines.append(f"- {f}")
            else:
                map_lines.append("No frontend files found.")
            map_lines.append("")

        # -----------------------------
        # Split project: Backend
        # -----------------------------
        if be_path:
            map_lines.append("BACKEND FILES:")
            be_files = scan_directory(be_path, allowed_extensions=GENERIC_SOURCE_EXTENSIONS)
            if be_files:
                for f in be_files:
                    map_lines.append(f"- {f}")
            else:
                map_lines.append("No backend files found.")
            map_lines.append("")

            domain_path = os.path.join(be_path, 'Domain')
            map_lines.append("DOMAIN ENTITIES SUMMARY:")
            map_lines.append(summarize_domain_entities(domain_path))
            map_lines.append("")

    # Write to file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(map_lines))

    print(f"Project map created/updated at {output_path}.")


def _main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate a project map at .claude/idev/project-map/project.map.md")
    parser.add_argument("--root", default=os.getcwd(),
                        help="Project root (default: current directory)")
    parser.add_argument("--mode", choices=["single", "unified", "split"], default=None,
                        help="Map mode ('single'/'unified' = one tree; default: auto-detect)")
    parser.add_argument("--frontend", default=None,
                        help="Frontend root (split mode)")
    parser.add_argument("--backend", default=None,
                        help="Backend root (split mode)")
    parser.add_argument("--output", default=None,
                        help="Output path (default: <root>/.claude/idev/project-map/project.map.md)")
    args = parser.parse_args()

    root = os.path.abspath(args.root)
    mode = "unified" if args.mode == "single" else args.mode
    fe, be = args.frontend, args.backend

    if mode is None:
        if fe or be:
            mode = "split"
        else:
            fe, be = autodetect_split_dirs(root)
            mode = "split" if (fe and be) else "unified"
    elif mode == "split" and not fe and not be:
        fe, be = autodetect_split_dirs(root)
        if not fe and not be:
            print("No frontend/backend dirs found; falling back to unified scan of root.")
            mode = "unified"

    output = args.output or os.path.join(root, ".claude", "idev", "project-map",
                                         "project.map.md")
    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)

    if mode == "unified":
        create_project_map(unified_path=root, project_type="unified", output_path=output)
    else:
        create_project_map(fe_path=fe, be_path=be, project_type="split", output_path=output)


if __name__ == "__main__":
    _main()
