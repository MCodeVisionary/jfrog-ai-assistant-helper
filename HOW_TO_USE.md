# How to Use This Setup

## What to say to your coding agent

Copy and paste **exactly this message** into your agent's chat
(Cursor, Claude Code, or VS Code Copilot):

---

> Run the JFrog MCP setup for me.
> Execute this command right now:
>
> `python3 launch_setup.py`
>
> That's all you need to do — don't explain it, don't ask me to run
> anything, just run that command.

---

The agent runs `launch_setup.py` (which takes less than a second).
A new terminal window opens on your screen with the setup wizard inside it.

---

## What happens next

Switch to the new terminal window.  You will be asked **3 questions**:

| Question | What to type |
|---|---|
| JFrog Platform URL | e.g. `https://mycompany.jfrog.io` — ask your admin |
| Access Token | A long code your admin gives you — hidden as you type |
| Project Key | e.g. `my-project` — ask your admin, or press Enter to skip |

Everything else — Node.js, JFrog CLI, npm setup, plugin install,
MCP registration, Claude restart — is fully automatic.

---

## Files in this folder

| File | What it does |
|---|---|
| `launch_setup.py` | **Give this to your agent.** Opens a terminal and starts setup. |
| `jfrog_mcp_setup.py` | The actual setup wizard (runs inside the terminal window). |
| `run.sh` | Bootstrap for macOS/Linux if Python is not yet installed. |
| `run.ps1` | Bootstrap for Windows if Python is not yet installed. |
| `reset.py` | Wipes everything so you can start fresh (testing use). |

---

## If something goes wrong

Contact your JFrog administrator and share any error messages
shown in the terminal window.
