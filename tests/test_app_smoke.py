from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import time
import unittest
from urllib import request


class AppSmokeTests(unittest.TestCase):
    def test_server_doctor_generate_and_export(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env["SKITBOX_HOME"] = tmp
            env["SKITBOX_DISABLE_OPEN"] = "1"
            proc = subprocess.Popen(
                [sys.executable, "-m", "sitcom_engine_app.app", "--no-open", "--port", "0"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=env,
            )
            try:
                url = self._read_url(proc)
                doctor = self._json(url + "/api/doctor")
                self.assertTrue(doctor["ok"])
                self.assertTrue(doctor["doctor"]["state_ok"])
                self.assertTrue(doctor["doctor"]["data_dir"].startswith(tmp))
                self.assertGreaterEqual(doctor["doctor"]["template_count"], 5)

                templates = self._json(url + "/api/templates")
                self.assertTrue(templates["ok"])
                self.assertGreaterEqual(len(templates["templates"]), 5)

                guide = self._text(url + "/guide")
                self.assertIn("<!doctype html>", guide)
                self.assertIn("<title>SkitBox</title>", guide)
                self.assertIn("<strong>SkitBox</strong>", guide)

                rooms_page = self._text(url + "/rooms")
                self.assertIn("<!doctype html>", rooms_page)
                self.assertIn("data-page=\"rooms\"", rooms_page)
                memory_page = self._text(url + "/memory")
                self.assertIn("<!doctype html>", memory_page)
                self.assertIn("data-page=\"memory\"", memory_page)

                css = self._text(url + "/static/app.css")
                self.assertIn("skitbox-guide-bg-v1.png", css)
                self.assertIn("skitbox-sparks-bg-v1.png", css)
                self.assertIn("skitbox-studio-bg-v2.png", css)
                self.assertIn("skitbox-library-bg-v1.png", css)
                self.assertIn("skitbox-wallpaper-v1.png", css)
                for asset in [
                    "skitbox-guide-bg-v1.png",
                    "skitbox-sparks-bg-v1.png",
                    "skitbox-studio-bg-v2.png",
                    "skitbox-library-bg-v1.png",
                    "skitbox-wallpaper-v1.png",
                ]:
                    self.assertGreater(len(self._bytes(url + f"/static/assets/{asset}")), 1000)

                applied = self._post_json(url + "/api/template", {"template_id": "pub"})
                self.assertTrue(applied["ok"])
                self.assertEqual(applied["state"]["sitcom_type"], "Pub")
                room_id = applied["state"]["rooms"][0]["id"]
                room_name = applied["state"]["rooms"][0]["name"]

                described = self._post_json(url + "/api/describe", {"prompt": "A saucer beam, police tape, and a heart above two people."})
                self.assertTrue(described["ok"])
                self.assertEqual(described["analysis"]["spark_ids"], ["ufo_beam", "police_tape", "heart_moment"])

                started = time.perf_counter()
                generated = self._post_json(
                    url + "/api/generate",
                    {
                        "seed": 5150,
                        "mode": "Random",
                        "weirdness": 75,
                        "cast_size": 4,
                        "room_id": room_id,
                        "sparks": ["heart_moment", "bad_plan"],
                    },
                )
                elapsed = time.perf_counter() - started
                self.assertLess(elapsed, 2)
                self.assertTrue(generated["ok"])
                self.assertIn("WHY THIS HAPPENED", generated["episode"]["script"])
                self.assertEqual(generated["episode"]["mode"], "Bad Plan")
                self.assertEqual(generated["episode"]["room"]["id"], room_id)
                self.assertIn(f"Room: {room_name}", generated["episode"]["script"])
                self.assertIn("Previously In This Room", generated["episode"]["script"])

                canon = self._post_json(url + "/api/canon", {"episode": generated["episode"]})
                self.assertTrue(canon["ok"])
                self.assertEqual(canon["incident"]["seed"], 5150)
                self.assertEqual(canon["readiness"]["counts"]["memory"], 1)
                self.assertEqual(canon["state"]["room_history"][0]["incidents"][0]["title"], generated["episode"]["title"])

                reset_memory = self._post_json(url + "/api/memory/reset", {})
                self.assertTrue(reset_memory["ok"])
                self.assertEqual(reset_memory["readiness"]["counts"]["memory"], 0)

                prompt_generated = self._post_json(
                    url + "/api/generate",
                    {
                        "seed": 20260627,
                        "mode": "Random",
                        "weirdness": 72,
                        "cast_size": 4,
                        "prompt": "A saucer beam, police tape, and a heart above two people.",
                    },
                )
                self.assertTrue(prompt_generated["ok"])
                self.assertEqual(
                    [spark["id"] for spark in prompt_generated["episode"]["scene_sparks"]],
                    ["ufo_beam", "police_tape", "heart_moment"],
                )
                self.assertIn("Scene Prompt:", prompt_generated["episode"]["script"])

                exported = self._post_json(url + "/api/export", {"episode": generated["episode"], "format": "html"})
                self.assertTrue(exported["ok"])
                self.assertTrue(exported["export"]["path"].startswith(tmp))

                open_exports = self._post_json(url + "/api/open-exports", {})
                self.assertTrue(open_exports["ok"])
                self.assertFalse(open_exports["export_folder"]["opened"])
            finally:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                if proc.stdout:
                    proc.stdout.close()

    def _read_url(self, proc: subprocess.Popen[str]) -> str:
        assert proc.stdout is not None
        deadline = time.time() + 8
        while time.time() < deadline:
            line = proc.stdout.readline()
            if not line:
                if proc.poll() is not None:
                    break
                continue
            match = re.search(r"http://127\.0\.0\.1:\d+", line)
            if match:
                return match.group(0)
        self.fail("Server did not print a local URL")

    def _json(self, url: str) -> dict:
        with request.urlopen(url, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))

    def _text(self, url: str) -> str:
        with request.urlopen(url, timeout=5) as response:
            return response.read().decode("utf-8")

    def _bytes(self, url: str) -> bytes:
        with request.urlopen(url, timeout=5) as response:
            return response.read()

    def _post_json(self, url: str, payload: dict) -> dict:
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(url, data=data, headers={"content-type": "application/json"}, method="POST")
        with request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
