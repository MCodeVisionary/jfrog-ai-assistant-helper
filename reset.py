#!/usr/bin/env python3
"""
JFrog MCP Gateway — Reset Tool
--------------------------------
Wipes everything the setup script created so you can test from a clean slate.

Usage:
    python3 reset.py          — interactive menu
    python3 reset.py --all    — wipe everything without prompting
    python3 reset.py --dry    — show what would be removed, don't touch anything
"""

import os
import sys
import json
import shutil
import platform
import subprocess
import argparse

# ─────────────────────────────────────────────────────────────────────────────
#  OS flags
# ─────────────────────────────────────────────────────────────────────────────
_OS        = platform.system()
IS_MAC     = _OS == "Darwin"
IS_WINDOWS = _OS == "Windows"
IS_LINUX   = _OS == "Linux"

# ─────────────────────────────────────────────────────────────────────────────
#  Colours
# ─────────────────────────────────────────────────────────────────────────────
if IS_WINDOWS:
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleMode(
            ctypes.windll.kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass

GREEN  = "\033[92m"; YELLOW = "\033[93m"; CYAN   = "\033[96m"
RED    = "\033[91m"; BOLD   = "\033[1m";  DIM    = "\033[2m"; RESET = "\033[0m"

def ok(t):    print(f"{GREEN}  ✅  {t}{RESET}")
def skip(t):  print(f"{DIM}  ──  {t}{RESET}")
def warn(t):  print(f"{YELLOW}  ⚠️   {t}{RESET}")
def info(t):  print(f"{CYAN}  ℹ️   {t}{RESET}")
def err(t):   print(f"{RED}  ❌  {t}{RESET}")
def head(t):  print(f"\n{BOLD}{CYAN}  {t}{RESET}")
def rule():   print(f"  {DIM}{'─'*52}{RESET}")

DRY = False   # set by --dry flag

# ─────────────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────────────
def run(cmd, capture=True):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=capture,
                           text=True, timeout=30)
        return r.returncode == 0, (r.stdout or "").strip()
    except Exception as e:
        return False, str(e)

def exists_cmd(cmd):
    return shutil.which(cmd) is not None

def remove_file(path, label=None):
    label = label or path
    if os.path.isfile(path):
        if DRY:
            warn(f"[dry] would delete file:   {label}")
        else:
            try:
                os.remove(path)
                ok(f"Deleted:  {label}")
            except Exception as e:
                err(f"Could not delete {label}: {e}")
    else:
        skip(f"Not found:  {label}")

def remove_dir(path, label=None):
    label = label or path
    if os.path.isdir(path):
        if DRY:
            warn(f"[dry] would delete folder: {label}")
        else:
            try:
                shutil.rmtree(path)
                ok(f"Deleted:  {label}")
            except Exception as e:
                err(f"Could not delete {label}: {e}")
    else:
        skip(f"Not found:  {label}")

def _shell_profile():
    shell = os.environ.get("SHELL", "")
    if "zsh"  in shell: return os.path.expanduser("~/.zshrc")
    if "fish" in shell: return os.path.expanduser("~/.config/fish/config.fish")
    return os.path.expanduser("~/.bashrc")

# ─────────────────────────────────────────────────────────────────────────────
#  Reset tasks — each returns True if anything was actually changed
# ─────────────────────────────────────────────────────────────────────────────

ENV_VAR_NAMES = [
    "JFROG_URL",
    "JFROG_PLATFORM_URL",
    "JFROG_ACCESS_TOKEN",
    "JF_PROJECT",
    "JFROG_NPM_REGISTRY",
    "JFROG_AGENT_GUARD_REPO",
]

def reset_env_vars():
    """Remove JFrog env vars from shell profile and current process."""
    head("Environment Variables")
    changed = False

    # Remove from current process
    for name in ENV_VAR_NAMES:
        if name in os.environ:
            if not DRY:
                del os.environ[name]
            ok(f"Cleared from session:  {name}")
            changed = True
        else:
            skip(f"Not in session:  {name}")

    # Remove from shell profile
    if not IS_WINDOWS:
        profile = _shell_profile()
        if os.path.exists(profile):
            lines = open(profile).readlines()
            new_lines = [l for l in lines
                         if not any(l.strip().startswith(f"export {n}=")
                                    for n in ENV_VAR_NAMES)]
            removed = len(lines) - len(new_lines)
            if removed:
                if DRY:
                    warn(f"[dry] would remove {removed} line(s) from {profile}")
                else:
                    open(profile, "w").writelines(new_lines)
                    ok(f"Removed {removed} line(s) from {profile}")
                changed = True
            else:
                skip(f"No JFrog lines found in {profile}")
        else:
            skip(f"Profile not found: {profile}")
    else:
        # Windows: remove from registry via REG DELETE
        for name in ENV_VAR_NAMES:
            ok_r, _ = run(f'REG QUERY HKCU\\Environment /v {name}')
            if ok_r:
                if DRY:
                    warn(f"[dry] would delete registry key: {name}")
                else:
                    run(f'REG DELETE HKCU\\Environment /v {name} /f')
                    ok(f"Removed registry key: {name}")
                changed = True
            else:
                skip(f"Registry key not set: {name}")

    return changed


def reset_session_files():
    """Delete the sourceable session files."""
    head("Session Files")
    remove_file(os.path.expanduser("~/.jfrog-mcp-session.sh"),
                "~/.jfrog-mcp-session.sh")
    remove_file(os.path.expanduser("~/.jfrog-mcp-session.ps1"),
                "~/.jfrog-mcp-session.ps1")


def reset_jfrog_cli():
    """Remove the jfrog-mcp server from JFrog CLI config."""
    head("JFrog CLI Config  (server ID: jfrog-mcp)")
    if not exists_cmd("jf"):
        skip("jf CLI not installed — nothing to remove")
        return

    ok_r, out = run("jf config show jfrog-mcp")
    if not ok_r or "jfrog-mcp" not in out:
        skip("Server 'jfrog-mcp' not configured")
        return

    if DRY:
        warn("[dry] would run: jf config remove jfrog-mcp")
        return

    ok_r, _ = run("jf config remove jfrog-mcp --quiet")
    if ok_r:
        ok("Removed server 'jfrog-mcp' from JFrog CLI")
    else:
        err("Could not remove — try manually:  jf config remove jfrog-mcp")


def reset_npmrc():
    """Remove JFrog-related lines from ~/.npmrc."""
    head("~/.npmrc")
    npmrc = os.path.expanduser("~/.npmrc")
    if not os.path.exists(npmrc):
        skip("~/.npmrc not found")
        return

    lines = open(npmrc).readlines()
    jfrog_keywords = ["jfrog-mcp-npm", "jfrog.io", "_authToken", "always-auth"]
    new_lines = [l for l in lines
                 if not any(kw in l for kw in jfrog_keywords)]
    removed = len(lines) - len(new_lines)

    if not removed:
        skip("No JFrog entries found in ~/.npmrc")
        return

    if DRY:
        warn(f"[dry] would remove {removed} line(s) from ~/.npmrc")
        for l in lines:
            if any(kw in l for kw in jfrog_keywords):
                warn(f"  would remove:  {l.rstrip()}")
        return

    if new_lines:
        open(npmrc, "w").writelines(new_lines)
        ok(f"Removed {removed} JFrog line(s) from ~/.npmrc")
    else:
        os.remove(npmrc)
        ok("Deleted ~/.npmrc (was entirely JFrog config)")


def reset_venv():
    """Delete the .venv folder in the current directory."""
    head(".venv  (virtual environment)")
    venv = os.path.join(os.getcwd(), ".venv")
    remove_dir(venv, f".venv/  ({venv})")


def reset_cursor():
    """Remove Cursor rule file and JFrog entries from mcp.json."""
    head("Cursor Config")

    # Rule file — global
    remove_file(
        os.path.expanduser("~/.cursor/rules/jfrog-mcp-management.md"),
        "~/.cursor/rules/jfrog-mcp-management.md")

    # Rule file — local project
    local_rule = os.path.join(os.getcwd(), ".cursor", "rules", "jfrog-mcp-management.md")
    remove_file(local_rule, f".cursor/rules/jfrog-mcp-management.md  (project)")

    # mcp.json — global: remove JFrog entries, keep the rest
    for label, path in [
        ("~/.cursor/mcp.json", os.path.expanduser("~/.cursor/mcp.json")),
        (".cursor/mcp.json (project)", os.path.join(os.getcwd(), ".cursor", "mcp.json")),
    ]:
        _strip_jfrog_from_mcp_json(path, label)


def reset_claude_code():
    """Uninstall the JFrog plugin and remove entries from Claude config."""
    head("Claude Code")

    # Uninstall plugin
    if exists_cmd("claude"):
        ok_r, out = run("claude plugin list")
        if "jfrog" in out.lower():
            if DRY:
                warn("[dry] would run: claude plugin uninstall jfrog")
            else:
                ok_r, _ = run("claude plugin uninstall jfrog")
                if ok_r:
                    ok("Uninstalled JFrog plugin from Claude Code")
                else:
                    warn("Could not uninstall plugin — try manually:  claude plugin uninstall jfrog")
        else:
            skip("JFrog plugin not installed in Claude Code")
    else:
        skip("claude CLI not found")

    # Claude desktop config
    claude_cfg = os.path.expanduser("~/.claude/claude_desktop_config.json")
    _strip_jfrog_from_mcp_json(claude_cfg, "~/.claude/claude_desktop_config.json")


def reset_vscode():
    """Remove the VS Code reference file written by setup."""
    head("VS Code + Copilot")
    remove_file(os.path.expanduser("~/.jfrog-mcp-vscode.json"),
                "~/.jfrog-mcp-vscode.json")
    info("The VS Code plugin itself must be removed manually inside VS Code:")
    info("  Extensions panel (Ctrl/Cmd+Shift+X)  →  search JFrog  →  Uninstall")


def reset_npm_remote_repo(url=None, token=None):
    """
    Delete the jfrog-mcp-npm remote repo from the JFrog instance.
    Requires credentials — reads from env if not passed.
    """
    head("JFrog NPM Remote Repository  (jfrog-mcp-npm)")

    url   = url   or os.environ.get("JFROG_URL") or os.environ.get("JFROG_PLATFORM_URL", "")
    token = token or os.environ.get("JFROG_ACCESS_TOKEN", "")

    if not url or not token:
        warn("Cannot delete repo — JFROG_URL and JFROG_ACCESS_TOKEN not set.")
        info("Pass them on the command line:  python3 reset.py --repo-url URL --repo-token TOKEN")
        return

    import ssl, urllib.request, urllib.error
    repo_key = "jfrog-mcp-npm"
    api_url  = f"{url.rstrip('/')}/artifactory/api/repositories/{repo_key}"

    # Check if it exists
    req = urllib.request.Request(api_url, method="GET")
    req.add_header("Authorization", f"Bearer {token}")
    ctx = ssl.create_default_context()
    try:
        urllib.request.urlopen(req, context=ctx, timeout=10)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            skip(f"Repo '{repo_key}' does not exist on {url}")
            return
        err(f"Could not check repo: {e}")
        return
    except Exception as e:
        err(f"Could not reach JFrog: {e}")
        return

    # Delete it
    if DRY:
        warn(f"[dry] would DELETE {api_url}")
        return

    req_del = urllib.request.Request(api_url, method="DELETE")
    req_del.add_header("Authorization", f"Bearer {token}")
    try:
        urllib.request.urlopen(req_del, context=ctx, timeout=10)
        ok(f"Deleted repository '{repo_key}' from {url}")
    except urllib.error.HTTPError as e:
        err(f"Delete failed ({e.code}): {e.read().decode()[:200]}")
    except Exception as e:
        err(f"Delete failed: {e}")


def _strip_jfrog_from_mcp_json(path, label):
    """Remove JFrog-related mcpServer entries from a JSON config file."""
    if not os.path.exists(path):
        skip(f"Not found:  {label}")
        return

    try:
        data = json.load(open(path))
    except Exception:
        warn(f"Could not parse JSON in {label} — skipping")
        return

    servers = data.get("mcpServers", {})
    if not servers:
        skip(f"No mcpServers in {label}")
        return

    # Remove any key that has jfrog fingerprints
    def _is_jfrog(key, val):
        if "jfrog" in key.lower():
            return True
        args = val.get("args", [])
        env  = val.get("env", {})
        return (any("jfrog" in str(a).lower() or "mcp-gateway" in str(a) for a in args)
                or "_JF_MCP_LOADER_ARGS" in env
                or "jfrog" in str(env).lower())

    to_remove = [k for k, v in servers.items() if _is_jfrog(k, v)]
    if not to_remove:
        skip(f"No JFrog entries found in {label}")
        return

    if DRY:
        warn(f"[dry] would remove {len(to_remove)} entry/entries from {label}:")
        for k in to_remove:
            warn(f"  {k}")
        return

    for k in to_remove:
        del servers[k]

    if servers:
        data["mcpServers"] = servers
        json.dump(data, open(path, "w"), indent=2)
        ok(f"Removed {len(to_remove)} JFrog entry/entries from {label}")
    else:
        # File only had JFrog stuff — remove the whole file
        os.remove(path)
        ok(f"Deleted {label}  (contained only JFrog entries)")

# ─────────────────────────────────────────────────────────────────────────────
#  Menu
# ─────────────────────────────────────────────────────────────────────────────
TASKS = [
    ("env",      "Environment variables  (JFROG_URL, token, project …)",  reset_env_vars),
    ("session",  "Session files          (~/.jfrog-mcp-session.sh/.ps1)", reset_session_files),
    ("cli",      "JFrog CLI server       (ID: jfrog-mcp)",                reset_jfrog_cli),
    ("npmrc",    "~/.npmrc entries       (registry + auth token)",         reset_npmrc),
    ("venv",     ".venv folder           (virtual environment)",           reset_venv),
    ("cursor",   "Cursor config          (rule file + mcp.json entries)",  reset_cursor),
    ("claude",   "Claude Code            (plugin + config entries)",       reset_claude_code),
    ("vscode",   "VS Code reference file (~/.jfrog-mcp-vscode.json)",     reset_vscode),
]

def print_menu():
    print(f"""
{BOLD}{CYAN}
╔══════════════════════════════════════════════════════════╗
║       JFrog MCP Gateway  —  Reset Tool                  ║
╚══════════════════════════════════════════════════════════╝{RESET}

  What would you like to reset?

    {BOLD}[A]{RESET}  Everything — full clean slate
    {BOLD}[R]{RESET}  Everything + delete NPM remote repo from JFrog
""")
    for i, (key, label, _) in enumerate(TASKS, 1):
        print(f"    {BOLD}[{i}]{RESET}  {label}")

    print(f"""
    {BOLD}[Q]{RESET}  Quit

  You can pick multiple numbers separated by commas, e.g.  1,3,5
""")


def pick_tasks(choice):
    choice = choice.strip().upper()

    if choice == "Q":
        return []

    if choice in ("A", "R"):
        return [(fn, choice == "R") for (_, _, fn) in TASKS]

    selected = []
    for part in choice.split(","):
        part = part.strip()
        if part.isdigit():
            idx = int(part) - 1
            if 0 <= idx < len(TASKS):
                selected.append((TASKS[idx][2], False))
            else:
                warn(f"No option [{part}] — skipping")
        else:
            warn(f"Unrecognised choice '{part}' — skipping")
    return selected


def confirm(msg):
    ans = input(f"\n{YELLOW}  {msg}  (y/N): {RESET}").strip().lower()
    return ans == "y"

# ─────────────────────────────────────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────────────────────────────────────
def main():
    global DRY

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--all",        action="store_true")
    parser.add_argument("--dry",        action="store_true")
    parser.add_argument("--repo-url",   default="")
    parser.add_argument("--repo-token", default="")
    args, _ = parser.parse_known_args()

    DRY = args.dry
    if DRY:
        print(f"\n{YELLOW}  DRY RUN — nothing will be deleted{RESET}")

    if args.all:
        if not DRY and not confirm("This will wipe ALL JFrog MCP setup. Continue?"):
            print("  Aborted.\n"); return
        tasks = [(fn, False) for (_, _, fn) in TASKS]
    else:
        print_menu()
        while True:
            choice = input(f"{BOLD}  Your choice: {RESET}").strip()
            if choice:
                break
        tasks = pick_tasks(choice)

    if not tasks:
        print("  Nothing selected.\n"); return

    print()
    rule()
    for fn, include_repo in tasks:
        fn()
        if include_repo and fn == reset_vscode:   # after all tasks, do repo
            pass
    if any(include_repo for _, include_repo in tasks):
        reset_npm_remote_repo(
            url=args.repo_url or None,
            token=args.repo_token or None)
    rule()

    print(f"""
  {BOLD}{GREEN}Done.{RESET}  Open a {BOLD}new terminal{RESET} to confirm env vars are cleared.

  To run setup again:
    {'bash run.sh' if not IS_WINDOWS else '.\\run.ps1'}
""")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}  Cancelled.{RESET}\n")
        sys.exit(0)
