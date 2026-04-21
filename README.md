# AgentMemory 🧠

> Open-source cross-agent memory layer for AI coding agents.

Your AI agent should remember what you built yesterday, why you rejected that approach last week, and that you prefer `async/await` over callbacks. **AgentMemory makes that happen.**

---

## The Problem

Every time you start a new session with Claude Code, Codex, or Cursor, your agent remembers **nothing**. You re-explain your codebase. You re-teach your preferences. You burn tokens and patience.

**AgentMemory fixes session amnesia.**

---

## Features

- ✅ **Local-first** — SQLite database on your machine. No cloud. No API keys.
- ✅ **Cross-agent** — Works with Claude Code, Codex, Cursor, Gemini CLI, or any agent that can read text.
- ✅ **Simple CLI** — `capture`, `recall`, `load`, `search`. Done.
- ✅ **Structured memory** — Facts, decisions, preferences, actions, errors. Not just chat logs.
- ✅ **Context briefing** — Auto-generates a markdown brief your agent can read at session start.
- ✅ **Project-scoped** — Memories are organized by project (auto-detected from git).

---

## Install

```bash
pip install agentmemory
# or
pipx install agentmemory
# or
uv tool install agentmemory
```

---

## Quick Start

### 1. Initialize memory for your project

```bash
cd my-project
agentmemory init
```

### 2. Capture memories as you work

```bash
agentmemory capture "Chose PostgreSQL over MongoDB for ACID compliance" --category decision --confidence 0.95

agentmemory capture "Always use async/await, never callbacks" --category preference

agentmemory capture "Auth bug: JWT refresh tokens not rotating" --category error
```

### 3. Load context before your agent session

```bash
agentmemory load
# Copy the output into Claude Code / Codex / Cursor
```

Or save it to a file:

```bash
agentmemory load --output AGENT_MEMORY.md
```

### 4. Recall what you did

```bash
agentmemory recall

agentmemory search "auth"
```

---

## How It Works

```
Your Terminal Agent
       │
       ├──► agentmemory capture "..."  ──► SQLite (~/.agent-memory/memory.db)
       │
       ├──► agentmemory load            ──► Markdown brief for agent context
       │
       └──► agentmemory recall/search   ──► Query stored memories
```

**Storage:** Plain SQLite. You can query it with any tool. You can back it up. You can version it.

**Privacy:** Nothing leaves your machine.

---

## Roadmap

- [x] Core SQLite engine
- [x] CLI (init, capture, recall, search, load, export)
- [x] Markdown context brief generation
- [ ] Semantic search (local vector index)
- [ ] Auto-capture from agent sessions
- [ ] Team sync (shared memory via git)
- [ ] MCP server integration

---

## Why Not Just Use CLAUDE.md?

`CLAUDE.md` is static documentation. AgentMemory is **learned memory**:

| CLAUDE.md | AgentMemory |
|-----------|-------------|
| You write it manually | Captured as you work |
| Same every session | Grows and evolves |
| No confidence scoring | Tags confidence + source |
| One file per project | Searchable across all history |

**Use both.** `CLAUDE.md` for stable conventions. AgentMemory for dynamic context.

---

## License

MIT
