"""FastAPI 接口冒烟测试（A7）。"""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from app.main import app  # noqa: E402

client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_questionnaire_endpoint() -> None:
    response = client.get("/api/v1/questionnaire")
    assert response.status_code == 200
    body = response.json()
    assert body["anonymous"] is True
    assert body["question_count"] == 28
    assert len(body["sections"]) == 8


def test_validate_endpoint() -> None:
    response = client.get("/api/v1/questionnaire/validate")
    assert response.status_code == 200
    assert response.json()["passed"] is True
    assert response.json()["sensitive_hits"] == []


def test_nps_rules_endpoint() -> None:
    response = client.get("/api/v1/nps/rules")
    assert response.status_code == 200
    assert "9–10" in response.json()["推荐者"]


def test_nps_calculate_endpoint() -> None:
    # 推荐者 2 人(9,10)、中立者 2 人(7,8)、贬损者 1 人(6) → (2-1)/5×100 = 20
    response = client.post("/api/v1/nps/calculate", json={"scores": [9, 10, 7, 8, 6]})
    assert response.status_code == 200
    body = response.json()
    assert body["sample_size"] == 5
    assert body["nps"] == 20


def test_nps_calculate_rejects_invalid_score() -> None:
    response = client.post("/api/v1/nps/calculate", json={"scores": [9, 11]})
    assert response.status_code == 422


def test_analysis_plan_endpoint() -> None:
    response = client.get("/api/v1/analysis-plan")
    assert response.status_code == 200
    assert "privacy" in response.json()


def test_preview_page() -> None:
    response = client.get("/preview")
    assert response.status_code == 200
    assert "questionnaire-data" in response.text
    assert "开始试填" in response.text
