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
    parser.add_argument("--prompt", default="", help="Optional weird scene description to translate into sparks.")
    args = parser.parse_args()

    state = load_default_state()
    for seed, mode, weirdness, cast_size in SAMPLES[: max(1, args.count)]:
        options = {"seed": seed, "mode": mode, "weirdness": weirdness, "cast_size": cast_size}
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
