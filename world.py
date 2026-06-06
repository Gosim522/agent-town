from __future__ import annotations

from typing import Callable

import config
import dialogue
import llm
from agent import Agent


def plan_day(agent: Agent, day: int) -> dict[str, str]:

    slots_text = ", ".join(config.TIME_SLOTS)
    places_text = ", ".join(config.ALL_PLACES)

    system = (
        f"당신은 '{agent.name}'이라는 사람이다.\n"
        f"프로필: {agent.profile_line()}\n"
        "당신의 직업과 성격, 하루 생활 리듬에 맞게 현실적인 하루 동선을 계획한다."
    )
    user = (
        f"오늘은 가상의 {day}일차다.\n"
        f"활동 시간대: {slots_text}\n"
        f"갈 수 있는 장소: {places_text}\n"
        '("집"은 당신의 개인 공간이다. 쉬거나 혼자 있고 싶을 때 선택한다.)\n\n'
        "각 시간대마다 어디에 있을지 한 곳씩 정하라. "
        "직업(예: 학생은 학교, 카페 사장은 카페 등)과 성격을 반영해 현실적으로 계획하라. "
        "반드시 아래 형식의 JSON만 출력하라.\n"
        '{ "plan": { "08:00": "장소", "11:00": "장소" } }'
    )
    data = llm.chat_json(system, user)
    plan = data.get("plan", {})


    schedule: dict[str, str] = {}
    for slot in config.TIME_SLOTS:
        place = str(plan.get(slot, config.HOME)).strip()
        if place not in config.ALL_PLACES:
            place = config.HOME
        schedule[slot] = place
    agent.schedule = schedule
    return schedule


def _resolve_location(agent: Agent, place: str) -> str:

    if place == config.HOME:
        return f"{agent.name}의 집"
    return place


def _default_printer(event: dict) -> None:

    kind = event["type"]
    if kind == "day_start":
        print(f"\n{'=' * 56}")
        print(f"  가상 {event['day']}일차 시작")
        print(f"{'=' * 56}")
        print("\n[하루 계획 수립]")
    elif kind == "plan":
        plan_str = ", ".join(f"{slot} {place}" for slot, place in event["schedule"].items())
        print(f"  - {event['agent']}: {plan_str}")
    elif kind == "meeting":
        print(f"\n[{event['day']}일차 {event['slot']}] {event['location']}에서 만남: {', '.join(event['names'])}")
        for speaker, line in event["transcript"]:
            print(f"    {speaker}: {line}")
    elif kind == "end":
        print(f"\n{'=' * 56}")
        print("  시뮬레이션 종료")
        print(f"{'=' * 56}")


def run_simulation(
    agents: list[Agent],
    days: int,
    on_event: Callable[[dict], None] | None = None,
) -> list[dict]:

    emit = on_event or _default_printer
    events: list[dict] = []

    def fire(event: dict) -> None:
        events.append(event)
        emit(event)

    for day in range(1, days + 1):
        fire({"type": "day_start", "day": day})


        for agent in agents:
            plan_day(agent, day)
            fire({"type": "plan", "day": day, "agent": agent.name, "schedule": dict(agent.schedule)})


        for slot in config.TIME_SLOTS:
            location_groups: dict[str, list[Agent]] = {}
            for agent in agents:
                place = agent.schedule.get(slot, config.HOME)
                location = _resolve_location(agent, place)
                location_groups.setdefault(location, []).append(agent)


            for location, group in location_groups.items():
                if location in config.PUBLIC_PLACES and len(group) >= 2:
                    transcript = dialogue.run_round(group, location, slot, day)
                    fire(
                        {
                            "type": "meeting",
                            "day": day,
                            "slot": slot,
                            "location": location,
                            "names": [a.name for a in group],
                            "transcript": transcript,
                        }
                    )

    fire({"type": "end"})
    return events
