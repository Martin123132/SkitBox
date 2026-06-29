from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock


class StorageTests(unittest.TestCase):
    def test_replace_with_retry_handles_transient_permission_error(self) -> None:
        from sitcom_engine_app import storage

        class FlakySource:
            def __init__(self) -> None:
                self.attempts = 0

            def replace(self, target: Path) -> None:
                self.attempts += 1
                if self.attempts < 3:
                    raise PermissionError("locked briefly")

        source = FlakySource()
        with mock.patch.object(storage.time, "sleep") as sleep:
            storage._replace_with_retry(source, Path("D:/SkitBoxData/show.json"))  # type: ignore[arg-type]

        self.assertEqual(source.attempts, 3)
        self.assertEqual(sleep.call_count, 2)

    def test_storage_saves_exports_and_opens_under_home(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("SKITBOX_HOME")
            old_disable_open = os.environ.get("SKITBOX_DISABLE_OPEN")
            os.environ["SKITBOX_HOME"] = tmp
            os.environ.pop("SKITBOX_DISABLE_OPEN", None)
            try:
                from sitcom_engine_app import storage
                from sitcom_engine_app.engine import generate_episode

                state = storage.load_default_state()
                state["show_name"] = "Test Show"
                state["template_selected"] = True
                saved = storage.save_state(state)
                self.assertEqual(saved["show_name"], "Test Show")
                self.assertEqual(storage.load_state()["show_name"], "Test Show")
                self.assertGreaterEqual(len(saved["rooms"]), 1)

                saved["rooms"][0]["cast"] = ["Nina"]
                saved["rooms"][0]["memory"] = "Nina moved the good chair into evidence."
                storage.save_state(saved)
                reloaded = storage.load_state()
                self.assertEqual(reloaded["rooms"][0]["cast"], ["Nina"])
                self.assertEqual(reloaded["rooms"][0]["memory"], "Nina moved the good chair into evidence.")

                episode = generate_episode(reloaded, {"seed": 909, "mode": "Cold Open", "room_id": reloaded["rooms"][0]["id"]})
                canon = storage.canonize_episode(episode)
                self.assertEqual(canon["incident"]["seed"], 909)
                self.assertEqual(canon["state"]["room_history"][0]["incidents"][0]["title"], episode["title"])
                self.assertTrue(any(item["canon_count"] >= 1 for item in canon["state"]["character_states"]))
                self.assertIn("Cold Open", canon["state"]["rooms"][0]["memory"])

                reloaded_after_canon = storage.load_state()
                remembered = generate_episode(
                    reloaded_after_canon,
                    {"seed": 910, "mode": "Bad Plan", "room_id": reloaded_after_canon["rooms"][0]["id"]},
                )
                self.assertTrue(remembered["memory_context"]["has_memory"])
                self.assertIn("Previously In This Room", remembered["script"])

                reset = storage.reset_memory()
                self.assertEqual(sum(len(room["incidents"]) for room in reset["room_history"]), 0)
                self.assertFalse(any(item["last_incident"] for item in reset["character_states"]))

                favourite = storage.save_favourite(episode)
                self.assertEqual(storage.list_favourites()[0]["id"], favourite["id"])

                exported = storage.export_episode(episode, "txt")
                self.assertTrue(Path(exported["path"]).exists())
                self.assertTrue(str(exported["path"]).startswith(tmp))

                card = storage.export_episode(episode, "card")
                card_path = Path(card["path"])
                self.assertEqual(card["format"], "card")
                self.assertEqual(card_path.suffix, ".html")
                self.assertTrue(card_path.exists())
                self.assertIn("SkitBox share card", card_path.read_text(encoding="utf-8"))

                world_pack = storage.export_world_pack(reloaded_after_canon)
                world_pack_path = Path(world_pack["path"])
                self.assertTrue(world_pack_path.exists())
                self.assertTrue(str(world_pack_path).startswith(tmp))
                world_pack_payload = json.loads(world_pack_path.read_text(encoding="utf-8"))
                self.assertEqual(world_pack_payload["skitbox_world_pack"], 1)
                self.assertEqual(world_pack_payload["state"]["show_name"], "Test Show")

                world_pack_payload["state"]["show_name"] = "Imported Show"
                imported = storage.import_world_pack(world_pack_payload)
                self.assertEqual(imported["show_name"], "Imported Show")
                self.assertEqual(storage.load_state()["show_name"], "Imported Show")

                opened_paths = []
                opened = storage.open_exports_folder(opener=lambda path: opened_paths.append(path))
                self.assertTrue(opened["opened"])
                self.assertEqual(opened_paths[0], Path(tmp, "exports").resolve())

                templates = storage.load_templates()
                self.assertGreaterEqual(len(templates), 5)
                office = storage.apply_template("office")
                self.assertEqual(office["template_id"], "office")
                self.assertTrue(office["template_selected"])
                self.assertEqual(office["sitcom_type"], "Office")
            finally:
                if old_home is None:
                    os.environ.pop("SKITBOX_HOME", None)
                else:
                    os.environ["SKITBOX_HOME"] = old_home
                if old_disable_open is None:
                    os.environ.pop("SKITBOX_DISABLE_OPEN", None)
                else:
                    os.environ["SKITBOX_DISABLE_OPEN"] = old_disable_open


if __name__ == "__main__":
    unittest.main()
