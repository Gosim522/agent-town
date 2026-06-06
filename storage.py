from __future__ import annotations

import json

from agent import Agent


def serialize(agents: list[Agent]) -> str:

    return json.dumps(
        {"agents": [a.to_dict() for a in agents]},
        ensure_ascii=False,
        indent=2,
    )


def deserialize(text: str) -> list[Agent]:

    data = json.loads(text)
    return [Agent.from_dict(item) for item in data.get("agents", [])]


def save_state(agents: list[Agent], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(serialize(agents))


def load_state(path: str) -> list[Agent]:
    with open(path, "r", encoding="utf-8") as f:
        return deserialize(f.read())
