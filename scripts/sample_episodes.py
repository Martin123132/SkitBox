from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sitcom_engine_app.engine import generate_episode  # noqa: E402
from sitcom_engine_app.storage import load_default_state  # noqa: E402


SAMPLES = [
    (101, "Bottle Episode", 58, 4),
    (202, "Misunderstanding", 72, 4),
    (303, "Bad Plan", 64, 5),
    (404, "Guest Star", 50, 3),
    (505, "Finale Chaos", 84, 5),
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate deterministic SkitBox sample skits.")
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument("--seed", type=int, default=None, help="Generate one exact seed instead of the built-in sample batch.")
    parser.add_argument("--mode", default="Random", help="Mode to use with --seed.")
    parser.add_argument("--weirdness", type=int, default=58, help="Weirdness to use with --seed.")
    parser.add_argument("--cast-size", type=int, default=4, help="Cast size to use with --seed.")
    parser.add_argument("--room", default="", help="Optional room id or name, such as kitchen or living-room.")
    parser.add_argument("--prompt", default="", help="Optional weird scene description to translate into sparks.")
    args = parser.parse_args()

    state = load_default_state()
    samples = SAMPLES[: max(1, args.count)]
    if args.seed is not None:
        samples = [(args.seed, args.mode, args.weirdness, args.cast_size)]
    for seed, mode, weirdness, cast_size in samples:
        options = {"seed": seed, "mode": mode, "weirdness": weirdness, "cast_size": cast_size}
        if args.room:
            options["room_id"] = args.room
        if args.prompt:
            options["mode"] = "Random"
            options["prompt"] = args.prompt
        episode = generate_episode(
            state,
            options,
        )
        print("=" * 78)
        print(episode["script"])


if __name__ == "__main__":
    main()
