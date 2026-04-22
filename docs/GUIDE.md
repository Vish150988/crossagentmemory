# CrossAgentMemory Complete User Guide

> **Version:** 0.3.9  
> **GitHub:** https://github.com/Vish150988/crossagentmemory

---

## Table of Contents

1. [Installation](#installation)
2. [Core Concepts](#core-concepts)
3. [Daily Workflow](#daily-workflow)
4. [CLI Reference](#cli-reference)
5. [Memory Categories](#memory-categories)
6. [Auto-Capture](#auto-capture)
7. [Team Sync](#team-sync)
8. [MCP Server](#mcp-server)
9. [Web Dashboard](#web-dashboard)
10. [Git Hooks](#git-hooks)
11. [Advanced Usage](#advanced-usage)
12. [Troubleshooting](#troubleshooting)

---

## Installation

### Basic Install

```bash
pip install crossagentmemory
```

### With All Features

```bash
pip install crossagentmemory[all]
```

### Selective Features

```bash
pip install crossagentmemory[embeddings]   # Better semantic search
pip install crossagentmemory[mcp]          # MCP server for Cursor/Copilot
pip install crossagentmemory[dashboard]    # Web UI
```

### Verify Install

```bash
crossagentmemory --version
# crossagentmemory, version 0.3.9
```

---

## Core Concepts

### What Is CrossAgentMemory?

CrossAgentMemory is a **local-first, cross-agent memory layer** for AI coding assistants. It stores what you learn, decide, and build as structured memories that any agent can read.

### Key Ideas

| Concept | Explanation |
|---------|-------------|
| **Memory** | A single piece of information (decision, fact, error, etc.) |
| **Project** | Memories are scoped by project (auto-detected from git) |
| **Session** | A group of memories from one work session |
| **Confidence** | 0.0 to 1.0 — how much you trust this memory |
| **Category** | Type of memory: fact, decision, action, preference, error |

### Storage

- **Location:** `~/.crossagentmemory/memory.db` (SQLite)
- **Privacy:** Nothing leaves your machine
- **Backup:** Copy the `.db` file or use `crossagentmemory export`

---

## Daily Workflow

### Morning: Start Your Session

```bash
cd my-project

# Optional: set a session ID so today's memories group together
export CROSSAGENTMEMORY_SESSION="stripe-integration"

# Load context from previous sessions
crossagentmemory load
```

**Copy the output** and paste it into your AI agent's context window.

### During The Day: Capture As You Go

```bash
# Architecture decision
crossagentmemory capture "Chose Stripe over PayPal for better API docs" --category decision --confidence 0.9

# Coding convention you just established
crossagentmemory capture "Use pydantic models for all API inputs" --category preference

# Bug you just fixed
crossagentmemory capture "Webhook signature verification fails on empty body" --category error

# What you just built
crossagentmemory capture "Implemented checkout session endpoint" --category action
```

### End Of Day: Auto-Capture Everything

```bash
# Preview what would be captured
crossagentmemory capture-auto --dry-run

# Actually capture from git log, shell history, and Claude sessions
crossagentmemory capture-auto

# Sync to CLAUDE.md for tomorrow
crossagentmemory sync

# Share with your team
crossagentmemory team export
```

### Commit Your Work

```bash
git add .
git add CLAUDE.md .crossagentmemory/   # include shared memory
git commit -m "feat: stripe checkout + shared agent memory"
```

---

## CLI Reference

### Core Commands

```bash
crossagentmemory init                          # Initialize memory for current project
crossagentmemory capture "content"             # Store a memory
crossagentmemory recall                        # List recent memories
crossagentmemory recall --category decision    # Filter by category
crossagentmemory recall --limit 50             # Show more
crossagentmemory search "keyword"              # Keyword search
crossagentmemory related "query"               # Semantic search
crossagentmemory summarize                     # Summarize entire project
crossagentmemory summarize --session <id>      # Summarize one session
crossagentmemory reinforce <id>                # Boost memory confidence
crossagentmemory decay                         # Apply confidence decay
crossagentmemory decay --dry-run               # Preview without changing
```

### Agent Integration

```bash
crossagentmemory load                          # Generate context brief for agents
crossagentmemory sync                          # Generate/update CLAUDE.md
crossagentmemory export                        # Export to markdown file
```

### Auto-Capture

```bash
crossagentmemory capture-auto                  # Capture from all sources
crossagentmemory capture-auto --sources git    # Only git commits
crossagentmemory capture-auto --sources shell,git   # Specific sources
crossagentmemory capture-auto --dry-run        # Preview only
```

### Team Sync

```bash
crossagentmemory team export                   # Export to .crossagentmemory/
crossagentmemory team export --project <name>  # Export specific project
crossagentmemory team import                   # Import team memories
crossagentmemory team import --dry-run         # Preview imports
crossagentmemory team status                   # Show sync state
```

### MCP Server & Dashboard

```bash
crossagentmemory mcp                           # Start MCP server (stdio)
crossagentmemory dashboard                     # Start web UI on :8745
crossagentmemory dashboard --port 8080         # Custom port
```

### Management

```bash
crossagentmemory stats                         # Show statistics
crossagentmemory hook install                  # Install git hooks
crossagentmemory hook uninstall                # Remove git hooks
crossagentmemory delete <project>              # Wipe all memories for project
```

---

## Memory Categories

| Category | When To Use | Example |
|----------|-------------|---------|
| `decision` | Architecture or tech choices | "Chose PostgreSQL over MongoDB" |
| `preference` | Coding style, conventions | "Always use type hints" |
| `fact` | Domain knowledge, structure | "User table has 50M rows" |
| `action` | What you built or changed | "Added OAuth2 login flow" |
| `error` | Bugs, gotchas, failures | "CORS breaks on localhost:3000" |

### Confidence Levels

| Value | Meaning |
|-------|---------|
| 1.0 | Definitely true, validated multiple times |
| 0.8 | Pretty sure, used in production |
| 0.6 | Experimental, might change |
| 0.4 | Old, possibly outdated |
| < 0.1 | Auto-archived by decay |

---

## Auto-Capture

Auto-capture scans your work history and converts it into memories automatically.

### Sources

| Source | What It Captures | Category |
|--------|------------------|----------|
| **Git log** | Commit messages | decision / action / error |
| **Shell history** | `pip install`, `git commit`, `docker run` | action |
| **Claude sessions** | Decision-like assistant messages | decision |

### Example Output

```bash
$ crossagentmemory capture-auto --dry-run
Dry run — would capture 8 memories:

  [action] [git commit] Add Stripe webhook handler
  [decision] [git commit] Chose webhooks over polling for events
  [action] [pip install] stripe==7.0.0
  [error] [git commit] Fix webhook signature verification
  ...
```

### Capture And Store

```bash
$ crossagentmemory capture-auto
[OK] Auto-captured 8 memories:
  shell: 2
  git: 5
  claude: 1
```

---

## Team Sync

Share agent memory across your team via git.

### How It Works

```
You                    Teammate
  |                        |
  ├── team export ──► .crossagentmemory/
  │                        │
  ├── git push ─────► git pull
  │                        │
  │                  team import
  │                        │
  │◄─── shared context ────┘
```

### Workflow

```bash
# You: export and commit
crossagentmemory team export
git add .crossagentmemory/
git commit -m "chore: sync agent memory"
git push

# Teammate: pull and import
git pull
crossagentmemory team import

# Check status anytime
crossagentmemory team status
```

### Deduplication

Team import automatically skips duplicates by content hash. Running `team import` twice is safe — no duplicates created.

---

## MCP Server

Expose CrossAgentMemory as tools to any **MCP-compatible agent** (Cursor, Claude Desktop, Copilot, etc.).

### Start The Server

```bash
crossagentmemory mcp
```

Runs over **stdio** — no network configuration needed.

### Connect To Cursor

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "crossagentmemory": {
      "command": "crossagentmemory",
      "args": ["mcp"]
    }
  }
}
```

Restart Cursor. The CrossAgentMemory tools appear in the MCP panel.

### Connect To Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "crossagentmemory": {
      "command": "crossagentmemory",
      "args": ["mcp"]
    }
  }
}
```

### Available Tools

| Tool | What It Does |
|------|--------------|
| `memory_recall` | Get recent memories for a project |
| `memory_search` | Search by keyword |
| `memory_capture` | Store a new memory |
| `memory_summarize` | Generate project/session summary |
| `memory_stats` | Show memory statistics |
| `memory_related` | Semantic similarity search |

### Example Agent Conversation

> **You:** "What were we doing with authentication?"
>
> **Agent:** *[calls memory_search]*
>
> **Agent:** "You have 5 auth-related memories. The most recent is: 'JWT refresh tokens not rotating on logout' (error, confidence 0.9). Want me to look at the decisions too?"

---

## Web Dashboard

Browse and manage memories in a browser.

### Start

```bash
crossagentmemory dashboard
# → http://localhost:8745
```

### Features

- **Stats cards** — total memories, projects, sessions, categories
- **Memory table** — browse with category badges
- **Search** — keyword filter
- **Category filter** — show only decisions, errors, etc.
- **Capture** — add new memories inline
- **Project switcher** — view any project's memories

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Dashboard UI |
| `/api/stats` | GET | Statistics |
| `/api/memories` | GET | List memories |
| `/api/search` | GET | Search memories |
| `/api/capture` | POST | Create memory |
| `/api/projects` | GET | List all projects |

---

## Git Hooks

Automatically sync `CLAUDE.md` on every commit.

### Install

```bash
crossagentmemory hook install
```

Creates:
- `.git/hooks/pre-commit` — syncs before commit
- `.git/hooks/post-commit` — syncs after commit

### What Happens

Every time you commit:
1. Pre-commit hook runs `crossagentmemory sync`
2. `CLAUDE.md` is updated with latest memories
3. `CLAUDE.md` is auto-added to the commit

### Uninstall

```bash
crossagentmemory hook uninstall
```

---

## Advanced Usage

### Custom Database Location

```bash
export CROSSAGENTMEMORY_DB=/path/to/custom/memory.db
crossagentmemory stats
```

### Session IDs

Group memories by session:

```bash
export CROSSAGENTMEMORY_SESSION="refactor-auth-2024"
crossagentmemory capture "Split auth into service layer" --category action
crossagentmemory capture "Added JWT middleware tests" --category action
```

### Tags

Add searchable tags:

```bash
crossagentmemory capture "Stripe webhook signature bug" --category error --tags "stripe,webhook,security"
crossagentmemory search "stripe"   # finds this
crossagentmemory search "security" # also finds this
```

### Semantic Search Backends

```bash
# Default: TF-IDF (pure numpy, always works)
crossagentmemory related "authentication"

# Optional: sentence-transformers (better quality)
pip install sentence-transformers
crossagentmemory related "authentication" --backend sentence-transformers
```

### Backup & Restore

```bash
# Export all memories to markdown
crossagentmemory export --output backup.md

# The SQLite file itself is portable
cp ~/.crossagentmemory/memory.db ~/backups/memory-$(date +%Y%m%d).db
```

---

## Troubleshooting

### `crossagentmemory: command not found`

```bash
# Use Python module path instead
python -m crossagentmemory.cli --help

# Or reinstall with pip
pip install --force-reinstall -e .
```

### Unicode errors on Windows

CrossAgentMemory uses `[OK]` instead of Unicode checkmarks on Windows. If you still see issues:

```bash
set PYTHONIOENCODING=utf-8
crossagentmemory stats
```

### MCP server not showing in Cursor

1. Verify the server starts: `crossagentmemory mcp` (should hang, waiting for input)
2. Check Cursor's MCP settings JSON is valid
3. Restart Cursor completely

### Dashboard port already in use

```bash
crossagentmemory dashboard --port 8080
```

### Team import shows 0 memories

```bash
# Check you're in the right directory
crossagentmemory team status

# Verify export files exist
ls .crossagentmemory/
```

---

## Quick Start Cheat Sheet

```bash
# 1. Install
pip install crossagentmemory[all]

# 2. Init
cd my-project && crossagentmemory init

# 3. Capture
capture-auto
capture "Key decision" --category decision

# 4. Recall
load          # context brief for agent
search "JWT"  # find specifics
related "auth" # semantic search

# 5. Sync
sync          # generate CLAUDE.md
hook install  # auto-sync on commit

# 6. Share
team export
git add .crossagentmemory/ CLAUDE.md && git commit
```

---

*Last updated: 2026-04-21*  
*For issues: https://github.com/Vish150988/crossagentmemory/issues*
