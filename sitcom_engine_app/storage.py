from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import Any

from .engine import analyze_state, episode_to_html, episode_to_text


APP_NAME = "SkitBox"


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


def export_episode(episode: dict[str, Any], export_format: str = "txt") -> dict[str, Any]:
    export_format = str(export_format or "txt").lower()
    if export_format not in {"txt", "html", "json"}:
        export_format = "txt"
    title = str(episode.get("title") or "skitbox-skit")
    stem = _slugify(title)[:70] or "skitbox-skit"
    stamp = time.strftime("%Y%m%d-%H%M%S")
    path = exports_dir() / f"{stamp}-{stem}.{export_format}"
    if export_format == "html":
        content = episode_to_html(episode)
    elif export_format == "json":
        content = json.dumps(episode, indent=2, ensure_ascii=False)
    else:
        content = episode_to_text(episode)
    path.write_text(content, encoding="utf-8")
    return {"path": str(path), "format": export_format, "title": title}


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
    }


def normalize_state(state: dict[str, Any]) -> dict[str, Any]:
    default = load_default_state()
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
    return normalized


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
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def _slugify(value: str) -> str:
    value = value.lower()
    value = "".join(ch if ch.isalnum() else "-" for ch in value)
    while "--" in value:
        value = value.replace("--", "-")
    return value.strip("-")
