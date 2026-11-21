"""NPS 分组边界、公式与异常处理测试（A2）。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from app.nps import (  # noqa: E402
    CATEGORY_DETRACTOR,
    CATEGORY_PASSIVE,
    CATEGORY_PROMOTER,
    calculate_nps,
    grouping_rule_text,
    nps_category,
)


@pytest.mark.parametrize("score,expected", [
    (0, CATEGORY_DETRACTOR),
    (6, CATEGORY_DETRACTOR),
    (7, CATEGORY_PASSIVE),
    (8, CATEGORY_PASSIVE),
    (9, CATEGORY_PROMOTER),
    (10, CATEGORY_PROMOTER),
])
def test_grouping_boundaries(score: int, expected: str) -> None:
    assert nps_category(score) == expected


@pytest.mark.parametrize("score", [-1, 11])
def test_out_of_range_rejected(score: int) -> None:
    with pytest.raises(ValueError):
        nps_category(score)


def test_invalid_type_rejected() -> None:
    with pytest.raises(ValueError):
        nps_category("9")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        nps_category(True)  # type: ignore[arg-type]


def test_nps_formula_typical() -> None:
    scores = [9, 10] * 45 + [7, 8] * 17 + [6, 0] * 10  # 90 promoters, 34 passives, 20 detractors
    result = calculate_nps(scores)
    assert result["sample_size"] == 144
    assert result["counts"][CATEGORY_PROMOTER] == 90
    assert result["counts"][CATEGORY_PASSIVE] == 34
    assert result["counts"][CATEGORY_DETRACTOR] == 20
    expected = round((90 - 20) / 144 * 100)
    assert result["nps"] == expected


def test_nps_round_half_up() -> None:
    # 推荐者 1、贬损者 0、样本 8 → 12.5%，ROUND_HALF_UP 应为 13（而非银行家舍入 12）
    result = calculate_nps([9] + [7] * 7)
    assert result["nps"] == 13


def test_nps_all_promoters_all_detractors() -> None:
    assert calculate_nps([9, 10, 10])["nps"] == 100
    assert calculate_nps([0, 6, 6])["nps"] == -100


def test_nps_empty_sample() -> None:
    result = calculate_nps([])
    assert result["sample_size"] == 0
    assert result["nps"] is None


def test_percentages_sum_about_100() -> None:
    result = calculate_nps([10, 8, 5, 9, 7, 3, 10, 6])
    assert abs(sum(result["percentages"].values()) - 100.0) < 0.05


def test_grouping_rule_text_contains_formula() -> None:
    rule = grouping_rule_text()
    assert "9–10" in rule["推荐者"]
    assert "7–8" in rule["中立者"]
    assert "0–6" in rule["贬损者"]
    assert "NPS" in rule["公式"]
