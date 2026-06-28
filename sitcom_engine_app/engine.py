from __future__ import annotations

import html
import random
import re
import time
from typing import Any


MODES = [
    "Random",
    "Cold Open",
    "Bottle Episode",
    "Misunderstanding",
    "Rivalry",
    "Bad Plan",
    "Guest Star",
    "Secret Revealed",
    "Finale Chaos",
]

PRIMES = [17, 19, 23, 29, 31, 37, 41]
MOODS = ["defensive", "grand", "suspicious", "generous", "petty", "heroic", "exhausted"]
DRIFTS = ["preserve", "fragment", "distort", "invert", "amplify", "misremember"]

MODE_SETUPS = {
    "Cold Open": "the episode begins halfway through a panic nobody has explained",
    "Bottle Episode": "nobody is allowed to leave until one tiny truth survives",
    "Misunderstanding": "one ordinary sentence is heard in the worst possible way",
    "Rivalry": "two people turn a household detail into a leadership contest",
    "Bad Plan": "a confident fix creates three new jobs and one witness",
    "Guest Star": "a visitor changes the room's social weather immediately",
    "Secret Revealed": "a secret escapes because someone tries to hide it neatly",
    "Finale Chaos": "every running joke demands payment at the same time",
}

MODE_COLLISIONS = {
    "Cold Open": ["everyone freezes in the exact pose that needs explaining", "the smallest object becomes the whole case"],
    "Bottle Episode": ["the door is blocked by principle", "leaving would mean admitting the minutes are false"],
    "Misunderstanding": ["the correction makes the misunderstanding sound official", "three apologies happen to the wrong people"],
    "Rivalry": ["the contest is judged by someone visibly unqualified", "both sides accidentally campaign for the same terrible idea"],
    "Bad Plan": ["the plan technically works and emotionally ruins the room", "the backup plan needs its own apology"],
    "Guest Star": ["the visitor understands the house too quickly", "everyone performs normality until the prop exposes them"],
    "Secret Revealed": ["the secret is old news except to the person guarding it", "the reveal is interrupted by a better, smaller reveal"],
    "Finale Chaos": ["all previous excuses form a queue", "the callback arrives wearing a serious face"],
}

SCENE_SPARKS = [
    {
        "id": "ufo_beam",
        "name": "UFO Beam",
        "description": "Someone gets lifted at the worst possible moment.",
        "mode": "Bottle Episode",
        "premise": "a mysterious beam interrupts a normal room argument and everyone claims jurisdiction",
        "prop_hint": "The Beam Remote",
        "conflict": "the room must decide whether this is an emergency, a prank, or a tenancy issue",
        "callback": "the beam",
        "boost": 12,
    },
    {
        "id": "police_tape",
        "name": "Police Tape",
        "description": "A harmless mystery suddenly has evidence.",
        "mode": "Misunderstanding",
        "premise": "a taped-off corner makes a missing object look like a major investigation",
        "prop_hint": "The Evidence Tape",
        "conflict": "everyone gives a statement and accidentally confesses to something smaller",
        "callback": "the tape",
        "boost": 8,
    },
    {
        "id": "heart_moment",
        "name": "Heart Moment",
        "description": "Two people are seen holding hands and the room overreacts.",
        "mode": "Bad Plan",
        "premise": "a tiny romantic-looking moment becomes a strategy nobody agreed to",
        "prop_hint": "The Emergency Bouquet",
        "conflict": "feelings are treated as logistics until logistics develop feelings",
        "callback": "the heart",
        "boost": 6,
    },
    {
        "id": "missing_object",
        "name": "Missing Object",
        "description": "One ordinary prop vanishes and becomes the whole skit.",
        "mode": "Rivalry",
        "premise": "a missing object makes everyone reveal what they secretly value",
        "prop_hint": "The Missing Thing",
        "conflict": "two theories compete until both become embarrassing",
        "callback": "the missing object",
        "boost": 5,
    },
    {
        "id": "guest_arrives",
        "name": "Guest Arrives",
        "description": "A visitor enters and understands the show too quickly.",
        "mode": "Guest Star",
        "premise": "a guest arrives and immediately changes the power map",
        "prop_hint": "The Visitor Badge",
        "conflict": "everyone performs normality and reveals exactly what normality is hiding",
        "callback": "the guest",
        "boost": 4,
    },
    {
        "id": "bad_plan",
        "name": "Bad Plan",
        "description": "Someone says 'hear me out' and the room should have left.",
        "mode": "Bad Plan",
        "premise": "a confident shortcut creates a public process with witnesses",
        "prop_hint": "The Plan Napkin",
        "conflict": "the plan works on paper and fails in front of people",
        "callback": "the plan",
        "boost": 7,
    },
    {
        "id": "rivalry",
        "name": "Rivalry",
        "description": "Two people make an ordinary detail a leadership contest.",
        "mode": "Rivalry",
        "premise": "a tiny decision becomes a contest for moral authority",
        "prop_hint": "The Score Sheet",
        "conflict": "winning becomes less important than explaining why winning matters",
        "callback": "the score",
        "boost": 6,
    },
    {
        "id": "secret_revealed",
        "name": "Secret Revealed",
        "description": "A secret slips out because someone hides it too carefully.",
        "mode": "Secret Revealed",
        "premise": "a concealed detail escapes through over-preparation",
        "prop_hint": "The Hidden Note",
        "conflict": "the secret is smaller than the cover-up and somehow worse",
        "callback": "the note",
        "boost": 9,
    },
]

PROMPT_SPARK_KEYWORDS = {
    "ufo_beam": [
        "ufo",
        "alien",
        "beam",
        "beams",
        "beaming",
        "abduct",
        "abducted",
        "abduction",
        "spaceship",
        "space ship",
        "saucer",
        "tractor beam",
        "floating",
        "lifted",
    ],
    "police_tape": [
        "police",
        "tape",
        "police tape",
        "chalk",
        "chalk outline",
        "outline",
        "detective",
        "crime",
        "evidence",
        "investigation",
        "case",
        "mystery",
    ],
    "heart_moment": [
        "heart",
        "love",
        "romance",
        "romantic",
        "date",
        "kiss",
        "holding hands",
        "hands",
        "crush",
        "wedding",
        "proposal",
    ],
    "missing_object": [
        "missing",
        "lost",
        "stolen",
        "vanish",
        "vanished",
        "gone",
        "where is",
        "who took",
        "misplaced",
    ],
    "guest_arrives": [
        "guest",
        "visitor",
        "arrives",
        "arrival",
        "stranger",
        "landlord",
        "inspector",
        "auntie",
        "boss",
        "neighbour",
        "neighbor",
    ],
    "bad_plan": [
        "plan",
        "scheme",
        "shortcut",
        "fake",
        "pretend",
        "hear me out",
        "cover story",
        "disguise",
        "trap",
    ],
    "rivalry": [
        "rival",
        "rivals",
        "competition",
        "contest",
        "bet",
        "score",
        "versus",
        "vote",
        "challenge",
        "match",
    ],
    "secret_revealed": [
        "secret",
        "revealed",
        "hidden",
        "note",
        "confess",
        "confession",
        "cover up",
        "coverup",
        "lie",
        "truth",
    ],
}


def get_scene_sparks() -> list[dict[str, Any]]:
    return [dict(spark) for spark in SCENE_SPARKS]


def describe_scene_prompt(prompt: str) -> dict[str, Any]:
    raw_prompt = str(prompt or "").strip()
    normalized = _normalize_prompt(raw_prompt)
    scored: list[dict[str, Any]] = []
    for index, spark in enumerate(SCENE_SPARKS):
        matches = []
        for keyword in PROMPT_SPARK_KEYWORDS.get(str(spark["id"]), []):
            if _keyword_in_prompt(keyword, normalized):
                matches.append(keyword)
        if matches:
            scored.append(
                {
                    "spark": spark,
                    "score": len(matches),
                    "matches": matches,
                    "order": index,
                }
            )

    scored.sort(key=lambda item: (-int(item["score"]), int(item["order"])))
    selected = scored[:3]
    fallback_used = False
    if raw_prompt and not selected:
        fallback = next(spark for spark in SCENE_SPARKS if spark["id"] == "bad_plan")
        selected = [{"spark": fallback, "score": 1, "matches": ["open prompt"], "order": 999}]
        fallback_used = True
    selected.sort(key=lambda item: int(item["order"]))

    selected_sparks = [dict(item["spark"]) for item in selected]
    spark_ids = [str(spark["id"]) for spark in selected_sparks]
    total_score = sum(int(item["score"]) for item in selected)
    mode = "Random"
    if selected_sparks:
        mode = _mode_from_sparks(selected_sparks, random.Random(_prompt_seed(raw_prompt)))
    confidence = _prompt_confidence(raw_prompt, total_score, len(selected_sparks), fallback_used)
    weirdness = 58 if not raw_prompt else min(95, 52 + len(selected_sparks) * 8 + total_score * 3)
    summary = _prompt_summary(raw_prompt, selected, fallback_used)
    return {
        "prompt": raw_prompt,
        "spark_ids": spark_ids,
        "sparks": [
            {
                "id": str(item["spark"]["id"]),
                "name": str(item["spark"]["name"]),
                "score": int(item["score"]),
                "matches": list(item["matches"]),
            }
            for item in selected
        ],
        "mode": mode,
        "weirdness": weirdness,
        "confidence": confidence,
        "summary": summary,
    }


def analyze_state(state: dict[str, Any]) -> dict[str, Any]:
    counts = {
        "characters": len(_items(state, "characters")),
        "locations": len(_items(state, "locations")),
        "props": len(_items(state, "props")),
        "jokes": len(_items(state, "jokes")),
        "rules": len(_items(state, "rules")),
        "relationships": len(_items(state, "relationships")),
        "premises": len(_items(state, "premises")),
    }
    targets = {
        "characters": 3,
        "locations": 1,
        "props": 1,
        "jokes": 2,
        "rules": 1,
        "relationships": 1,
        "premises": 1,
    }
    page_status = {
        "templates": "green" if state.get("template_selected") else "amber",
        "bible": _status(1 if state.get("show_name") and state.get("core_rule") else 0, 1, 1),
        "characters": _status(counts["characters"], 2, targets["characters"]),
        "locations": _status(counts["locations"] + counts["props"], 2, targets["locations"] + targets["props"]),
        "jokes": _status(counts["jokes"] + counts["rules"], 2, targets["jokes"] + targets["rules"]),
        "sparks": "green",
        "generate": "green",
    }
    blockers = []
    for key, target in targets.items():
        if counts[key] < target:
            blockers.append((key, target - counts[key]))
    if counts["characters"] < 2 or counts["locations"] < 1 or counts["jokes"] < 1:
        overall = "red"
    elif blockers:
        overall = "amber"
    else:
        overall = "green"

    next_action = "Generate a skit"
    next_page = "generate"
    if not state.get("template_selected"):
        next_action = "Choose a starting sitcom"
        next_page = "templates"
    elif blockers:
        key, missing = blockers[0]
        label = key.replace("_", " ")
        next_action = f"Add {missing} more {label}"
        next_page = {
            "characters": "characters",
            "locations": "locations",
            "props": "locations",
            "jokes": "jokes",
            "rules": "jokes",
            "relationships": "jokes",
            "premises": "jokes",
        }.get(key, "bible")

    return {
        "overall": overall,
        "counts": counts,
        "targets": targets,
        "pages": page_status,
        "next_action": next_action,
        "next_page": next_page,
        "can_generate": overall in {"amber", "green"},
    }


def generate_episode(state: dict[str, Any], options: dict[str, Any] | None = None) -> dict[str, Any]:
    options = options or {}
    seed = _int(options.get("seed"), None)
    if seed is None:
        seed = int(time.time() * 1000) % 10_000_000
    rng = random.Random(seed)
    scene_prompt = str(options.get("prompt") or options.get("scene_prompt") or "").strip()
    prompt_analysis = describe_scene_prompt(scene_prompt) if scene_prompt else None
    spark_ids = options.get("sparks") or options.get("scene_sparks") or []
    if not spark_ids and prompt_analysis:
        spark_ids = prompt_analysis.get("spark_ids") or []
    selected_sparks = _selected_sparks(spark_ids)
    mode = str(options.get("mode") or "Random")
    if selected_sparks and (mode == "Random" or mode not in MODES):
        mode = _mode_from_sparks(selected_sparks, rng)
    if mode == "Random" or mode not in MODES:
        mode = rng.choice(MODES[1:])
    weirdness_fallback = int(prompt_analysis["weirdness"]) if prompt_analysis else 50
    weirdness = max(0, min(100, _int(options.get("weirdness"), weirdness_fallback)))
    weirdness = max(0, min(100, weirdness + sum(_int(spark.get("boost"), 0) for spark in selected_sparks[:3])))
    cast_size = max(2, min(5, _int(options.get("cast_size"), 4)))

    show_name = str(state.get("show_name") or "Untitled Skit")
    sitcom_type = str(state.get("sitcom_type") or "House")
    tone = str(state.get("tone") or "warm chaos")
    core_rule = str(state.get("core_rule") or "Small problems must become public problems.")
    recurring_premise = str(state.get("recurring_premise") or "The room has opinions.")

    characters = _items(state, "characters") or [_fallback_character()]
    locations = _items(state, "locations") or [_fallback_location()]
    props = _items(state, "props") or [_fallback_prop()]
    jokes = _items(state, "jokes") or [_fallback_joke()]
    rules = _items(state, "rules") or [_fallback_rule()]
    relationships = _items(state, "relationships") or [_fallback_relationship(characters)]
    premises = _items(state, "premises") or [_fallback_premise()]

    cast = _pick_many(rng, characters, cast_size)
    location = rng.choice(locations)
    prop = rng.choice(props)
    joke = rng.choice(jokes)
    rule = rng.choice(rules)
    relationship = rng.choice(relationships)
    premise = rng.choice(premises)
    if selected_sparks:
        premise = {
            "title": _spark_title(selected_sparks, premise),
            "spark": _spark_premise(selected_sparks, premise),
        }
    callback_pool = [spark["callback"] for spark in selected_sparks] + [_name(prop), _name(joke), _safe_get(cast[0], "phrase", _name(cast[0]))]
    callback = rng.choice(callback_pool)

    traces = [_character_trace(rng, character, idx, weirdness) for idx, character in enumerate(cast)]
    midpoint = sum(trace["trace"][-1] for trace in traces) % 29
    escalation = _escalation_level(weirdness, midpoint)
    collision = _collision(mode, rng, prop, joke, relationship, escalation, selected_sparks)
    title = _episode_title(mode, premise, prop, joke, rng)
    beats = _build_beats(
        rng,
        mode,
        cast,
        location,
        prop,
        joke,
        rule,
        relationship,
        premise,
        callback,
        collision,
        escalation,
        core_rule,
        selected_sparks,
    )
    stories = _story_threads(cast, premise, prop, joke, selected_sparks)
    script = _render_script(
        title,
        show_name,
        sitcom_type,
        tone,
        mode,
        weirdness,
        cast,
        location,
        prop,
        joke,
        rule,
        premise,
        beats,
        traces,
        collision,
        recurring_premise,
        selected_sparks,
        stories,
        prompt_analysis,
    )
    best_line = _best_line(beats)
    return {
        "title": title,
        "show_name": show_name,
        "sitcom_type": sitcom_type,
        "mode": mode,
        "seed": seed,
        "weirdness": weirdness,
        "cast_size": len(cast),
        "cast": [_name(item) for item in cast],
        "setting": _name(location),
        "prop": _name(prop),
        "running_joke": _name(joke),
        "rule": _name(rule),
        "premise": _name(premise),
        "scene_sparks": [{"id": spark["id"], "name": spark["name"]} for spark in selected_sparks],
        "scene_prompt": scene_prompt,
        "prompt_analysis": prompt_analysis,
        "stories": stories,
        "beats": beats,
        "collision": collision,
        "traces": traces,
        "trace_lines": _trace_lines(traces, collision, callback, selected_sparks, prompt_analysis),
        "script": script,
        "best_line": best_line,
        "share_text": f"{best_line}\n\nSkitBox | {mode} | seed {seed}",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def episode_to_text(episode: dict[str, Any]) -> str:
    return str(episode.get("script") or "")


def episode_to_html(episode: dict[str, Any]) -> str:
    title = html.escape(str(episode.get("title") or "SkitBox Skit"))
    body = html.escape(episode_to_text(episode))
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<title>{title}</title>"
        "<style>body{font-family:Segoe UI,Arial,sans-serif;line-height:1.5;max-width:860px;margin:40px auto;padding:0 20px;}"
        "pre{white-space:pre-wrap;background:#f5f7f8;border:1px solid #dbe2e6;border-radius:8px;padding:20px;}</style>"
        f"</head><body><h1>{title}</h1><pre>{body}</pre></body></html>"
    )


def _build_beats(
    rng: random.Random,
    mode: str,
    cast: list[dict[str, Any]],
    location: dict[str, Any],
    prop: dict[str, Any],
    joke: dict[str, Any],
    rule: dict[str, Any],
    relationship: dict[str, Any],
    premise: dict[str, Any],
    callback: str,
    collision: dict[str, str],
    escalation: str,
    core_rule: str,
    selected_sparks: list[dict[str, Any]],
) -> list[dict[str, str]]:
    a, b = cast[0], cast[1]
    c = cast[2] if len(cast) > 2 else cast[0]
    d = cast[3] if len(cast) > 3 else cast[-1]
    setup = MODE_SETUPS.get(mode, MODE_SETUPS["Bad Plan"])
    spark_line = _spark_conflict(selected_sparks) if selected_sparks else _safe_get(premise, "spark", "one normal errand has become public")
    return [
        {
            "label": "Cold Open",
            "speaker": "Narrator",
            "line": f"{setup.capitalize()}, because {spark_line}.",
        },
        {
            "label": "Act One - A Story",
            "speaker": _name(a),
            "line": f"{_safe_get(a, 'phrase', 'Right.')} If {_name(prop)} is involved, we need rules before anyone touches {_name(location)}.",
        },
        {
            "label": "Act One - A Story",
            "speaker": _name(b),
            "line": f"I can fix this in one move, assuming nobody asks what the move is.",
        },
        {
            "label": "Act One - B Story",
            "speaker": _name(c),
            "line": f"{_safe_get(c, 'phrase', 'I noticed something.')} {_safe_get(relationship, 'dynamic', 'This room has history')}, while {_name(joke)} starts a second, smaller problem.",
        },
        {
            "label": "Act One - B Story",
            "speaker": "Narrator",
            "line": f"The rule of the show wakes up: {core_rule}",
        },
        {
            "label": "Act Two - Collision",
            "speaker": _name(d),
            "line": f"I am not saying {_name(rule)} is law, but I have already made a queue.",
        },
        {
            "label": "Act Two - Collision",
            "speaker": "Narrator",
            "line": f"The collision turns {escalation}: {collision['action']}",
        },
        {
            "label": "Callback",
            "speaker": _name(a),
            "line": f"Fine. But if anyone asks, {callback} was always part of the plan.",
        },
        {
            "label": "Tag Scene",
            "speaker": rng.choice([_name(x) for x in cast]),
            "line": rng.choice(
                [
                    f"I found the minutes. They apologise to {_name(prop)}.",
                    f"The kettle clicked, so technically I won.",
                    f"Nobody move. The chair looks confident again.",
                    f"We can still call this a pilot if we hide the evidence.",
                ]
            ),
        },
    ]


def _render_script(
    title: str,
    show_name: str,
    sitcom_type: str,
    tone: str,
    mode: str,
    weirdness: int,
    cast: list[dict[str, Any]],
    location: dict[str, Any],
    prop: dict[str, Any],
    joke: dict[str, Any],
    rule: dict[str, Any],
    premise: dict[str, Any],
    beats: list[dict[str, str]],
    traces: list[dict[str, Any]],
    collision: dict[str, str],
    recurring_premise: str,
    selected_sparks: list[dict[str, Any]],
    stories: dict[str, str],
    prompt_analysis: dict[str, Any] | None,
) -> str:
    lines = [
        title.upper(),
        "",
        f"Show: {show_name} ({sitcom_type}, {tone})",
        f"Mode: {mode} | Weirdness: {weirdness}",
        f"Premise: {_name(premise)} - {_safe_get(premise, 'spark', recurring_premise)}",
        f"Scene Sparks: {', '.join(spark['name'] for spark in selected_sparks) if selected_sparks else 'None'}",
    ]
    if prompt_analysis and prompt_analysis.get("prompt"):
        lines.append(f"Scene Prompt: {prompt_analysis['prompt']}")
        lines.append(f"Prompt Read: {prompt_analysis['summary']}")
    lines.extend(
        [
            f"Setting: {_name(location)} - {_safe_get(location, 'texture', 'a room with strong timing')}",
            f"Cast: {', '.join(_name(item) for item in cast)}",
            f"Prop: {_name(prop)} - {_safe_get(prop, 'joke', 'it becomes important too quickly')}",
            f"Running Joke: {_name(joke)} - {_safe_get(joke, 'text', 'it comes back at the wrong time')}",
            "",
            "Story Threads:",
            f"A Story: {stories['a_story']}",
            f"B Story: {stories['b_story']}",
            "",
        ]
    )
    current = ""
    for beat in beats:
        label = beat["label"]
        if label != current:
            lines.extend([f"{label}:", ""])
            current = label
        lines.append(f"{beat['speaker']}: {beat['line']}")
        lines.append("")
    lines.extend(
        [
            "WHY THIS HAPPENED",
            f"Rule triggered: {_name(rule)} - {_safe_get(rule, 'text', 'small problems become public')}",
            f"Collision: {collision['type']} | action={collision['action']}",
        ]
    )
    for trace in traces:
        lines.append(
            f"- {trace['name']}: prime Z{trace['prime']}, seed {trace['seed']}, "
            f"trace {trace['trace']}, mood={trace['mood']}, drift={trace['drift']}"
        )
    return "\n".join(lines).strip() + "\n"


def _character_trace(rng: random.Random, character: dict[str, Any], idx: int, weirdness: int) -> dict[str, Any]:
    prime = rng.choice(PRIMES)
    base = (sum(ord(ch) for ch in _name(character)) + weirdness + idx * 7 + rng.randint(0, prime)) % prime
    step = rng.randint(2, prime - 2)
    trace = []
    value = base
    for i in range(7):
        value = (value * step + weirdness + i + idx) % prime
        trace.append(value)
    return {
        "name": _name(character),
        "prime": prime,
        "seed": base,
        "trace": trace,
        "mood": MOODS[trace[-1] % len(MOODS)],
        "drift": DRIFTS[(trace[0] + trace[-1]) % len(DRIFTS)],
        "want": _safe_get(character, "want", "to be understood"),
        "flaw": _safe_get(character, "flaw", "chooses the wrong moment"),
    }


def _collision(
    mode: str,
    rng: random.Random,
    prop: dict[str, Any],
    joke: dict[str, Any],
    relationship: dict[str, Any],
    escalation: str,
    selected_sparks: list[dict[str, Any]],
) -> dict[str, str]:
    action = rng.choice(MODE_COLLISIONS.get(mode, MODE_COLLISIONS["Bad Plan"]))
    if selected_sparks:
        action = f"{action}, while {_spark_conflict(selected_sparks)}"
    action = (
        f"{action}; {_name(prop)} proves {_name(joke).lower()} was never a side issue, "
        f"and {escalation} energy takes over"
    )
    return {
        "type": mode.lower().replace(" ", "_"),
        "action": action,
        "relationship": _safe_get(relationship, "dynamic", "everyone knows too much"),
    }


def _episode_title(mode: str, premise: dict[str, Any], prop: dict[str, Any], joke: dict[str, Any], rng: random.Random) -> str:
    prop_title = _title_object(prop)
    patterns = [
        f"{_name(premise)}",
        f"The One With {_name(prop)}",
        f"{_name(joke)}: {mode}",
        f"The {prop_title} Situation",
    ]
    return rng.choice(patterns)


def _trace_lines(
    traces: list[dict[str, Any]],
    collision: dict[str, str],
    callback: str,
    selected_sparks: list[dict[str, Any]],
    prompt_analysis: dict[str, Any] | None = None,
) -> list[str]:
    lines = [f"Collision chose {collision['type']} because {collision['relationship']}."]
    if selected_sparks:
        lines.append("Scene sparks: " + ", ".join(spark["name"] for spark in selected_sparks) + ".")
    if prompt_analysis and prompt_analysis.get("prompt"):
        lines.append(f"Prompt read: {prompt_analysis['summary']}")
    lines.append(f"Callback anchor: {callback}.")
    for trace in traces:
        lines.append(
            f"{trace['name']}: Z{trace['prime']} seed {trace['seed']} -> {trace['trace']} "
            f"({trace['mood']}, {trace['drift']})"
        )
    return lines


def _selected_sparks(spark_ids: Any) -> list[dict[str, Any]]:
    if not isinstance(spark_ids, list):
        return []
    wanted = {str(item) for item in spark_ids[:3]}
    return [spark for spark in get_scene_sparks() if spark["id"] in wanted]


def _normalize_prompt(prompt: str) -> str:
    lowered = str(prompt or "").lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", lowered)).strip()


def _keyword_in_prompt(keyword: str, normalized_prompt: str) -> bool:
    normalized_keyword = _normalize_prompt(keyword)
    if not normalized_keyword or not normalized_prompt:
        return False
    return f" {normalized_keyword} " in f" {normalized_prompt} "


def _prompt_seed(prompt: str) -> int:
    return sum((index + 1) * ord(char) for index, char in enumerate(prompt or "")) % 1_000_003


def _prompt_confidence(raw_prompt: str, total_score: int, spark_count: int, fallback_used: bool) -> str:
    if not raw_prompt:
        return "none"
    if fallback_used:
        return "low"
    if spark_count >= 3 or total_score >= 5:
        return "high"
    if spark_count >= 2 or total_score >= 2:
        return "medium"
    return "low"


def _prompt_summary(raw_prompt: str, selected: list[dict[str, Any]], fallback_used: bool) -> str:
    if not raw_prompt:
        return "Type a scene description to translate it into sparks."
    if fallback_used:
        return "No exact spark words found, so Bad Plan is acting as the flexible chaos starter."
    names = ", ".join(str(item["spark"]["name"]) for item in selected)
    matches: list[str] = []
    for item in selected:
        matches.extend(str(match) for match in item["matches"][:3])
    unique_matches = []
    for match in matches:
        if match not in unique_matches:
            unique_matches.append(match)
    evidence = ", ".join(unique_matches[:8])
    return f"Detected {names} from: {evidence}."


def _mode_from_sparks(selected_sparks: list[dict[str, Any]], rng: random.Random) -> str:
    ids = {spark["id"] for spark in selected_sparks}
    if {"ufo_beam", "police_tape"} <= ids:
        return "Misunderstanding"
    if {"heart_moment", "bad_plan"} <= ids:
        return "Bad Plan"
    if {"missing_object", "rivalry"} <= ids:
        return "Rivalry"
    if {"guest_arrives", "secret_revealed"} <= ids:
        return "Guest Star"
    return str(rng.choice(selected_sparks).get("mode") or "Bad Plan")


def _spark_title(selected_sparks: list[dict[str, Any]], fallback: dict[str, Any]) -> str:
    if not selected_sparks:
        return _name(fallback)
    if len(selected_sparks) == 1:
        return f"The {selected_sparks[0]['name']} Skit"
    return "The " + " / ".join(spark["name"] for spark in selected_sparks[:3])


def _spark_premise(selected_sparks: list[dict[str, Any]], fallback: dict[str, Any]) -> str:
    if not selected_sparks:
        return _safe_get(fallback, "spark", "a normal job becomes everyone's problem")
    if len(selected_sparks) == 1:
        return str(selected_sparks[0]["premise"])
    fragments = [str(spark["premise"]) for spark in selected_sparks[:3]]
    return "; then ".join(fragments)


def _spark_conflict(selected_sparks: list[dict[str, Any]]) -> str:
    if not selected_sparks:
        return "one normal errand has become public"
    conflicts = [str(spark["conflict"]) for spark in selected_sparks[:3]]
    if len(conflicts) == 1:
        return conflicts[0]
    return "; meanwhile ".join(conflicts)


def _story_threads(
    cast: list[dict[str, Any]],
    premise: dict[str, Any],
    prop: dict[str, Any],
    joke: dict[str, Any],
    selected_sparks: list[dict[str, Any]],
) -> dict[str, str]:
    lead = _name(cast[0]) if cast else "Someone"
    foil = _name(cast[1]) if len(cast) > 1 else "Everyone"
    a_story = f"{lead} tries to control {_safe_get(premise, 'spark', 'the main problem')} before {_name(prop)} becomes evidence."
    b_story = f"{foil} accidentally keeps {_name(joke)} alive in a side plot that should have stayed small."
    if selected_sparks:
        spark_names = ", ".join(spark["name"] for spark in selected_sparks)
        a_story = f"{lead} tries to explain {spark_names} before the room votes on the wrong version of events."
        b_story = f"{foil} treats the sparks as a separate opportunity and makes the callback inevitable."
    return {"a_story": a_story, "b_story": b_story}


def _best_line(beats: list[dict[str, str]]) -> str:
    candidates = [beat for beat in beats if beat["speaker"] != "Narrator"]
    if not candidates:
        candidates = beats
    scored = sorted(candidates, key=lambda beat: (len(beat["line"]), beat["label"]), reverse=True)
    best = scored[0]
    return f"{best['speaker']}: {best['line']}"


def _escalation_level(weirdness: int, midpoint: int) -> str:
    score = weirdness + midpoint
    if score >= 100:
        return "full finale"
    if score >= 70:
        return "house meeting"
    if score >= 40:
        return "awkward silence"
    return "contained nonsense"


def _status(count: int, red_target: int, green_target: int) -> str:
    if count < red_target:
        return "red"
    if count < green_target:
        return "amber"
    return "green"


def _items(state: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = state.get(key)
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _pick_many(rng: random.Random, items: list[dict[str, Any]], count: int) -> list[dict[str, Any]]:
    if len(items) >= count:
        return rng.sample(items, count)
    picked = list(items)
    while len(picked) < count:
        picked.append(rng.choice(items))
    return picked


def _safe_get(item: dict[str, Any], key: str, fallback: str) -> str:
    value = item.get(key)
    return str(value) if value not in (None, "") else fallback


def _name(item: dict[str, Any]) -> str:
    return _safe_get(item, "name", _safe_get(item, "title", "Untitled"))


def _title_object(item: dict[str, Any]) -> str:
    name = _name(item)
    return name[4:] if name.lower().startswith("the ") else name


def _int(value: Any, fallback: int | None) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _fallback_character() -> dict[str, str]:
    return {
        "name": "Someone",
        "role": "person near the problem",
        "want": "to avoid being blamed",
        "flaw": "speaks too soon",
        "phrase": "This is fine.",
        "pressure": "silence",
    }


def _fallback_location() -> dict[str, str]:
    return {"name": "Room", "texture": "a room waiting for a joke", "rule": "nothing stays small"}


def _fallback_prop() -> dict[str, str]:
    return {"name": "The Object", "joke": "it matters more each time someone denies it"}


def _fallback_joke() -> dict[str, str]:
    return {"name": "The Old Bit", "text": "the same excuse returns wearing a new hat"}


def _fallback_rule() -> dict[str, str]:
    return {"name": "Sitcom Law", "text": "a quiet fix must become a public problem"}


def _fallback_relationship(characters: list[dict[str, Any]]) -> dict[str, str]:
    first = _name(characters[0]) if characters else "Someone"
    return {"from": first, "to": "Everyone", "dynamic": f"{first} knows why this is a bad idea and joins in anyway"}


def _fallback_premise() -> dict[str, str]:
    return {"title": "The Problem", "spark": "a tiny issue becomes everyone's business"}
