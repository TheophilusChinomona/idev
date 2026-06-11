import time
import json
import os
from pathlib import Path
from ai_map_updater import create_project_map

UPDATE_INTERVAL = 60  # 1 minute
# State lives in the project, not the plugin install dir (run from project root)
STATE_DIR = Path.cwd() / ".claude" / "idev" / "project-map"
CONFIG_FILE = STATE_DIR / "watcher_config.json"
LEGACY_CONFIG_FILE = STATE_DIR / "config.json"


def load_config():
    """Load saved configuration if it exists."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    return None


def save_config(config):
    """Save the current configuration to both config files."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    legacy = {
        "frontend_path": config.get("frontend_path"),
        "backend_path": config.get("backend_path")
    }
    with open(LEGACY_CONFIG_FILE, 'w') as f:
        json.dump(legacy, f, indent=2)


def ask_project_config():
    """Interactively confirm or change project configuration at startup."""
    config = load_config()

    if config and config.get("project_type"):
        project_type = config["project_type"]
        print("\nCurrent configuration:")
        print(f"  Project type: {project_type}")

        if project_type == "unified":
            print(f"  Project path: {config.get('unified_path', '(none)')}")
        else:
            print(f"  Frontend: {config.get('frontend_path') or '(none)'}")
            print(f"  Backend:  {config.get('backend_path') or '(none)'}")

        response = input("\nUse this configuration? [Y/n]: ").strip().lower()
        if response == "" or response == "y" or response == "yes":
            return config

        print("\nReconfiguring...\n")

    else:
        print("Welcome to AI Map Watcher!")
        print("No saved configuration found.\n")

    # Ask for project type
    print("What type of project structure do you have?")
    print("  1. Split    - Separate FE + BE projects (e.g. React + .NET API)")
    print("  2. Unified  - Single project where UI + services coexist (e.g. Blazor Server, MVC)")
    print()

    while True:
        choice = input("Enter 1 or 2: ").strip()
        if choice in ("1", "2"):
            break
        print("Please enter 1 or 2.")

    config = {}

    if choice == "2":
        config["project_type"] = "unified"
        unified_path = input("Enter the project root path: ").strip()
        config["unified_path"] = unified_path if unified_path else None
        config["frontend_path"] = None
        config["backend_path"] = None
    else:
        config["project_type"] = "split"
        fe_path = input("Frontend root path (or leave blank if none): ").strip()
        be_path = input("Backend root path (or leave blank if none): ").strip()
        config["frontend_path"] = fe_path if fe_path else None
        config["backend_path"] = be_path if be_path else None
        config["unified_path"] = None

    save_config(config)
    print("Configuration saved.\n")

    return config


if __name__ == "__main__":
    print("AI Map Watcher Starting...")

    config = ask_project_config()

    # Always create/update the map at startup
    create_project_map(config=config)

    print(f"AI Map Watcher Running... updates every {UPDATE_INTERVAL} seconds.")

    while True:
        time.sleep(UPDATE_INTERVAL)
        print("Watcher tick: regenerating project map...")
        create_project_map(config=config)
