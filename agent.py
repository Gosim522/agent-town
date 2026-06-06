from __future__ import annotations


class Agent:
    def __init__(self, name, age, job, personality):
        self.name = name
        self.age = age
        self.job = job
        self.personality = personality


        self.memory: dict[str, list[str]] = {}

        self.relations: dict[str, str] = {}

        self.schedule: dict[str, str] = {}


    def add_facts(self, about: str, facts: list[str]) -> None:

        bucket = self.memory.setdefault(about, [])
        for fact in facts:
            fact = fact.strip()
            if fact and fact not in bucket:
                bucket.append(fact)

    def known_facts(self, about: str) -> list[str]:
        return self.memory.get(about, [])

    def set_reflection(self, about: str, reflection: str) -> None:
        self.relations[about] = reflection.strip()

    def reflection_on(self, about: str) -> str:
        return self.relations.get(about, "")

    def has_met(self, other_name: str) -> bool:

        return other_name in self.memory or other_name in self.relations


    def profile_line(self) -> str:
        return f"{self.name}({self.age}세, {self.job}) - {self.personality}"

    def memory_brief(self, about: str) -> str:

        facts = self.known_facts(about)
        reflection = self.reflection_on(about)
        parts = []
        if reflection:
            parts.append(f"관계: {reflection}")
        if facts:
            parts.append("알고 있는 사실: " + " / ".join(facts))
        return "\n".join(parts) if parts else "아직 아는 것이 없음(처음 만나는 사이)."


    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "age": self.age,
            "job": self.job,
            "personality": self.personality,
            "memory": self.memory,
            "relations": self.relations,
            "schedule": self.schedule,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Agent":
        agent = cls(data["name"], data["age"], data["job"], data["personality"])
        agent.memory = {k: list(v) for k, v in data.get("memory", {}).items()}
        agent.relations = dict(data.get("relations", {}))
        agent.schedule = dict(data.get("schedule", {}))
        return agent

    def __repr__(self) -> str:
        return f"<Agent {self.name}>"
