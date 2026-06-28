from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sitcom_engine_app.engine import generate_episode  # noqa: E402
from sitcom_engine_app import storage  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a deterministic SkitBox canon-memory proof.")
    parser.add_argument("--room", default="kitchen", help="Room id or name, such as kitchen or living-room.")
    parser.add_argument("--first-seed", type=int, default=40401)
    parser.add_argument("--second-seed", type=int, default=40402)
    parser.add_argument("--first-mode", default="Bad Plan")
    parser.add_argument("--second-mode", default="Misunderstanding")
    parser.add_argument("--weirdness", type=int, default=70)
    parser.add_argument("--cast-size", type=int, default=4)
    args = parser.parse_args()

    state = storage.reset_state()
    first = generate_episode(
        state,
        {
            "seed": args.first_seed,
            "mode": args.first_mode,
            "weirdness": args.weirdness,
            "cast_size": args.cast_size,
            "room_id": args.room,
        },
    )
    canon = storage.canonize_episode(first)
    second = generate_episode(
        canon["state"],
        {
            "seed": args.second_seed,
            "mode": args.second_mode,
            "weirdness": args.weirdness,
            "cast_size": args.cast_size,
            "room_id": args.room,
        },
    )

    print("=" * 78)
    print("FIRST SCENE - SAVE THIS AS CANON")
    print("=" * 78)
    print(first["script"])
    print("=" * 78)
    print("CANON INCIDENT")
    print("=" * 78)
    print(canon["incident"]["summary"])
    print("=" * 78)
    print("SECOND SCENE - MEMORY SHOULD BE VISIBLE")
    print("=" * 78)
    print(second["script"])
    print("=" * 78)
    print("SECOND TRACE")
    print("=" * 78)
    for line in second["trace_lines"]:
        print(line)


if __name__ == "__main__":
    main()

