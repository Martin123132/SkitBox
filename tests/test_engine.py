from __future__ import annotations

import unittest

from sitcom_engine_app.engine import analyze_state, describe_scene_prompt, generate_episode
from sitcom_engine_app.storage import load_default_state


class EngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = load_default_state()
        self.state["template_selected"] = True

    def test_same_seed_produces_same_episode(self) -> None:
        options = {"seed": 12345, "mode": "Bottle Episode", "weirdness": 60, "cast_size": 4}
        first = generate_episode(self.state, options)
        second = generate_episode(self.state, options)
        self.assertEqual(first["script"], second["script"])
        self.assertEqual(first["trace_lines"], second["trace_lines"])

    def test_different_seed_changes_episode(self) -> None:
        first = generate_episode(self.state, {"seed": 111, "mode": "Bad Plan"})
        second = generate_episode(self.state, {"seed": 222, "mode": "Bad Plan"})
        self.assertNotEqual(first["script"], second["script"])

    def test_missing_seed_auto_generates_nonzero_seed(self) -> None:
        episode = generate_episode(self.state, {"mode": "Bad Plan"})
        self.assertIsInstance(episode["seed"], int)
        self.assertGreater(episode["seed"], 0)

    def test_trace_steps_are_seven(self) -> None:
        episode = generate_episode(self.state, {"seed": 77, "mode": "Misunderstanding", "cast_size": 5})
        self.assertTrue(episode["traces"])
        for trace in episode["traces"]:
            self.assertEqual(len(trace["trace"]), 7)

    def test_episode_has_required_sections(self) -> None:
        episode = generate_episode(self.state, {"seed": 303, "mode": "Finale Chaos"})
        script = episode["script"]
        for section in ["Cold Open", "Act One - A Story", "Act One - B Story", "Act Two - Collision", "Callback", "Tag Scene", "WHY THIS HAPPENED"]:
            self.assertIn(section, script)
        self.assertIn("Story Threads", script)
        self.assertIn("best_line", episode)
        self.assertIn("share_text", episode)

    def test_readiness_changes_when_state_is_thin(self) -> None:
        full = analyze_state(self.state)
        thin = dict(self.state)
        thin["characters"] = []
        thin["jokes"] = []
        thin_ready = analyze_state(thin)
        self.assertEqual(full["overall"], "green")
        self.assertEqual(thin_ready["overall"], "red")
        self.assertEqual(thin_ready["next_page"], "characters")

    def test_scene_sparks_drive_episode(self) -> None:
        episode = generate_episode(
            self.state,
            {"seed": 4242, "mode": "Random", "sparks": ["ufo_beam", "police_tape"], "weirdness": 40},
        )
        self.assertEqual(episode["mode"], "Misunderstanding")
        self.assertEqual([spark["id"] for spark in episode["scene_sparks"]], ["ufo_beam", "police_tape"])
        self.assertIn("UFO Beam", episode["script"])
        self.assertIn("Police Tape", episode["trace_lines"][1])

    def test_scene_prompt_detects_sparks(self) -> None:
        analysis = describe_scene_prompt(
            "A flying saucer beams up the landlord behind police tape while two people hold hands."
        )
        self.assertEqual(analysis["spark_ids"], ["ufo_beam", "police_tape", "heart_moment"])
        self.assertEqual(analysis["confidence"], "high")
        self.assertIn("UFO Beam", analysis["summary"])
        self.assertIn("Police Tape", analysis["summary"])

    def test_scene_prompt_can_generate_without_manual_sparks(self) -> None:
        episode = generate_episode(
            self.state,
            {
                "seed": 6060,
                "mode": "Random",
                "prompt": "A chalk outline appears beside the sofa and an alien beam lifts the remote.",
            },
        )
        self.assertEqual([spark["id"] for spark in episode["scene_sparks"]], ["ufo_beam", "police_tape"])
        self.assertIn("Scene Prompt:", episode["script"])
        self.assertIn("Prompt Read:", episode["script"])
        self.assertTrue(any(line.startswith("Prompt read:") for line in episode["trace_lines"]))


if __name__ == "__main__":
    unittest.main()
