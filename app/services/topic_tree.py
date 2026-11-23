from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Topic
from .stats import Stats


def load_topics(db: Session) -> list[Topic]:
    return list(
        db.scalars(select(Topic).order_by(Topic.position, Topic.name)).all()
    )


def children_map(topics: list[Topic]) -> dict[int | None, list[Topic]]:
    children: dict[int | None, list[Topic]] = {}
    for topic in topics:
        children.setdefault(topic.parent_id, []).append(topic)
    for values in children.values():
        values.sort(key=lambda item: (item.position, item.name))
    return children


def top_level(topics: list[Topic]) -> list[Topic]:
    return [topic for topic in topics if topic.parent_id is None]


def subtree_ids(children: dict[int | None, list[Topic]], root_id: int) -> set[int]:
    result = set()
    stack = [root_id]
    while stack:
        current = stack.pop()
        if current in result:
            continue
        result.add(current)
        stack.extend(topic.id for topic in children.get(current, []))
    return result


def subtree_count(
    children: dict[int | None, list[Topic]],
    direct: dict[int, int],
    root_id: int,
) -> int:
    return sum(direct.get(topic_id, 0) for topic_id in subtree_ids(children, root_id))


def subtree_stats(
    children: dict[int | None, list[Topic]],
    direct: dict[int, Stats],
    root_id: int,
) -> Stats:
    result = Stats()
    for topic_id in subtree_ids(children, root_id):
        current = direct.get(topic_id)
        if current is None:
            continue
        result.total += current.total
        result.correct += current.correct
        result.blank += current.blank
        result.total_seconds += current.total_seconds
    return result


def descendant_rows(
    children: dict[int | None, list[Topic]],
    direct_counts: dict[int, int],
    direct_stats: dict[int, Stats],
    root_id: int,
) -> list[dict]:
    rows = []

    def walk(parent_id: int, depth: int):
        for child in children.get(parent_id, []):
            rows.append(
                {
                    "topic": child,
                    "depth": depth,
                    "count": subtree_count(children, direct_counts, child.id),
                    "stats": subtree_stats(children, direct_stats, child.id),
                }
            )
            walk(child.id, depth + 1)

    walk(root_id, 0)
    return rows
