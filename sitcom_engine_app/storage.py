from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import Any

from .engine import analyze_state, episode_to_html, episode_to_share_card_html, episode_to_text


APP_NAME = "SkitBox"
MEMORY_LIMIT = 3


def app_root() -> Path:
    return Path(__file__).resolve().parent.parent


def app_data_dir() -> Path:
    override = os.getenv("SKITBOX_HOME")
    if override:
        root = Path(override).expanduser()
    elif app_root().drive and app_root().drive.upper() != "C:":
        root = app_root() / "user_data"
    else:
        drive_root = _preferred_d_drive_root()
        root = drive_root or (
            Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / APP_NAME
            if os.name == "nt"
            else Path.home() / ".local" / "share" / "skitbox"
        )
    root.mkdir(parents=True, exist_ok=True)
    return root


def _preferred_d_drive_root() -> Path | None:
    if os.name != "nt":
        return None
    candidate = Path("D:/SkitBoxData")
    try:
        candidate.mkdir(parents=True, exist_ok=True)
        if os.access(candidate, os.W_OK):
            return candidate
    except OSError:
        return None
    return None


def exports_dir() -> Path:
    path = app_data_dir() / "exports"
    path.mkdir(parents=True, exist_ok=True)
    return path


def default_state_path() -> Path:
    return app_root() / "sitcom_engine_app" / "seeds" / "default_show.json"


def templates_path() -> Path:
    return app_root() / "sitcom_engine_app" / "seeds" / "templates.json"


def user_state_path() -> Path:
    return app_data_dir() / "show.json"


def favourites_path() -> Path:
    return app_data_dir() / "favourites.json"


def load_default_state() -> dict[str, Any]:
    return _read_json(default_state_path(), fallback={})


def load_templates() -> list[dict[str, Any]]:
    data = _read_json(templates_path(), fallback=[])
    if not isinstance(data, list):
        return []
    return [template for template in data if isinstance(template, dict) and template.get("id") and isinstance(template.get("state"), dict)]


def apply_template(template_id: str) -> dict[str, Any]:
    for template in load_templates():
        if template.get("id") == template_id:
            state = normalize_state(dict(template["state"]))
            state["template_id"] = str(template_id)
            state["template_selected"] = True
            save_state(state)
            return state
    raise ValueError(f"Unknown template: {template_id}")


def load_state() -> dict[str, Any]:
    path = user_state_path()
    if not path.exists():
        state = load_default_state()
        save_state(state)
        return state
    state = _read_json(path, fallback=None)
    if not isinstance(state, dict) or not state.get("show_name"):
        broken = path.with_suffix(f".broken-{int(time.time())}.json")
        try:
            shutil.copy2(path, broken)
        except OSError:
            pass
        state = load_default_state()
        save_state(state)
    return normalize_state(state)


def save_state(state: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_state(state)
    _write_json(user_state_path(), normalized)
    return normalized


def reset_state() -> dict[str, Any]:
    state = load_default_state()
    save_state(state)
    return state


def list_favourites() -> list[dict[str, Any]]:
    data = _read_json(favourites_path(), fallback=[])
    return data if isinstance(data, list) else []


def save_favourite(episode: dict[str, Any]) -> dict[str, Any]:
    favourites = list_favourites()
    item = {
        "id": f"episode-{int(time.time() * 1000)}",
        "title": str(episode.get("title") or "Untitled Skit"),
        "mode": episode.get("mode"),
        "seed": episode.get("seed"),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "episode": episode,
    }
    favourites.insert(0, item)
    _write_json(favourites_path(), favourites[:200])
    return item


def canonize_episode(episode: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(episode, dict) or not episode.get("script"):
        raise ValueError("No skit supplied")
    state = load_state()
    state, incident = _apply_episode_canon(state, episode)
    saved = save_state(state)
    return {"state": saved, "incident": incident}


def reset_memory() -> dict[str, Any]:
    state = load_state()
    for room in state.get("rooms", []):
        if isinstance(room, dict):
            room["memory"] = "No canon saved here yet."
    state["character_states"] = _normalize_character_states([], state)
    state["room_history"] = _normalize_room_history([], state)
    return save_state(state)


def export_episode(episode: dict[str, Any], export_format: str = "txt") -> dict[str, Any]:
    export_format = str(export_format or "txt").lower()
    if export_format not in {"txt", "html", "json", "card"}:
        export_format = "txt"
    title = str(episode.get("title") or "skitbox-skit")
    stem = _slugify(title)[:70] or "skitbox-skit"
    stamp = time.strftime("%Y%m%d-%H%M%S")
    extension = "html" if export_format == "card" else export_format
    path = exports_dir() / f"{stamp}-{stem}.{extension}"
    if export_format == "html":
        content = episode_to_html(episode)
    elif export_format == "card":
        content = episode_to_share_card_html(episode)
    elif export_format == "json":
        content = json.dumps(episode, indent=2, ensure_ascii=False)
    else:
        content = episode_to_text(episode)
    path.write_text(content, encoding="utf-8")
    return {"path": str(path), "format": export_format, "title": title}


def export_world_pack(state: dict[str, Any] | None = None) -> dict[str, Any]:
    state = normalize_state(state or load_state())
    stamp = time.strftime("%Y%m%d-%H%M%S")
    show_name = _slugify(str(state.get("show_name") or "skitbox-world"))[:70] or "skitbox-world"
    path = exports_dir() / f"{stamp}-{show_name}-world-pack.json"
    payload = {
        "skitbox_world_pack": 1,
        "exported_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "app": APP_NAME,
        "state": state,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"path": str(path), "format": "json", "title": str(state.get("show_name") or "SkitBox World")}


def import_world_pack(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("World pack must be a JSON object.")
    state = payload.get("state") if isinstance(payload.get("state"), dict) else payload
    if not isinstance(state, dict):
        raise ValueError("World pack does not contain a show state.")
    return save_state(state)


def open_exports_folder(opener: Any | None = None) -> dict[str, Any]:
    path = exports_dir().resolve()
    root = app_data_dir().resolve()
    if path != root and root not in path.parents:
        raise RuntimeError("Refusing to open a folder outside SkitBox data.")
    try:
        if os.getenv("SKITBOX_DISABLE_OPEN") == "1":
            return {"opened": False, "path": str(path), "error": "Opening folders is disabled for this run."}
        if opener:
            opener(path)
        elif os.name == "nt":
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
        return {"opened": True, "path": str(path)}
    except (OSError, RuntimeError) as exc:
        return {"opened": False, "path": str(path), "error": str(exc)}


def doctor() -> dict[str, Any]:
    data_dir = app_data_dir()
    state = load_state()
    memory_count = sum(
        len(item.get("incidents", []))
        for item in state.get("room_history", [])
        if isinstance(item, dict) and isinstance(item.get("incidents"), list)
    )
    return {
        "data_dir": str(data_dir),
        "storage_mode": _storage_mode(),
        "state_path": str(user_state_path()),
        "favourites_path": str(favourites_path()),
        "exports_dir": str(exports_dir()),
        "state_ok": bool(state.get("show_name")),
        "readiness": analyze_state(state),
        "favourite_count": len(list_favourites()),
        "template_count": len(load_templates()),
        "memory_count": memory_count,
    }


def normalize_state(state: dict[str, Any]) -> dict[str, Any]:
    default = load_default_state()
    source_has_rooms = isinstance(state, dict) and isinstance(state.get("rooms"), list) and bool(state.get("rooms"))
    normalized = dict(default)
    if isinstance(state, dict):
        normalized.update(state)
    normalized["version"] = int(normalized.get("version") or 1)
    normalized["template_id"] = str(normalized.get("template_id") or default.get("template_id") or "shared_house")
    normalized["template_selected"] = bool(normalized.get("template_selected", default.get("template_selected", False)))
    for key in ["show_name", "sitcom_type", "tone", "core_rule", "recurring_premise"]:
        normalized[key] = str(normalized.get(key) or default.get(key) or "")
    for key in ["characters", "locations", "props", "jokes", "rules", "relationships", "premises"]:
        if not isinstance(normalized.get(key), list):
            normalized[key] = default.get(key, [])
    if source_has_rooms:
        normalized["rooms"] = _normalize_rooms(normalized.get("rooms"), normalized)
    else:
        normalized["rooms"] = _derive_rooms(normalized)
    normalized["character_states"] = _normalize_character_states(normalized.get("character_states"), normalized)
    normalized["room_history"] = _normalize_room_history(normalized.get("room_history"), normalized)
    return normalized


def _apply_episode_canon(state: dict[str, Any], episode: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    state = normalize_state(state)
    room = episode.get("room") if isinstance(episode.get("room"), dict) else {}
    room_id = str(room.get("id") or "").strip()
    if not room_id and state.get("rooms"):
        room_id = str(state["rooms"][0].get("id") or "")
    room_name = str(room.get("name") or _room_name(state, room_id) or "No fixed room")
    title = str(episode.get("title") or "Untitled Skit")
    mode = str(episode.get("mode") or "Scene")
    summary = _canon_summary(episode, room_name)
    incident = {
        "title": title,
        "mode": mode,
        "seed": episode.get("seed"),
        "summary": summary,
        "cast": _string_list(episode.get("cast")),
        "prop": str(episode.get("prop") or ""),
        "running_joke": str(episode.get("running_joke") or ""),
        "created_at": str(episode.get("created_at") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
    }

    history = _normalize_room_history(state.get("room_history"), state)
    matched_history = None
    for item in history:
        if str(item.get("room_id") or "") == room_id:
            matched_history = item
            break
    if matched_history is None:
        matched_history = {"room_id": room_id, "room_name": room_name, "incidents": []}
        history.insert(0, matched_history)
    matched_history["room_name"] = room_name
    duplicate = any(
        existing.get("title") == incident["title"] and existing.get("seed") == incident["seed"]
        for existing in matched_history.get("incidents", [])
    )
    old_incidents = [
        existing
        for existing in matched_history.get("incidents", [])
        if not (existing.get("title") == incident["title"] and existing.get("seed") == incident["seed"])
    ]
    matched_history["incidents"] = [incident, *old_incidents][:MEMORY_LIMIT]
    state["room_history"] = history

    for room_item in state.get("rooms", []):
        if isinstance(room_item, dict) and str(room_item.get("id") or "") == room_id:
            room_item["memory"] = summary

    traces = {
        str(trace.get("name") or ""): trace
        for trace in episode.get("traces", [])
        if isinstance(trace, dict) and trace.get("name")
    }
    character_states = _normalize_character_states(state.get("character_states"), state)
    by_name = {str(item.get("name") or ""): item for item in character_states}
    collision = episode.get("collision") if isinstance(episode.get("collision"), dict) else {}
    for name in incident["cast"]:
        item = by_name.get(name)
        if item is None:
            item = {
                "name": name,
                "mood": "ready",
                "pressure": "being noticed",
                "last_incident": "",
                "relationship_nudge": "",
                "pinned": False,
                "canon_count": 0,
            }
            character_states.append(item)
            by_name[name] = item
        trace = traces.get(name) or {}
        item["mood"] = str(trace.get("mood") or item.get("mood") or "charged")
        item["pressure"] = _short(
            f"{mode} around {episode.get('prop') or 'the room'}",
            96,
        )
        item["last_incident"] = summary
        item["relationship_nudge"] = _short(str(collision.get("relationship") or episode.get("best_line") or ""), 120)
        item["canon_count"] = _safe_int(item.get("canon_count"), 0) + (0 if duplicate else 1)
    state["character_states"] = character_states
    return state, incident


def _normalize_character_states(value: Any, state: dict[str, Any]) -> list[dict[str, Any]]:
    existing: dict[str, dict[str, Any]] = {}
    if isinstance(value, dict):
        iterable = [dict(item, name=name) if isinstance(item, dict) else {"name": name} for name, item in value.items()]
    elif isinstance(value, list):
        iterable = [item for item in value if isinstance(item, dict)]
    else:
        iterable = []
    for item in iterable:
        name = str(item.get("name") or "").strip()
        if name:
            existing[_slugify(name)] = item

    states: list[dict[str, Any]] = []
    for character in [item for item in state.get("characters", []) if isinstance(item, dict)]:
        name = str(character.get("name") or "Unnamed").strip() or "Unnamed"
        item = existing.get(_slugify(name), {})
        states.append(
            {
                "name": name,
                "mood": str(item.get("mood") or "ready"),
                "pressure": str(item.get("pressure") or character.get("pressure") or "being noticed"),
                "last_incident": str(item.get("last_incident") or ""),
                "relationship_nudge": str(item.get("relationship_nudge") or ""),
                "pinned": bool(item.get("pinned", False)),
                "canon_count": _safe_int(item.get("canon_count"), 0),
            }
        )
    return states


def _normalize_room_history(value: Any, state: dict[str, Any]) -> list[dict[str, Any]]:
    existing: dict[str, dict[str, Any]] = {}
    if isinstance(value, dict):
        iterable = [dict(item, room_id=room_id) if isinstance(item, dict) else {"room_id": room_id} for room_id, item in value.items()]
    elif isinstance(value, list):
        iterable = [item for item in value if isinstance(item, dict)]
    else:
        iterable = []
    for item in iterable:
        key = _slugify(str(item.get("room_id") or item.get("room_name") or item.get("name") or ""))
        if key:
            existing[key] = item

    history: list[dict[str, Any]] = []
    for room in [item for item in state.get("rooms", []) if isinstance(item, dict)]:
        room_id = str(room.get("id") or _slugify(str(room.get("name") or ""))).strip()
        room_name = str(room.get("name") or room.get("location") or room_id or "Room").strip()
        item = existing.get(_slugify(room_id)) or existing.get(_slugify(room_name)) or {}
        incidents = [
            _normalize_incident(incident)
            for incident in (item.get("incidents") or [])
            if isinstance(incident, dict)
        ][:MEMORY_LIMIT]
        history.append({"room_id": room_id, "room_name": room_name, "incidents": incidents})
    return history


def _normalize_incident(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": str(item.get("title") or "Untitled Skit"),
        "mode": str(item.get("mode") or "Scene"),
        "seed": item.get("seed"),
        "summary": str(item.get("summary") or ""),
        "cast": _string_list(item.get("cast")),
        "prop": str(item.get("prop") or ""),
        "running_joke": str(item.get("running_joke") or ""),
        "created_at": str(item.get("created_at") or ""),
    }


def _canon_summary(episode: dict[str, Any], room_name: str) -> str:
    title = str(episode.get("title") or "Untitled Skit")
    mode = str(episode.get("mode") or "Scene")
    prop = str(episode.get("prop") or "the prop")
    joke = str(episode.get("running_joke") or "the running joke")
    return _short(f"{title} left {room_name} carrying {mode} energy around {prop} and {joke}.", 180)


def _room_name(state: dict[str, Any], room_id: str) -> str:
    for room in state.get("rooms", []):
        if isinstance(room, dict) and str(room.get("id") or "") == room_id:
            return str(room.get("name") or room.get("location") or room_id)
    return ""


def _normalize_rooms(value: Any, state: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return _derive_rooms(state)
    rooms: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or item.get("location") or f"Room {index + 1}").strip() or f"Room {index + 1}"
        room_id = str(item.get("id") or _slugify(name) or f"room-{index + 1}").strip()
        if room_id in seen:
            room_id = f"{room_id}-{index + 1}"
        seen.add(room_id)
        rooms.append(
            {
                "id": room_id,
                "name": name,
                "mood": str(item.get("mood") or "ready for trouble"),
                "description": str(item.get("description") or item.get("texture") or ""),
                "location": str(item.get("location") or name),
                "cast": _string_list(item.get("cast")),
                "props": _string_list(item.get("props")),
                "jokes": _string_list(item.get("jokes")),
                "rule": str(item.get("rule") or ""),
                "memory": str(item.get("memory") or "Nothing has been moved here yet."),
            }
        )
    return rooms or _derive_rooms(state)


def _derive_rooms(state: dict[str, Any]) -> list[dict[str, Any]]:
    locations = [item for item in state.get("locations", []) if isinstance(item, dict)] or [{"name": "Main Room"}]
    characters = [str(item.get("name")) for item in state.get("characters", []) if isinstance(item, dict) and item.get("name")]
    props = [str(item.get("name")) for item in state.get("props", []) if isinstance(item, dict) and item.get("name")]
    jokes = [str(item.get("name")) for item in state.get("jokes", []) if isinstance(item, dict) and item.get("name")]
    rules = [str(item.get("name")) for item in state.get("rules", []) if isinstance(item, dict) and item.get("name")]
    rooms: list[dict[str, Any]] = []
    for index, location in enumerate(locations):
        name = str(location.get("name") or f"Room {index + 1}")
        room_cast = _slice_names(characters, index, len(locations), 2)
        room_props = _slice_names(props, index, len(locations), 1)
        room_jokes = _slice_names(jokes, index, len(locations), 1)
        rule = str(location.get("rule") or (rules[index % len(rules)] if rules else "small problems get louder here"))
        rooms.append(
            {
                "id": _slugify(name) or f"room-{index + 1}",
                "name": name,
                "mood": "pressure building",
                "description": str(location.get("texture") or "a room with strong timing"),
                "location": name,
                "cast": room_cast,
                "props": room_props,
                "jokes": room_jokes,
                "rule": rule,
                "memory": "This room is waiting for its first proper incident.",
            }
        )
    return rooms


def _slice_names(names: list[str], index: int, room_count: int, minimum: int) -> list[str]:
    if not names:
        return []
    picked = names[index:: max(1, room_count)]
    cursor = 0
    while len(picked) < min(minimum, len(names)):
        candidate = names[(index + cursor) % len(names)]
        if candidate not in picked:
            picked.append(candidate)
        cursor += 1
    return picked


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return []


def _short(value: str, limit: int) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)].rstrip(" .,!?:;") + "..."


def _safe_int(value: Any, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _storage_mode() -> str:
    if os.getenv("SKITBOX_HOME"):
        return "SKITBOX_HOME"
    if app_root().drive and app_root().drive.upper() != "C:":
        return "portable_user_data"
    if _preferred_d_drive_root():
        return "d_drive_fallback"
    return "local_app_data"


def _read_json(path: Path, fallback: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return fallback


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.{time.time_ns()}.tmp")
    try:
        tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)
    finally:
        try:
            if tmp.exists():
                tmp.unlink()
        except OSError:
            pass


def _slugify(value: str) -> str:
    value = value.lower()
    value = "".join(ch if ch.isalnum() else "-" for ch in value)
    while "--" in value:
        value = value.replace("--", "-")
    return value.strip("-")
