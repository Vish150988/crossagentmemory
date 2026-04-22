"""Memory confidence decay and reinforcement."""

from __future__ import annotations

from datetime import datetime, timezone

from .core import MemoryEngine


def decay_confidence(
    engine: MemoryEngine,
    project: str | None = None,
    half_life_days: float = 30.0,
    dry_run: bool = False,
) -> dict[str, int]:
    """Decay memory confidence based on age.

    Uses exponential decay: new_confidence = old_confidence * (0.5)^(days/half_life)

    Args:
        engine: MemoryEngine instance
        project: Project to decay (None = all projects)
        half_life_days: Number of days for confidence to halve
        dry_run: If True, only report what would change

    Returns:
        Stats dict with counts
    """
    now = datetime.now(timezone.utc)
    memories = engine.recall(project=project, limit=100000)

    updated = 0
    unchanged = 0
    archived = 0

    for m in memories:
        try:
            created = datetime.fromisoformat(m.timestamp.replace("Z", "+00:00"))
        except ValueError:
            continue

        # Ensure both datetimes are offset-aware
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)

        age_days = (now - created).total_seconds() / 86400.0
        if age_days <= 0:
            unchanged += 1
            continue

        decay_factor = 0.5 ** (age_days / half_life_days)
        new_confidence = m.confidence * decay_factor

        # Archive very old, low-confidence memories
        if new_confidence < 0.1:
            new_confidence = 0.0
            archived += 1

        if abs(new_confidence - m.confidence) > 0.001 and not dry_run:
            engine.update_memory(m.id, {"confidence": round(new_confidence, 4)})
            updated += 1
        else:
            unchanged += 1

    return {
        "updated": updated,
        "unchanged": unchanged,
        "archived": archived,
        "total_processed": len(memories),
    }


def reinforce_memory(engine: MemoryEngine, memory_id: int, boost: float = 0.1) -> bool:
    """Boost confidence of a memory when it's recalled/validated.

    Args:
        engine: MemoryEngine instance
        memory_id: ID of memory to reinforce
        boost: Amount to boost confidence (capped at 1.0)

    Returns:
        True if updated, False if not found
    """
    memory = engine.get_memory_by_id(memory_id)
    if memory is None:
        return False

    new_confidence = min(1.0, memory.confidence + boost)
    engine.update_memory(
        memory_id,
        {"confidence": new_confidence},
    )
    return True
