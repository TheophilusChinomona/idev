"""Preflight checks for the codebase-explainer skill.

Verifies the `notebooklm` CLI is installed and authenticated. Never imports
notebooklm-py; uses PATH lookup + a cheap CLI call. All externals injectable.
"""

import argparse
import json
import shutil
import subprocess
import sys

NB_BIN = "notebooklm"
AUTH_CHECK_ARGS = ["notebooks", "list"]
INSTALL_HINT = 'install it with:  pip install "notebooklm-py[browser]"  (then: notebooklm login)'
LOGIN_HINT = "not authenticated — run:  notebooklm login"


def cli_available(which=shutil.which):
    return which(NB_BIN) is not None


def auth_ready(run=subprocess.run):
    try:
        result = run([NB_BIN, *AUTH_CHECK_ARGS], capture_output=True, text=True)
    except FileNotFoundError:
        return False
    return result.returncode == 0


def preflight(which=shutil.which, run=subprocess.run):
    messages = []
    cli = cli_available(which=which)
    if not cli:
        messages.append(f"notebooklm CLI not found — {INSTALL_HINT}")
        return {"cli": False, "auth": False, "ready": False, "messages": messages}
    auth = auth_ready(run=run)
    if not auth:
        messages.append(LOGIN_HINT)
    return {"cli": True, "auth": auth, "ready": auth, "messages": messages}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Codebase-explainer preflight.")
    parser.parse_args(argv)
    status = preflight()
    print(json.dumps(status, indent=2))
    return 0 if status["ready"] else 1


if __name__ == "__main__":
    sys.exit(main())
