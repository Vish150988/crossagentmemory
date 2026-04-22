"""Extractive session summarization."""

from __future__ import annotations

from collections import Counter

from .core import MemoryEngine, MemoryEntry


def extract_keywords(memories: list[MemoryEntry], top_n: int = 10) -> list[tuple[str, int]]:
    """Extract top keywords from a list of memories."""
    from .semantic import _tokenize

    all_tokens: list[str] = []
    for m in memories:
        all_tokens.extend(_tokenize(m.content))

    counts = Counter(all_tokens)
    return counts.most_common(top_n)


def summarize_session(
    engine: MemoryEngine,
    session_id: str,
    project: str | None = None,
) -> str:
    """Generate an extractive summary of a session."""
    memories = engine.recall(project=project, session_id=session_id, limit=1000)
    if not memories:
        return "_No memories found for this session._"

    # Group by category
    by_category: dict[str, list[MemoryEntry]] = {}
    for m in memories:
        by_category.setdefault(m.category, []).append(m)

    lines = [f"# Session Summary: {session_id}", ""]

    # Keywords
    keywords = extract_keywords(memories, top_n=8)
    if keywords:
        lines.append("## Key Themes")
        lines.append(", ".join(f"{word} ({count})" for word, count in keywords))
        lines.append("")

    # Decisions
    if "decision" in by_category:
        lines.append("## Decisions")
        for m in by_category["decision"]:
            flag = "[high confidence]" if m.confidence > 0.9 else ""
            lines.append(f"- {m.content} {flag}")
        lines.append("")

    # Preferences
    if "preference" in by_category:
        lines.append("## Preferences Established")
        for m in by_category["preference"]:
            lines.append(f"- {m.content}")
        lines.append("")

    # Errors / Warnings
    if "error" in by_category:
        lines.append("## Issues Encountered")
        for m in by_category["error"]:
            lines.append(f"- {m.content}")
        lines.append("")

    # Actions
    if "action" in by_category:
        lines.append("## Actions Taken")
        for m in by_category["action"][:10]:
            lines.append(f"- {m.content}")
        lines.append("")

    # Facts
    if "fact" in by_category:
        lines.append("## Facts Learned")
        for m in by_category["fact"][:10]:
            lines.append(f"- {m.content}")
        lines.append("")

    lines.append(f"_Total memories: {len(memories)}_")
    return "\n".join(lines)


def summarize_project(engine: MemoryEngine, project: str) -> str:
    """Generate a high-level summary of all activity in a project."""
    memories = engine.recall(project=project, limit=10000)
    if not memories:
        return "_No memories found for this project._"

    sessions = set(m.session_id for m in memories)
    keywords = extract_keywords(memories, top_n=10)

    lines = [
        f"# Project Summary: {project}",
        "",
        f"- **Total memories:** {len(memories)}",
        f"- **Sessions:** {len(sessions)}",
        "",
    ]

    if keywords:
        lines.append("## Top Themes")
        for word, count in keywords:
            lines.append(f"- {word}: {count} mentions")
        lines.append("")

    # Recent decisions
    decisions = engine.recall(project=project, category="decision", limit=5)
    if decisions:
        lines.append("## Recent Decisions")
        for m in decisions:
            lines.append(f"- {m.content}")
        lines.append("")

    # Active issues
    errors = engine.recall(project=project, category="error", limit=5)
    if errors:
        lines.append("## Active Issues")
        for m in errors:
            lines.append(f"- {m.content}")
        lines.append("")

    return "\n".join(lines)
