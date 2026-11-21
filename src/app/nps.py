"""NPS（净推荐值）分组规则与计算。

分组规则（客户需求原文要求写明）：
- 推荐者 Promoter：9–10 分
- 中立者 Passive ：7–8 分
- 贬损者 Detractor：0–6 分

计算公式：
    NPS = 推荐者占比(%) − 贬损者占比(%)
        = (推荐者人数 − 贬损者人数) / 有效答卷数 × 100
结果按四舍五入取整数（ROUND_HALF_UP）。中立者计入分母但不计入分子。
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any

PROMOTER_MIN = 9
PASSIVE_MIN = 7
SCORE_MIN = 0
SCORE_MAX = 10

CATEGORY_PROMOTER = "推荐者"
CATEGORY_PASSIVE = "中立者"
CATEGORY_DETRACTOR = "贬损者"


def nps_category(score: int) -> str:
    """将 0–10 分映射为推荐者/中立者/贬损者。"""
    if isinstance(score, bool) or not isinstance(score, int):
        raise ValueError(f"NPS 分数必须为整数，收到 {score!r}")
    if not SCORE_MIN <= score <= SCORE_MAX:
        raise ValueError(f"NPS 分数必须在 0–10 之间，收到 {score}")
    if score >= PROMOTER_MIN:
        return CATEGORY_PROMOTER
    if score >= PASSIVE_MIN:
        return CATEGORY_PASSIVE
    return CATEGORY_DETRACTOR


def _round_half_up(value: Decimal) -> int:
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def calculate_nps(scores: list[int]) -> dict[str, Any]:
    """根据一组 0–10 分计算 NPS 与分组统计。

    空样本时返回 nps=None，避免除零；调用方应提示样本不足。
    """
    if not isinstance(scores, list):
        raise ValueError("scores 必须为整数列表")

    counts = {
        CATEGORY_PROMOTER: 0,
        CATEGORY_PASSIVE: 0,
        CATEGORY_DETRACTOR: 0,
    }
    for score in scores:
        counts[nps_category(score)] += 1

    total = len(scores)
    if total == 0:
        return {
            "sample_size": 0,
            "counts": counts,
            "percentages": {k: 0.0 for k in counts},
            "nps": None,
            "formula": "NPS = 推荐者占比 − 贬损者占比（空样本不计算）",
            "note": "有效答卷数为 0，NPS 不可计算。",
        }

    promoter_pct = Decimal(counts[CATEGORY_PROMOTER] * 100) / Decimal(total)
    passive_pct = Decimal(counts[CATEGORY_PASSIVE] * 100) / Decimal(total)
    detractor_pct = Decimal(counts[CATEGORY_DETRACTOR] * 100) / Decimal(total)
    nps_value = _round_half_up(promoter_pct - detractor_pct)

    return {
        "sample_size": total,
        "counts": counts,
        "percentages": {
            CATEGORY_PROMOTER: float(promoter_pct.quantize(Decimal("0.01"))),
            CATEGORY_PASSIVE: float(passive_pct.quantize(Decimal("0.01"))),
            CATEGORY_DETRACTOR: float(detractor_pct.quantize(Decimal("0.01"))),
        },
        "nps": nps_value,
        "formula": "NPS = 推荐者占比(%) − 贬损者占比(%) = (推荐者数 − 贬损者数) / 有效答卷数 × 100",
        "note": "按 ROUND_HALF_UP 四舍五入取整数；中立者计入分母不计入分子。",
    }


def grouping_rule_text() -> dict[str, str]:
    """返回可直接写入文档的分组规则说明。"""
    return {
        "推荐者": "9–10 分：高度满意，愿意主动推荐",
        "中立者": "7–8 分：基本满意，但不主动推荐",
        "贬损者": "0–6 分：不满意，可能负面传播",
        "公式": "NPS = (推荐者数 − 贬损者数) ÷ 有效答卷数 × 100，四舍五入取整数",
        "取值范围": "-100 至 +100",
    }
