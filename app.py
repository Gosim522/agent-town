from __future__ import annotations

import config
import dialogue
import llm
import report
import storage
import world
from agent import Agent
from main import build_agents

import streamlit as st

st.set_page_config(page_title="Generative Agent 시뮬레이션", layout="wide")


if "agents" not in st.session_state:
    st.session_state.agents = build_agents()


def agents_by_name() -> dict[str, Agent]:
    return {a.name: a for a in st.session_state.agents}


with st.sidebar:
    st.header("설정")
    st.markdown(f"**현재 LLM 공급자**\n\n`{llm.provider_info()}`")
    if llm.PROVIDER_NAME == "ollama":
        st.caption("OpenAI 키가 없어 로컬 Ollama로 동작 중입니다. (응답이 다소 느릴 수 있어요)")

    st.divider()
    st.subheader("상태 저장 / 불러오기")
    st.download_button(
        "상태 저장 (JSON 다운로드)",
        data=storage.serialize(st.session_state.agents),
        file_name="simulation_state.json",
        mime="application/json",
        use_container_width=True,
    )
    uploaded = st.file_uploader("상태 파일 선택 (JSON)", type="json")
    if uploaded is not None and st.button("이 파일로 불러오기", use_container_width=True):
        try:
            st.session_state.agents = storage.deserialize(uploaded.getvalue().decode("utf-8"))
            st.success("상태를 불러왔습니다.")
        except Exception as exc:
            st.error(f"불러오기 실패: {exc}")

    st.divider()
    if st.button("초기 상태로 리셋", use_container_width=True):
        st.session_state.agents = build_agents()
        st.success("초기 상태로 되돌렸습니다.")


st.title("Generative Agent 시뮬레이션")
st.caption("에이전트들이 하루를 계획하고, 같은 장소에서 만나 대화하며, 서로에 대한 사실과 관계를 쌓습니다.")

tab_agents, tab_manual, tab_auto, tab_report = st.tabs(
    ["에이전트", "수동 대화", "자동 시뮬레이션", "리포트"]
)


with tab_agents:
    st.subheader("현재 에이전트")
    for a in st.session_state.agents:
        with st.expander(a.profile_line()):
            st.markdown("**Memory (상대별 알고 있는 사실)**")
            if a.memory:
                for other, facts in a.memory.items():
                    st.markdown(f"- {other}: " + " / ".join(facts))
            else:
                st.caption("아직 없음")
            st.markdown("**Relation Map (관계 / Reflection)**")
            if a.relations:
                for other, rel in a.relations.items():
                    st.markdown(f"- {other}: {rel}")
            else:
                st.caption("아직 없음")

    st.divider()
    st.subheader("새 에이전트 추가")
    with st.form("add_agent"):
        c1, c2 = st.columns(2)
        name = c1.text_input("이름")
        age = c2.number_input("나이", min_value=1, max_value=120, value=25)
        job = st.text_input("직업")
        personality = st.text_area("성격", height=70)
        init_mem = st.text_area("초기 기억 (선택, 한 줄에 하나씩  '상대|사실' 형식)", height=70,
                                placeholder="예) 이서연|동네 카페 사장님이다")
        submitted = st.form_submit_button("추가")
    if submitted:
        if not name.strip():
            st.warning("이름을 입력하세요.")
        elif name in agents_by_name():
            st.warning("같은 이름의 에이전트가 이미 있습니다.")
        else:
            new_agent = Agent(name.strip(), int(age), job.strip(), personality.strip())
            for line in init_mem.splitlines():
                if "|" in line:
                    other, fact = line.split("|", 1)
                    if other.strip() and fact.strip():
                        new_agent.add_facts(other.strip(), [fact.strip()])
            st.session_state.agents.append(new_agent)
            st.success(f"'{name}' 에이전트를 추가했습니다.")


with tab_manual:
    st.subheader("수동 대화 라운드")
    st.caption("참여자와 발언 수, 주제를 직접 정해 한 라운드를 실행합니다. 주제를 비우면 각자 기억을 바탕으로 이야기합니다.")

    all_names = [a.name for a in st.session_state.agents]
    selected = st.multiselect("참여 에이전트 (2명 이상)", all_names, default=all_names[:2])
    c1, c2 = st.columns(2)
    turns = c1.number_input("발언 수(turns)", min_value=2, max_value=12, value=int(config.CONV_TURNS))
    place = c2.selectbox("장소", config.PUBLIC_PLACES)
    topic = st.text_input("주제 (선택)")

    if st.button("대화 실행", type="primary"):
        if len(selected) < 2:
            st.warning("최소 2명을 선택하세요.")
        else:
            mapping = agents_by_name()
            participants = [mapping[n] for n in selected]
            with st.spinner("대화를 생성하는 중..."):
                result = dialogue.run_round_detailed(
                    participants, place, "수동", 0, turns=int(turns), topic=topic or None
                )
            st.markdown("#### 대화")
            for speaker, line in result["transcript"]:
                st.markdown(f"**{speaker}**: {line}")

            st.markdown("#### 추출된 사실 (Fact)")
            any_fact = False
            for subject, facts in result["facts"].items():
                if facts:
                    any_fact = True
                    st.markdown(f"- **{subject}**: " + " / ".join(facts))
            if not any_fact:
                st.caption("추출된 새 사실이 없습니다.")

            st.markdown("#### 갱신된 관계 (Reflection)")
            for observer, targets in result["reflections"].items():
                for target, summary in targets.items():
                    st.markdown(f"- {observer} → {target}: {summary}")


with tab_auto:
    st.subheader("자동 시뮬레이션")
    st.caption("각 에이전트가 하루 계획을 세우고, 시간 순서로 진행하며 같은 장소에 모이면 자동으로 대화합니다.")
    days = st.number_input("진행할 가상 일수", min_value=1, max_value=5, value=int(config.NUM_DAYS))

    if st.button("시뮬레이션 실행", type="primary"):
        with st.status("시뮬레이션 진행 중...", expanded=True) as status:

            def on_event(event: dict) -> None:
                kind = event["type"]
                if kind == "day_start":
                    st.markdown(f"### 가상 {event['day']}일차")
                    st.markdown("**하루 계획**")
                elif kind == "plan":
                    plan_str = ", ".join(f"{s} {p}" for s, p in event["schedule"].items())
                    st.markdown(f"- {event['agent']}: {plan_str}")
                elif kind == "meeting":
                    st.markdown(
                        f"**[{event['day']}일차 {event['slot']}] {event['location']}** — "
                        + ", ".join(event["names"])
                    )
                    for speaker, line in event["transcript"]:
                        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;{speaker}: {line}", unsafe_allow_html=True)

            world.run_simulation(st.session_state.agents, int(days), on_event=on_event)
            status.update(label="시뮬레이션 완료", state="complete")
        st.success("완료되었습니다. '리포트' 탭에서 결과를 확인하세요.")


with tab_report:
    st.subheader("관계 리포트")
    names = [a.name for a in st.session_state.agents]
    default_idx = min(config.REPORT_AGENT_INDEX, len(names) - 1) if names else 0
    viewer_name = st.selectbox("리포트 기준 에이전트", names, index=default_idx)

    if st.button("리포트 생성", type="primary"):
        viewer = agents_by_name()[viewer_name]
        text = report.build_report(viewer, st.session_state.agents)
        st.text(text)
        st.download_button(
            "리포트 다운로드 (.txt)",
            data=text,
            file_name=f"{viewer_name}_report.txt",
            mime="text/plain",
        )
