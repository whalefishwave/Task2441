"""FastAPI 服务：会员问卷定义、校验、NPS 计算与预览。

本工单无外部依赖工单（依赖：无），故不涉及数据库/缓存连接；
如后续接入会员中台，对接点见 README。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from . import __version__
from .config import settings
from .nps import calculate_nps, grouping_rule_text
from .questionnaire import get_questionnaire, validate_questionnaire

app = FastAPI(
    title="会员问卷服务 · S1-INT-008",
    description="匿名会员问卷：满意度、NPS 与资源对接诉求",
    version=__version__,
)

STATIC_DIR = Path(__file__).resolve().parent / "static"


class NPSRequest(BaseModel):
    scores: list[int] = Field(..., description="0–10 分的 NPS 打分列表")


@app.get("/api/v1/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "env": settings.app_env,
        "version": __version__,
    }


@app.get("/api/v1/questionnaire")
def questionnaire() -> dict[str, Any]:
    return get_questionnaire()


@app.get("/api/v1/questionnaire/validate")
def questionnaire_validate() -> dict[str, Any]:
    report = validate_questionnaire()
    return JSONResponse(status_code=200 if report["passed"] else 422, content=report)


@app.get("/api/v1/nps/rules")
def nps_rules() -> dict[str, str]:
    return grouping_rule_text()


@app.post("/api/v1/nps/calculate")
def nps_calculate(payload: NPSRequest) -> dict[str, Any]:
    try:
        return calculate_nps(payload.scores)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/v1/analysis-plan")
def analysis_plan() -> dict[str, Any]:
    return {
        "objective": "评估会员空间服务满意度与 NPS，识别资源对接诉求与续约风险",
        "population": "约 100 家会员企业的对接人（匿名）",
        "sampling": "全量邀请，目标回收 ≥ 60 份有效答卷",
        "validity_rules": [
            "作答时长 < 90 秒视为无效答卷",
            "同一 IP/设备重复提交仅保留首份",
            "量表题全部选择同一分值且开放题无内容者标记待复核",
        ],
        "analysis_steps": [
            "描述统计：题量分布、满意度均值/好评率、NPS 分组占比",
            "交叉分析：行业(A1)/规模(A2)/入驻年限(A3) × 满意度、NPS、续约意向",
            "驱动分析：B1–B8 分项满意度与 B9 NPS、F1 续约意向的相关性排序",
            "需求优先级：C1 资源类型、E3 线上办理事项的需求率排序",
            "定性编码：G1/G2 开放题主题归类并摘录代表性原话",
            "输出：月度仪表盘指标 + 改进清单（含责任触点与目标分值）",
        ],
        "indicators": ["整体满意度均值", "各服务项好评率", "NPS", "对接获得率", "数字化需求率", "续约意向率"],
        "privacy": "仅输出聚合结果，最小分组样本 n<5 时不展示交叉表；不收集任何身份与联系方式字段。",
    }


@app.get("/preview", response_class=HTMLResponse)
@app.get("/", response_class=HTMLResponse)
def preview() -> HTMLResponse:
    html_path = STATIC_DIR / "preview.html"
    if not html_path.exists():
        raise HTTPException(status_code=500, detail="预览页面文件缺失")
    return HTMLResponse(html_path.read_text(encoding="utf-8"))
