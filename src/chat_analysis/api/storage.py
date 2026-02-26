"""JSON file persistence helpers for group and chat data."""

import json
from pathlib import Path

from chat_analysis.core.config import GROUPS_DIR


def _group_dir(group_id: str) -> Path:
    return GROUPS_DIR / group_id


def _group_path(group_id: str) -> Path:
    return _group_dir(group_id) / "group.json"


def _chat_path(group_id: str, chat_id: str) -> Path:
    return _group_dir(group_id) / "chats" / f"{chat_id}.json"


def _chats_dir(group_id: str) -> Path:
    return _group_dir(group_id) / "chats"


def save_group(group_id: str, data: dict) -> None:
    path = _group_path(group_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load_group(group_id: str) -> dict | None:
    path = _group_path(group_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_chat(group_id: str, chat_id: str, data: dict) -> None:
    path = _chat_path(group_id, chat_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load_chat(group_id: str, chat_id: str) -> dict | None:
    path = _chat_path(group_id, chat_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def load_all_chats(group_id: str) -> list[dict]:
    chats_dir = _chats_dir(group_id)
    if not chats_dir.exists():
        return []
    chats = []
    for path in sorted(chats_dir.glob("*.json")):
        chats.append(json.loads(path.read_text(encoding="utf-8")))
    return chats


def update_chat_status(group_id: str, chat_id: str, status: str) -> None:
    data = load_chat(group_id, chat_id)
    if data is not None:
        data["status"] = status
        save_chat(group_id, chat_id, data)


def save_context(group_id: str, content: str) -> None:
    path = _group_dir(group_id) / "context.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def load_context(group_id: str) -> str:
    path = _group_dir(group_id) / "context.md"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def list_groups() -> list[dict]:
    """Return all group metadata records, sorted by created_at descending."""
    if not GROUPS_DIR.exists():
        return []
    groups = []
    for path in GROUPS_DIR.glob("*/group.json"):
        try:
            groups.append(json.loads(path.read_text(encoding="utf-8")))
        except Exception:
            continue
    groups.sort(key=lambda g: g.get("created_at", ""), reverse=True)
    return groups
