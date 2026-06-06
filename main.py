from __future__ import annotations

import sys

import config
import report
import world
from agent import Agent


def build_agents() -> list[Agent]:
    agents = [
        Agent(p["name"], p["age"], p["job"], p["personality"]) for p in config.AGENT_PROFILES
    ]
    by_name = {a.name: a for a in agents}


    for name, data in config.INITIAL_KNOWLEDGE.items():
        agent = by_name.get(name)
        if not agent:
            continue
        for about, facts in data.get("facts", {}).items():
            agent.add_facts(about, facts)
        for about, reflection in data.get("relations", {}).items():
            agent.set_reflection(about, reflection)

    return agents


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")

    agents = build_agents()

    print("등장 에이전트:")
    for i, a in enumerate(agents):
        print(f"  [{i}] {a.profile_line()}")

    world.run_simulation(agents, config.NUM_DAYS)

    viewer = agents[config.REPORT_AGENT_INDEX]
    text = report.build_report(viewer, agents)
    print("\n" + text)
    report.save_report(text, config.REPORT_PATH)
    print(f"\n리포트를 '{config.REPORT_PATH}' 파일로 저장했습니다.")


if __name__ == "__main__":
    main()
