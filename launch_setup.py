#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════════════╗
# ║  CODING AGENT — RUN THIS FILE, NOT jfrog_mcp_setup.py              ║
# ║                                                                      ║
# ║  This launcher is non-interactive. Run it with:                     ║
# ║      python3 launch_setup.py                                        ║
# ║                                                                      ║
# ║  It will open a new terminal window and start the setup wizard      ║
# ║  there, so the user can answer the prompts themselves.              ║
# ║  You do not need to do anything after running this file.            ║
# ╚══════════════════════════════════════════════════════════════════════╝
"""
JFrog MCP Gateway — Terminal Launcher
--------------------------------------
Agents cannot drive interactive scripts through their Bash tool because
stdin is not a real terminal.  This launcher solves that:

  1.  Finds jfrog_mcp_setup.py in the same folder as this file.
  2.  Opens a new terminal window on the user's screen.
  3.  Runs the setup wizard inside that terminal so the user can
      answer the prompts themselves.
  4.  Exits immediately — no waiting, no blocking.

Usage (for the coding agent):
    python3 launch_setup.py
"""

import os
import sys
import platform
import subprocess
import shutil
import tempfile

_OS = platform.system()
IS_MAC     = _OS == "Darwin"
IS_WINDOWS = _OS == "Windows"
IS_LINUX   = _OS == "Linux"

GREEN  = "\033[92m"; YELLOW = "\033[93m"; CYAN = "\033[96m"
BOLD   = "\033[1m";  DIM    = "\033[2m";  RESET = "\033[0m"

def info(t):  print(f"{CYAN}  ℹ️   {t}{RESET}")
def ok(t):    print(f"{GREEN}  ✅  {t}{RESET}")
def warn(t):  print(f"{YELLOW}  ⚠️   {t}{RESET}")
def err(t):   print(f"\033[91m  ❌  {t}{RESET}", file=sys.stderr)

# ── Find jfrog_mcp_setup.py ───────────────────────────────────────────────────
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
SETUP_SCRIPT = os.path.join(SCRIPT_DIR, "jfrog_mcp_setup.py")

if not os.path.exists(SETUP_SCRIPT):
    err(f"jfrog_mcp_setup.py not found in:  {SCRIPT_DIR}")
    err("Make sure both files are in the same folder.")
    sys.exit(1)

PYTHON = sys.executable   # same python that ran this launcher

# ── Forward --admin flag if the launcher was called with it ──────────────────
# Usage:
#   python3 launch_setup.py            → regular user  (Identity Token)
#   python3 launch_setup.py --admin    → platform admin (Access Token)
import argparse as _ap
_p = _ap.ArgumentParser(add_help=False)
_p.add_argument("--admin", action="store_true")
_known, _ = _p.parse_known_args()
_ADMIN_FLAG = "--admin" if _known.admin else ""

# ── Build the command that runs in the new terminal window ────────────────────
if IS_WINDOWS:
    terminal_cmd = f'"{PYTHON}" "{SETUP_SCRIPT}" {_ADMIN_FLAG}'.strip()
else:
    escaped = SETUP_SCRIPT.replace("'", "'\\''")
    py_esc  = PYTHON.replace("'", "'\\''")
    terminal_cmd = f"'{py_esc}' '{escaped}' {_ADMIN_FLAG}; echo; echo '  Setup finished. You may close this window.'; exec bash"

# ── Open a new terminal window ────────────────────────────────────────────────
def _open_terminal():
    if IS_MAC:
        # Write an AppleScript to a temp file to avoid quoting nightmares
        apple = (
            f'tell application "Terminal"\n'
            f'    activate\n'
            f'    do script "{terminal_cmd.replace(chr(92), chr(92)*2).replace(chr(34), chr(92)+chr(34))}"\n'
            f'end tell'
        )
        tmp = tempfile.NamedTemporaryFile(suffix=".applescript", mode="w",
                                          delete=False, encoding="utf-8")
        tmp.write(apple)
        tmp.close()
        result = subprocess.run(["osascript", tmp.name],
                                capture_output=True, text=True, timeout=10)
        os.unlink(tmp.name)
        if result.returncode == 0:
            return "Terminal.app"

        # Fallback: try iTerm2
        apple_iterm = (
            f'tell application "iTerm2"\n'
            f'    create window with default profile\n'
            f'    tell current session of current window\n'
            f'        write text "{terminal_cmd.replace(chr(34), chr(92)+chr(34))}"\n'
            f'    end tell\n'
            f'end tell'
        )
        tmp2 = tempfile.NamedTemporaryFile(suffix=".applescript", mode="w",
                                            delete=False, encoding="utf-8")
        tmp2.write(apple_iterm)
        tmp2.close()
        result2 = subprocess.run(["osascript", tmp2.name],
                                  capture_output=True, text=True, timeout=10)
        os.unlink(tmp2.name)
        if result2.returncode == 0:
            return "iTerm2"

        return None

    elif IS_LINUX:
        bash_cmd = f'bash -c \'{terminal_cmd}\''
        for term, flags in [
            ("gnome-terminal", ["--"]),
            ("xterm",          ["-e"]),
            ("konsole",        ["-e"]),
            ("xfce4-terminal", ["-e"]),
            ("lxterminal",     ["-e"]),
            ("mate-terminal",  ["-e"]),
            ("tilix",          ["-e"]),
        ]:
            if shutil.which(term):
                try:
                    subprocess.Popen([term] + flags + [bash_cmd],
                                     start_new_session=True)
                    return term
                except Exception:
                    continue
        return None

    elif IS_WINDOWS:
        try:
            subprocess.Popen(
                ["cmd", "/k", terminal_cmd],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            return "cmd"
        except Exception:
            pass
        try:
            subprocess.Popen(
                ["powershell", "-NoExit", "-Command", terminal_cmd],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            return "PowerShell"
        except Exception:
            pass
        return None

    return None


# ── Main ──────────────────────────────────────────────────────────────────────
print(f"""
{BOLD}{CYAN}
╔══════════════════════════════════════════════════════════╗
║    JFrog MCP Gateway  —  Opening Setup Wizard           ║
╚══════════════════════════════════════════════════════════╝{RESET}

  Opening a new terminal window for the setup wizard...
""")

terminal = _open_terminal()

if terminal:
    ok(f"Setup wizard launched in a new {terminal} window.")
    print(f"""
  {BOLD}What to do next:{RESET}
    1.  Switch to the new terminal window that just opened.
    2.  Follow the prompts — it will ask you for:
          • Your JFrog Platform URL
          • Your Access Token
          • Your Project Key
    3.  Everything else is automatic.

  {DIM}This launcher window can be closed.{RESET}
""")
else:
    warn("Could not open a terminal window automatically.")
    print(f"""
  Please open a terminal yourself and run:

    {CYAN}python3 "{SETUP_SCRIPT}"{RESET}

  {DIM}(copy and paste the line above){RESET}
""")
    sys.exit(1)
