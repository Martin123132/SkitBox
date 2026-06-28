from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest


class StorageTests(unittest.TestCase):
    def test_storage_saves_exports_and_opens_under_home(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("SKITBOX_HOME")
            os.environ["SKITBOX_HOME"] = tmp
            try:
                from sitcom_engine_app import storage
                from sitcom_engine_app.engine import generate_episode

                state = storage.load_default_state()
                state["show_name"] = "Test Show"
                state["template_selected"] = True
                saved = storage.save_state(state)
                self.assertEqual(saved["show_name"], "Test Show")
                self.assertEqual(storage.load_state()["show_name"], "Test Show")

                episode = generate_episode(saved, {"seed": 909, "mode": "Cold Open"})
                favourite = storage.save_favourite(episode)
                self.assertEqual(storage.list_favourites()[0]["id"], favourite["id"])

                exported = storage.export_episode(episode, "txt")
                self.assertTrue(Path(exported["path"]).exists())
                self.assertTrue(str(exported["path"]).startswith(tmp))

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


if __name__ == "__main__":
    unittest.main()
