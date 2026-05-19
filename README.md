# JFrog MCP Gateway — Prerequisites

Everything you need to have ready before running the setup wizard.

---

## What the script installs automatically

You do **not** need to install these yourself — the setup script handles them:

- **Node.js + npm** — required to run the MCP Gateway
- **JFrog CLI** — used to register your JFrog server locally

---

## What you need to have ready

### 1. Python 3.9 or higher

The setup script is written in Python. Check if you have it:

```bash
python3 --version
```

If Python is missing or too old, use the bootstrap scripts included in this package instead of running the setup script directly:

| OS | Command |
|---|---|
| macOS / Linux | `bash run.sh` |
| Windows | `.\run.ps1` |

The bootstrap installs the correct Python version automatically, then launches the setup wizard.

---

### 2. A JFrog Platform instance

You need access to a JFrog Platform instance. Ask your JFrog administrator for:

| What | Example |
|---|---|
| **Platform URL** | `https://mycompany.jfrog.io` |
| **Token** | See token types below |
| **Project key** | `my-project` |

---

### 3. A token — two types depending on your role

> **Recommended: let the wizard generate the token for you.**
> When prompted, choose **`[1] Log in via browser`**. The wizard opens
> JFrog in your browser, you sign in with your usual credentials (SSO,
> SAML, LDAP, or username/password), and the token is generated and
> handed back to the script automatically — no copy/paste.
>
> The manual steps below are only needed if the browser flow fails or
> your environment blocks it.

#### Regular user (default)

You need an **Identity Token** — generated from your own JFrog user profile.

<details>
<summary>Manual fallback — generate the token yourself</summary>

Go to:

```
https://<your-instance>.jfrog.io/ui/user_profile
```

Steps on that page:
1. Click **Generate Token** (or **Identity Tokens** section)
2. Give it a name — e.g. `JFrog MCP Setup`
3. Click **Generate** and copy the token
4. Paste it into the terminal when prompted

</details>

#### Platform Administrator

Run the setup with the `--admin` flag:

```bash
python3 jfrog_mcp_setup.py --admin
# or, if you are driving this from a coding agent:
python3 launch_setup.py --admin
```

You need an **Access Token**. The wizard's browser flow generates this
automatically when run with `--admin` — same recommendation as above.

<details>
<summary>Manual fallback — generate the access token yourself</summary>

Go to:

```
https://<your-instance>.jfrog.io/ui/admin/configuration/security/access_tokens
```

Steps:
1. Click **Generate Token**
2. Give it a name — e.g. `JFrog MCP Setup`
3. Set scope to **Applied Permissions / Admin**
4. Set expiry as required by your organisation
5. Click **Generate** and copy the token

</details>

> Access Tokens can only be created by Platform Administrators. If you are
> not an admin, use the regular user flow above.

---

### 4. A coding agent installed

One of the following must be installed on your machine:

| Agent | Install |
|---|---|
| **Cursor** | [cursor.sh](https://cursor.sh) |
| **Claude Code** | [claude.ai/code](https://claude.ai/code) |
| **VS Code + GitHub Copilot** | [code.visualstudio.com](https://code.visualstudio.com) with the [Copilot Chat extension](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot-chat) |

---

### 5. VS Code only — one GitHub org setting

If you are using **VS Code + GitHub Copilot**, your GitHub organisation
administrator must enable this setting once:

```
GitHub.com → Your Organisation → Settings
  → Copilot → Policies
  → Editor preview features → Enabled
```

Without this, Copilot Chat cannot load the JFrog plugin. Contact your
GitHub org admin if this setting is not visible to you.

---

## How to run

### Regular user

If Python 3.9+ is already installed, run the wizard directly:

```bash
python3 jfrog_mcp_setup.py
```

If Python is missing, use the bootstrap scripts (they install Python, then launch the wizard):

```bash
# macOS / Linux
bash run.sh

# Windows (PowerShell)
.\run.ps1
```

### Platform Administrator

```bash
# macOS / Linux
python3 jfrog_mcp_setup.py --admin

# Windows
python jfrog_mcp_setup.py --admin
```

### Driving the setup from a coding agent

Coding agents (Cursor, Claude Code, VS Code + Copilot) cannot drive
interactive prompts through their Bash tool. For that case, use the
launcher instead — it opens a fresh terminal window where the wizard
runs so you can answer the prompts yourself:

```bash
python3 launch_setup.py            # regular user
python3 launch_setup.py --admin    # platform administrator
```

See [HOW_TO_USE.md](HOW_TO_USE.md) for the exact message to paste into
your agent.

---

## Summary checklist

| | Item | Notes |
|---|---|---|
| ☐ | Python 3.9+ | Or use `run.sh` / `run.ps1` to install it |
| ☐ | JFrog Platform URL | From your JFrog administrator |
| ☐ | Identity Token or Access Token | See token section above |
| ☐ | Project key | From your JFrog administrator (optional but recommended) |
| ☐ | Coding agent installed | Cursor, Claude Code, or VS Code + Copilot |
| ☐ | VS Code only: GitHub org preview feature enabled | Admin one-time setup |
