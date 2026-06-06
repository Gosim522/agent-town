from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.8"))


LLM_PROVIDER = os.getenv("LLM_PROVIDER", "auto")

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")


NUM_DAYS = int(os.getenv("NUM_DAYS", "2"))


TIME_SLOTS = ["08:00", "11:00", "14:00", "17:00", "20:00"]


HOME = "집"
PUBLIC_PLACES = ["학교", "카페", "도서관", "레스토랑", "공원", "헬스장"]
ALL_PLACES = [HOME] + PUBLIC_PLACES


CONV_TURNS = int(os.getenv("CONV_TURNS", "4"))


REPORT_AGENT_INDEX = 0


AGENT_PROFILES = [
    {
        "name": "김민준",
        "age": 21,
        "job": "대학생(컴퓨터공학과)",
        "personality": "호기심이 많고 외향적이며, 새로운 사람과 어울리는 것을 좋아한다.",
    },
    {
        "name": "이서연",
        "age": 27,
        "job": "동네 카페 사장 겸 바리스타",
        "personality": "차분하고 다정하며, 사람을 관찰하고 이야기를 들어주는 것을 즐긴다.",
    },
    {
        "name": "박도현",
        "age": 34,
        "job": "프리랜서 소프트웨어 개발자",
        "personality": "내향적이고 분석적이며, 혼자 도서관에서 집중해 일하는 것을 선호한다.",
    },
    {
        "name": "정하늘",
        "age": 23,
        "job": "헬스 트레이너",
        "personality": "활기차고 직설적이며, 운동과 건강에 대한 이야기를 즐긴다.",
    },
]


INITIAL_KNOWLEDGE = {
    "김민준": {
        "facts": {
            "이서연": ["동네 카페 사장님이다.", "가끔 카페에 들러 인사하는 사이다."],
        },
        "relations": {
            "이서연": "단골로 가는 카페의 사장님. 편하게 인사하는 가벼운 친분이 있다.",
        },
    },
    "이서연": {
        "facts": {
            "김민준": ["근처 대학에 다니는 단골 손님이다.", "컴퓨터공학을 전공한다."],
        },
        "relations": {
            "김민준": "카페에 자주 오는 친근한 단골 대학생. 인사를 나누는 사이다.",
        },
    },
}


REPORT_PATH = os.getenv("REPORT_PATH", "report.txt")
