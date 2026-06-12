#!/usr/bin/env python3
"""
Instinct CLI - Manage instincts for Continuous Learning v2

Commands:
  status   - Show all instincts and their status
  import   - Import instincts from file or URL
  export   - Export instincts to file
  evolve   - Cluster instincts and print candidates for skills/commands/agents
"""

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────

HOMUNCULUS_DIR = Path.home() / ".claude" / "homunculus"
INSTINCTS_DIR = HOMUNCULUS_DIR / "instincts"
PERSONAL_DIR = INSTINCTS_DIR / "personal"
INHERITED_DIR = INSTINCTS_DIR / "inherited"
EVOLVED_DIR = HOMUNCULUS_DIR / "evolved"
OBSERVATIONS_FILE = HOMUNCULUS_DIR / "observations.jsonl"


def ensure_dirs():
    """Create the homunculus directory tree (called from main, not at import)."""
    for d in [PERSONAL_DIR, INHERITED_DIR, EVOLVED_DIR / "skills",
              EVOLVED_DIR / "commands", EVOLVED_DIR / "agents"]:
        d.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────
# Sanitization
# ─────────────────────────────────────────────

# Same secret-pattern redaction as hooks/observe.py
SECRET_RE = re.compile(
    r"(api[_-]?key|token|secret|password|authorization)(\s*[=:]\s*)\S+",
    re.IGNORECASE,
)
# Absolute filesystem paths (POSIX home dirs and Windows user dirs)
PATH_RE = re.compile(
    r"(?:/(?:home|Users)/[^\s\"'`]+|[A-Za-z]:\\Users\\[^\s\"'`]+)"
)


def sanitize(text: str) -> str:
    """Redact secrets and absolute filesystem paths from exported text."""
    text = SECRET_RE.sub(r"\1\2[REDACTED]", text)
    text = PATH_RE.sub("<path>", text)
    return text


# ─────────────────────────────────────────────
# Instinct Parser / Serializer
# ─────────────────────────────────────────────

def parse_instinct_file(content: str) -> list:
    """Parse instinct files.

    An instinct is a YAML frontmatter block (lines between two `---` lines)
    followed by a markdown body that runs until the next frontmatter block
    or EOF. The body attaches to the preceding frontmatter as `content`.
    """
    instincts = []
    lines = content.split('\n')
    n = len(lines)
    current = None
    body_lines = []

    def flush():
        nonlocal current, body_lines
        if current is not None:
            current['content'] = '\n'.join(body_lines).strip()
            instincts.append(current)
        current = None
        body_lines = []

    i = 0
    while i < n:
        line = lines[i]
        if line.strip() == '---':
            # Scan ahead for the closing '---' of a frontmatter block
            j = i + 1
            frontmatter = {}
            closed = False
            while j < n:
                if lines[j].strip() == '---':
                    closed = True
                    break
                if ':' in lines[j]:
                    key, value = lines[j].split(':', 1)
                    key = key.strip()
                    raw = value.strip()
                    # JSON-quoted scalars (as written by export) parse cleanly;
                    # otherwise fall back to stripping plain quotes.
                    try:
                        parsed_value = json.loads(raw)
                    except (ValueError, TypeError):
                        parsed_value = raw.strip('"').strip("'")
                    if key == 'confidence':
                        try:
                            parsed_value = float(parsed_value)
                        except (TypeError, ValueError):
                            pass
                    frontmatter[key] = parsed_value
                j += 1
            if closed:
                # Finish the previous instinct, start a new one
                flush()
                current = frontmatter
                i = j + 1
                continue
            # Unclosed '---': treat as a plain body line
        if current is not None:
            body_lines.append(line)
        i += 1

    flush()
    return [inst for inst in instincts if inst.get('id')]


FRONTMATTER_KEYS = ['id', 'trigger', 'confidence', 'domain', 'source',
                    'source_repo', 'imported_from']


def serialize_instinct(inst: dict) -> str:
    """Serialize one instinct to frontmatter + body.

    String values are emitted with json.dumps, which produces valid
    (escaped, quoted) YAML scalars — quotes in triggers can't corrupt output.
    """
    out = "---\n"
    for key in FRONTMATTER_KEYS:
        value = inst.get(key)
        if value is None or value == '':
            continue
        if isinstance(value, bool):
            out += f"{key}: {'true' if value else 'false'}\n"
        elif isinstance(value, (int, float)):
            out += f"{key}: {value}\n"
        else:
            out += f"{key}: {json.dumps(str(value))}\n"
    out += "---\n\n"
    body = inst.get('content', '')
    if body:
        out += body + "\n"
    out += "\n"
    return out


def load_all_instincts() -> list:
    """Load all instincts from personal and inherited directories."""
    instincts = []

    for directory in [PERSONAL_DIR, INHERITED_DIR]:
        if not directory.exists():
            continue
        for pattern in ("*.yaml", "*.md"):
            for file in sorted(directory.glob(pattern)):
                try:
                    content = file.read_text()
                    parsed = parse_instinct_file(content)
                    for inst in parsed:
                        inst['_source_file'] = str(file)
                        inst['_source_type'] = directory.name
                    instincts.extend(parsed)
                except Exception as e:
                    print(f"Warning: Failed to parse {file}: {e}", file=sys.stderr)

    return instincts


# ─────────────────────────────────────────────
# Status Command
# ─────────────────────────────────────────────

def cmd_status(args):
    """Show status of all instincts."""
    instincts = load_all_instincts()

    if not instincts:
        print("No instincts found.")
        print(f"\nInstinct directories:")
        print(f"  Personal:  {PERSONAL_DIR}")
        print(f"  Inherited: {INHERITED_DIR}")
        return

    # Group by domain
    by_domain = defaultdict(list)
    for inst in instincts:
        domain = inst.get('domain', 'general')
        by_domain[domain].append(inst)

    # Print header
    print(f"\n{'='*60}")
    print(f"  INSTINCT STATUS - {len(instincts)} total")
    print(f"{'='*60}\n")

    # Summary by source
    personal = [i for i in instincts if i.get('_source_type') == 'personal']
    inherited = [i for i in instincts if i.get('_source_type') == 'inherited']
    print(f"  Personal:  {len(personal)}")
    print(f"  Inherited: {len(inherited)}")
    print()

    # Print by domain
    for domain in sorted(by_domain.keys()):
        domain_instincts = by_domain[domain]
        print(f"## {str(domain).upper()} ({len(domain_instincts)})")
        print()

        for inst in sorted(domain_instincts, key=lambda x: -x.get('confidence', 0.5)):
            conf = inst.get('confidence', 0.5)
            conf_bar = '#' * int(conf * 10) + '-' * (10 - int(conf * 10))
            trigger = inst.get('trigger', 'unknown trigger')

            print(f"  {conf_bar} {int(conf*100):3d}%  {inst.get('id', 'unnamed')}")
            print(f"            trigger: {trigger}")

            # Extract action from content
            content = inst.get('content', '')
            action_match = re.search(r'## Action\s*\n\s*(.+?)(?:\n\n|\n##|$)', content, re.DOTALL)
            if action_match:
                action = action_match.group(1).strip().split('\n')[0]
                print(f"            action: {action[:60]}{'...' if len(action) > 60 else ''}")

            print()

    # Observations stats
    if OBSERVATIONS_FILE.exists():
        obs_count = sum(1 for _ in open(OBSERVATIONS_FILE))
        print(f"-" * 57)
        print(f"  Observations: {obs_count} events logged")
        print(f"  File: {OBSERVATIONS_FILE}")

    print(f"\n{'='*60}\n")


# ─────────────────────────────────────────────
# Import Command
# ─────────────────────────────────────────────

def update_instinct_in_place(existing_inst: dict, new_inst: dict) -> None:
    """Update an existing instinct's file in place (no duplicate files)."""
    target = Path(existing_inst['_source_file'])
    file_instincts = parse_instinct_file(target.read_text())
    out = ""
    for fi in file_instincts:
        if fi.get('id') == new_inst.get('id'):
            merged = dict(fi)
            merged.update({k: v for k, v in new_inst.items()
                           if not k.startswith('_')})
            out += serialize_instinct(merged)
        else:
            out += serialize_instinct(fi)
    target.write_text(out)


def cmd_import(args):
    """Import instincts from file or URL."""
    source = args.source

    # Fetch content
    if source.startswith('http://') or source.startswith('https://'):
        print(f"Fetching from URL: {source}")
        try:
            with urllib.request.urlopen(source) as response:
                content = response.read().decode('utf-8')
        except Exception as e:
            print(f"Error fetching URL: {e}", file=sys.stderr)
            return 1
    else:
        path = Path(source).expanduser()
        if not path.exists():
            print(f"File not found: {path}", file=sys.stderr)
            return 1
        content = path.read_text()

    # Parse instincts
    new_instincts = parse_instinct_file(content)
    if not new_instincts:
        print("No valid instincts found in source.")
        return 1

    print(f"\nFound {len(new_instincts)} instincts to import.\n")

    # Load existing
    existing = load_all_instincts()
    existing_ids = {i.get('id') for i in existing}

    # Categorize
    to_add = []
    duplicates = []
    to_update = []

    for inst in new_instincts:
        inst_id = inst.get('id')
        if inst_id in existing_ids:
            # Check if we should update
            existing_inst = next((e for e in existing if e.get('id') == inst_id), None)
            if existing_inst:
                if inst.get('confidence', 0) > existing_inst.get('confidence', 0):
                    to_update.append((existing_inst, inst))
                else:
                    duplicates.append(inst)
        else:
            to_add.append(inst)

    # Filter by minimum confidence
    min_conf = args.min_confidence or 0.0
    to_add = [i for i in to_add if i.get('confidence', 0.5) >= min_conf]
    to_update = [(e, i) for e, i in to_update if i.get('confidence', 0.5) >= min_conf]

    # Display summary
    if to_add:
        print(f"NEW ({len(to_add)}):")
        for inst in to_add:
            print(f"  + {inst.get('id')} (confidence: {inst.get('confidence', 0.5):.2f})")

    if to_update:
        print(f"\nUPDATE ({len(to_update)}):")
        for _, inst in to_update:
            print(f"  ~ {inst.get('id')} (confidence: {inst.get('confidence', 0.5):.2f})")

    if duplicates:
        print(f"\nSKIP ({len(duplicates)} - already exists with equal/higher confidence):")
        for inst in duplicates[:5]:
            print(f"  - {inst.get('id')}")
        if len(duplicates) > 5:
            print(f"  ... and {len(duplicates) - 5} more")

    if args.dry_run:
        print("\n[DRY RUN] No changes made.")
        return 0

    if not to_add and not to_update:
        print("\nNothing to import.")
        return 0

    # Confirm. Never call input() without a TTY (would crash with EOFError
    # under non-interactive stdin); proceed as confirmed instead.
    if not args.force:
        if sys.stdin.isatty():
            response = input(f"\nImport {len(to_add)} new, update {len(to_update)}? [y/N] ")
            if response.lower() != 'y':
                print("Cancelled.")
                return 0
        else:
            print(f"\nNon-interactive session: importing {len(to_add)} new, "
                  f"updating {len(to_update)} without prompt.")

    # Updates: rewrite the existing instinct's file in place so the old and
    # new versions don't both keep loading.
    for existing_inst, inst in to_update:
        update_instinct_in_place(existing_inst, inst)

    # New instincts: write to the inherited directory
    output_file = None
    if to_add:
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        source_name = Path(source).stem if not source.startswith('http') else 'web-import'
        output_file = INHERITED_DIR / f"{source_name}-{timestamp}.yaml"

        output_content = f"# Imported from {source}\n# Date: {datetime.now().isoformat()}\n\n"
        for inst in to_add:
            record = {k: v for k, v in inst.items() if not k.startswith('_')}
            record.setdefault('trigger', 'unknown')
            record.setdefault('confidence', 0.5)
            record.setdefault('domain', 'general')
            record['source'] = 'inherited'
            record['imported_from'] = source
            output_content += serialize_instinct(record)

        output_file.write_text(output_content)

    print(f"\nImport complete.")
    print(f"   Added: {len(to_add)}")
    print(f"   Updated (in place): {len(to_update)}")
    if output_file:
        print(f"   New instincts saved to: {output_file}")

    return 0


# ─────────────────────────────────────────────
# Export Command
# ─────────────────────────────────────────────

def cmd_export(args):
    """Export instincts to file."""
    instincts = load_all_instincts()

    if not instincts:
        print("No instincts to export.")
        return 1

    # Filter by domain if specified
    if args.domain:
        instincts = [i for i in instincts if i.get('domain') == args.domain]

    # Filter by minimum confidence
    if args.min_confidence:
        instincts = [i for i in instincts if i.get('confidence', 0.5) >= args.min_confidence]

    if not instincts:
        print("No instincts match the criteria.")
        return 1

    # Generate output. Sanitize string fields and bodies: redact absolute
    # filesystem paths and secret-looking values before sharing.
    output = f"# Instincts export\n# Date: {datetime.now().isoformat()}\n# Total: {len(instincts)}\n\n"

    for inst in instincts:
        record = {}
        for key in FRONTMATTER_KEYS:
            value = inst.get(key)
            if value is None or value == '':
                continue
            record[key] = sanitize(str(value)) if isinstance(value, str) else value
        record['content'] = sanitize(inst.get('content', ''))
        output += serialize_instinct(record)

    # Write to file or stdout
    if args.output:
        Path(args.output).write_text(output)
        print(f"Exported {len(instincts)} instincts to {args.output}")
    else:
        print(output)

    return 0


# ─────────────────────────────────────────────
# Evolve Command
# ─────────────────────────────────────────────

def cmd_evolve(args):
    """Analyze instincts and suggest evolutions to skills/commands/agents."""
    instincts = load_all_instincts()

    if len(instincts) < 3:
        print("Need at least 3 instincts to analyze patterns.")
        print(f"Currently have: {len(instincts)}")
        return 1

    print(f"\n{'='*60}")
    print(f"  EVOLVE ANALYSIS - {len(instincts)} instincts")
    print(f"{'='*60}\n")

    # High-confidence instincts (candidates for skills)
    high_conf = [i for i in instincts if i.get('confidence', 0) >= 0.8]
    print(f"High confidence instincts (>=80%): {len(high_conf)}")

    # Find clusters (instincts with similar triggers)
    trigger_clusters = defaultdict(list)
    for inst in instincts:
        trigger = inst.get('trigger', '')
        # Normalize trigger
        trigger_key = str(trigger).lower()
        for keyword in ['when', 'creating', 'writing', 'adding', 'implementing', 'testing']:
            trigger_key = trigger_key.replace(keyword, '').strip()
        # Guard: an empty normalized trigger would cluster unrelated
        # instincts together — skip those.
        if not trigger_key:
            continue
        trigger_clusters[trigger_key].append(inst)

    # Find clusters with 3+ instincts (good skill candidates)
    skill_candidates = []
    for trigger, cluster in trigger_clusters.items():
        if len(cluster) >= 3:
            avg_conf = sum(i.get('confidence', 0.5) for i in cluster) / len(cluster)
            skill_candidates.append({
                'trigger': trigger,
                'instincts': cluster,
                'avg_confidence': avg_conf,
                'domains': list(set(i.get('domain', 'general') for i in cluster))
            })

    # Sort by cluster size and confidence
    skill_candidates.sort(key=lambda x: (-len(x['instincts']), -x['avg_confidence']))

    print(f"\nPotential skill clusters found: {len(skill_candidates)}")

    if skill_candidates:
        print(f"\n## SKILL CANDIDATES\n")
        for i, cand in enumerate(skill_candidates[:5], 1):
            print(f"{i}. Cluster: \"{cand['trigger']}\"")
            print(f"   Instincts: {len(cand['instincts'])}")
            print(f"   Avg confidence: {cand['avg_confidence']:.0%}")
            print(f"   Domains: {', '.join(cand['domains'])}")
            print(f"   Instincts:")
            for inst in cand['instincts'][:3]:
                print(f"     - {inst.get('id')}")
            print()

    # Command candidates (workflow instincts with high confidence)
    workflow_instincts = [i for i in instincts if i.get('domain') == 'workflow' and i.get('confidence', 0) >= 0.7]
    if workflow_instincts:
        print(f"\n## COMMAND CANDIDATES ({len(workflow_instincts)})\n")
        for inst in workflow_instincts[:5]:
            trigger = str(inst.get('trigger', 'unknown'))
            # Suggest command name
            cmd_name = trigger.replace('when ', '').replace('implementing ', '').replace('a ', '')
            cmd_name = cmd_name.replace(' ', '-')[:20]
            print(f"  /{cmd_name}")
            print(f"    From: {inst.get('id')}")
            print(f"    Confidence: {inst.get('confidence', 0.5):.0%}")
            print()

    # Agent candidates (complex multi-step patterns)
    agent_candidates = [c for c in skill_candidates if len(c['instincts']) >= 3 and c['avg_confidence'] >= 0.75]
    if agent_candidates:
        print(f"\n## AGENT CANDIDATES ({len(agent_candidates)})\n")
        for cand in agent_candidates[:3]:
            agent_name = cand['trigger'].replace(' ', '-')[:20] + '-agent'
            print(f"  {agent_name}")
            print(f"    Covers {len(cand['instincts'])} instincts")
            print(f"    Avg confidence: {cand['avg_confidence']:.0%}")
            print()

    if args.generate:
        # Generation is not implemented in this CLI. Claude reads the cluster
        # output above and writes the evolved files itself.
        print("\n[--generate] This CLI does not write evolved files itself.")
        print("  Review the clusters above and create the files under:")
        print("    Skills:  ", EVOLVED_DIR / "skills")
        print("    Commands:", EVOLVED_DIR / "commands")
        print("    Agents:  ", EVOLVED_DIR / "agents")

    print(f"\n{'='*60}\n")
    return 0


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Instinct CLI for Continuous Learning v2')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Status
    subparsers.add_parser('status', help='Show instinct status')

    # Import
    import_parser = subparsers.add_parser('import', help='Import instincts')
    import_parser.add_argument('source', help='File path or URL')
    import_parser.add_argument('--dry-run', action='store_true', help='Preview without importing')
    import_parser.add_argument('--force', action='store_true', help='Skip confirmation')
    import_parser.add_argument('--min-confidence', type=float, help='Minimum confidence threshold')

    # Export
    export_parser = subparsers.add_parser('export', help='Export instincts')
    export_parser.add_argument('--output', '-o', help='Output file')
    export_parser.add_argument('--domain', help='Filter by domain')
    export_parser.add_argument('--min-confidence', type=float, help='Minimum confidence')

    # Evolve
    evolve_parser = subparsers.add_parser('evolve', help='Analyze and evolve instincts')
    evolve_parser.add_argument('--generate', action='store_true',
                               help='Print where evolved files should be created (generation itself is done by Claude)')

    args = parser.parse_args()

    ensure_dirs()

    if args.command == 'status':
        return cmd_status(args)
    elif args.command == 'import':
        return cmd_import(args)
    elif args.command == 'export':
        return cmd_export(args)
    elif args.command == 'evolve':
        return cmd_evolve(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main() or 0)
