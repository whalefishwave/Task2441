"""问卷结构、元数据完整性与匿名性测试（A1/A2/A3/A4）。"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from app.questionnaire import (  # noqa: E402
    QUESTIONS,
    SECTIONS,
    get_questionnaire,
    validate_questionnaire,
)


def test_question_count_within_range() -> None:
    assert 20 <= len(QUESTIONS) <= 30
    assert len(QUESTIONS) == 28


def test_seven_sections_plus_optional() -> None:
    assert [code for code, _ in SECTIONS] == ["A", "B", "C", "D", "E", "F", "G", "H"]


def test_question_ids_unique() -> None:
    ids = [q.qid for q in QUESTIONS]
    assert len(ids) == len(set(ids))


def test_every_question_has_required_metadata() -> None:
    for q in QUESTIONS:
        assert q.qid and q.title and q.qtype, q.qid
        assert q.section and q.section_title, q.qid
        assert q.jump.strip(), q.qid
        assert q.analysis.strip(), q.qid
        assert isinstance(q.required, bool), q.qid


def test_choice_questions_have_options() -> None:
    for q in QUESTIONS:
        if q.qtype in ("单选题", "多选题", "量表题", "NPS 评分题"):
            assert q.options, q.qid


def test_anonymity_scan_has_zero_hits() -> None:
    report = validate_questionnaire()
    assert report["sensitive_hits"] == []
    assert report["passed"] is True


def test_satisfaction_and_nps_configuration() -> None:
    report = validate_questionnaire()
    assert report["satisfaction_items"] >= 8
    nps = [q for q in QUESTIONS if q.qid == "B9"]
    assert len(nps) == 1
    assert nps[0].scale == "0–10 分"
    assert "推荐者(9–10)" in nps[0].analysis


def test_questionnaire_payload_serializable() -> None:
    payload = get_questionnaire()
    assert payload["anonymous"] is True
    assert payload["question_count"] == len(QUESTIONS)
    assert sum(len(s["questions"]) for s in payload["sections"]) == len(QUESTIONS)
