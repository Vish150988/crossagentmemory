"""CLI interface for AgentMemory."""

from __future__ import annotations

import json
import os
import sys
import uuid
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from .core import DEFAULT_MEMORY_DIR, MemoryEngine, MemoryEntry
from .export import export_markdown
from .recall import build_context_brief

console = Console()


def _get_project() -> str:
    """Detect project name from git repo or directory name."""
    cwd = Path.cwd()
    git_dir = cwd / ".git"
    if git_dir.exists():
        # Try to read git config for remote name
        try:
            import subprocess

            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                cwd=cwd,
            )
            if result.returncode == 0:
                url = result.stdout.strip()
                # Extract repo name from URL
                name = url.split("/")[-1].replace(".git", "")
                if name:
                    return name
        except Exception:
            pass
    return cwd.name


@click.group()
@click.version_option(version="0.1.0")
def main() -> None:
    """AgentMemory — Cross-agent memory layer for AI coding agents."""
    pass


@main.command()
@click.option("--project", "-p", help="Project name (auto-detected by default)")
def init(project: str | None) -> None:
    """Initialize agent memory for the current project."""
    project = project or _get_project()
    engine = MemoryEngine()

    # Store minimal project context
    engine.set_project_context(
        project,
        context={
            "initialized_at": str(Path.cwd()),
            "cwd": str(Path.cwd()),
        },
        description=f"Project initialized at {Path.cwd()}",
    )

    console.print(f"[green][OK][/green] Initialized agent memory for project: [bold]{project}[/bold]")
    console.print(f"  Database: {DEFAULT_MEMORY_DIR / 'memory.db'}")


@main.command()
@click.argument("content")
@click.option("--project", "-p", help="Project name")
@click.option("--category", "-c", default="fact", type=click.Choice(["fact", "decision", "action", "preference", "error"]))
@click.option("--confidence", default=1.0, type=float)
@click.option("--tags", "-t", default="", help="Comma-separated tags")
@click.option("--source", "-s", default="user", help="Source of the memory")
def capture(
    content: str,
    project: str | None,
    category: str,
    confidence: float,
    tags: str,
    source: str,
) -> None:
    """Capture a memory entry."""
    project = project or _get_project()
    engine = MemoryEngine()

    session_id = os.environ.get("AGENTMEMORY_SESSION", str(uuid.uuid4())[:8])

    entry = MemoryEntry(
        project=project,
        session_id=session_id,
        category=category,
        content=content,
        confidence=confidence,
        source=source,
        tags=tags,
    )
    memory_id = engine.store(entry)
    console.print(f"[green][OK][/green] Captured memory [bold]#{memory_id}[/bold] in [bold]{project}[/bold]")


@main.command()
@click.option("--project", "-p", help="Project name")
@click.option("--category", "-c", help="Filter by category")
@click.option("--limit", "-n", default=20, help="Number of memories to show")
def recall(project: str | None, category: str | None, limit: int) -> None:
    """Recall recent memories."""
    project = project or _get_project()
    engine = MemoryEngine()
    memories = engine.recall(project=project, category=category, limit=limit)

    if not memories:
        console.print(f"[yellow]No memories found for project '{project}'[/yellow]")
        return

    table = Table(title=f"Recent Memories — {project}")
    table.add_column("ID", style="dim", width=6)
    table.add_column("Category", width=12)
    table.add_column("Content")
    table.add_column("Source", width=12)
    table.add_column("Time", width=16)

    for m in memories:
        table.add_row(
            str(m.id),
            f"[bold]{m.category}[/bold]",
            m.content[:80] + ("..." if len(m.content) > 80 else ""),
            m.source,
            m.timestamp[:16].replace("T", " "),
        )

    console.print(table)


@main.command()
@click.argument("keyword")
@click.option("--project", "-p", help="Project name")
@click.option("--limit", "-n", default=10)
def search(keyword: str, project: str | None, limit: int) -> None:
    """Search memories by keyword."""
    project = project or _get_project()
    engine = MemoryEngine()
    results = engine.search(keyword, project=project, limit=limit)

    if not results:
        console.print(f"[yellow]No results for '{keyword}'[/yellow]")
        return

    for m in results:
        console.print(f"[bold]#{m.id}[/bold] [{m.category}] {m.content[:100]}")


@main.command()
@click.option("--project", "-p", help="Project name")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
def load(project: str | None, output: str | None) -> None:
    """Load context briefing for your AI agent."""
    project = project or _get_project()
    engine = MemoryEngine()
    brief = build_context_brief(engine, project)

    if output:
        Path(output).write_text(brief, encoding="utf-8")
        console.print(f"[green][OK][/green] Context written to {output}")
    else:
        console.print("\n[bold cyan]--- Agent Context Brief ---[/bold cyan]\n")
        console.print(brief)
        console.print("\n[dim]Copy the above into your agent's context.[/dim]")


@main.command()
@click.option("--project", "-p", help="Project name")
@click.option("--output", "-o", type=click.Path(), help="Output markdown file")
def export(project: str | None, output: str | None) -> None:
    """Export memories to markdown."""
    project = project or _get_project()
    engine = MemoryEngine()
    md = export_markdown(engine, project)

    if output:
        Path(output).write_text(md, encoding="utf-8")
        console.print(f"[green][OK][/green] Exported to {output}")
    else:
        out_path = Path.cwd() / f"AGENT_MEMORY_{project}.md"
        out_path.write_text(md, encoding="utf-8")
        console.print(f"[green][OK][/green] Exported to {out_path}")


@main.command()
def stats() -> None:
    """Show memory statistics."""
    engine = MemoryEngine()
    data = engine.stats()

    console.print("[bold]AgentMemory Stats[/bold]\n")
    console.print(f"Total memories: {data['total_memories']}")
    console.print(f"Projects: {data['projects']}")
    console.print(f"Sessions: {data['sessions']}")
    if data["by_category"]:
        console.print("\nBy category:")
        for cat, count in data["by_category"].items():
            console.print(f"  {cat}: {count}")


@main.command()
@click.argument("project")
@click.confirmation_option(prompt="Are you sure you want to delete all memories for this project?")
def delete(project: str) -> None:
    """Delete all memories for a project."""
    engine = MemoryEngine()
    count = engine.delete_project(project)
    console.print(f"[red][DELETED][/red] {count} memories for project '{project}'")


if __name__ == "__main__":
    main()
