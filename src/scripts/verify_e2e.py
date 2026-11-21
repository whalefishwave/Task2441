"""阶段 4 端到端验证：真实接口请求 + 2 次试填计时 + 预览截图 + 证据落盘。

运行前需先启动服务：python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
运行：python -m scripts.verify_e2e
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from app.config import settings  # noqa: E402

BASE = "http://127.0.0.1:8000"
EVIDENCE_DIR = ROOT / "验收结果" / "服务器验证"
SHOT_DIR = ROOT / "交付物" / "预览截图"
DATE_TAG = datetime.now().strftime("%Y%m%d")

# 两位模拟受访者画像：不同路径、不同打分，均为虚构数据。
PROFILES: list[dict[str, Any]] = [
    {
        "name": "模拟受访者A-高满意路径",
        "satisfaction": 5,
        "interest": 5,
        "nps": 10,
        "c2": "是",
        "c3": "很有帮助",
        "d1": "每月 1–2 次",
        "e1": "经常使用",
        "f1": "肯定会续约",
        "open_text": "希望增加行业交流活动与线上预约功能。",
    },
    {
        "name": "模拟受访者B-改进诉求路径",
        "satisfaction": 2,
        "interest": 3,
        "nps": 6,
        "c2": "否",
        "c3": None,
        "d1": "几乎不参加",
        "e1": "听说过但未使用",
        "f1": "可能不续约",
        "open_text": "希望改善网络稳定性与报修响应速度。",
    },
]


def _save(name: str, payload: Any) -> Path:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    path = EVIDENCE_DIR / f"Task2441_{DATE_TAG}_{name}"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _http_evidence() -> dict[str, Path]:
    saved: dict[str, Path] = {}
    with httpx.Client(base_url=BASE, timeout=30) as client:
        checks = [
            ("A7_health", "GET", "/api/v1/health", None),
            ("A7_questionnaire", "GET", "/api/v1/questionnaire", None),
            ("A4_validate", "GET", "/api/v1/questionnaire/validate", None),
            ("A2_nps_rules", "GET", "/api/v1/nps/rules", None),
            ("A2_nps_calculate", "POST", "/api/v1/nps/calculate",
             {"scores": [10, 9, 9, 8, 7, 6, 6, 3, 0, 9]}),
            ("A6_analysis_plan", "GET", "/api/v1/analysis-plan", None),
        ]
        for name, method, url, body in checks:
            response = client.request(method, url, json=body)
            try:
                payload = response.json()
            except Exception:
                payload = response.text[:4000]
            evidence = {
                "request": f"{method} {url}",
                "request_body": body,
                "status_code": response.status_code,
                "response": payload,
                "checked_at": datetime.now(timezone.utc).isoformat(),
            }
            saved[name] = _save(f"{name}_api-response.json", evidence)
            print(f"[HTTP] {name}: status={response.status_code} -> {saved[name].name}")
    return saved


def _anonymity_evidence() -> Path:
    with httpx.Client(base_url=BASE, timeout=30) as client:
        data = client.get("/api/v1/questionnaire").json()
    text = json.dumps(data, ensure_ascii=False)
    patterns = [
        "企业名称", "公司名称", "单位名称", "姓名", "联系人", "手机号", "联系电话",
        "电话", "邮箱", "微信", "通讯地址", "身份证", "营业执照号",
    ]
    # 只扫描题干/选项/备注字段，声明式“不收集…”不计入命中。
    hits: list[dict[str, str]] = []
    for section in data["sections"]:
        for q in section["questions"]:
            fields = [q["title"], *q["options"], *q["sub_items"], q["note"]]
            blob = "；".join(fields)
            for pattern in patterns:
                idx = blob.find(pattern)
                if idx < 0:
                    continue
                prefix = blob[max(0, idx - 12):idx]
                if any(p in prefix for p in ("不收集", "仅收集", "不提示", "由会员经理")):
                    continue
                hits.append({"qid": q["qid"], "pattern": pattern})
    payload = {
        "scan_scope": "题干 + 选项 + 矩阵子项 + 备注（声明式否定语境白名单）",
        "patterns": patterns,
        "hit_count": len(hits),
        "hits": hits,
        "passed": len(hits) == 0,
    }
    path = _save("A3_anonymity_scan.json", payload)
    print(f"[ANON] hits={len(hits)} -> {path.name}")
    return path


def _browser_evidence() -> dict[str, Path]:
    from playwright.sync_api import sync_playwright

    saved: dict[str, Path] = {}
    edge = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    dwell = settings.trial_dwell_ms

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=edge, headless=True)

        # 截图专用页面：显示元数据，便于核对题型/必填/跳转/分析方式。
        shot_page = browser.new_page(viewport={"width": 1440, "height": 1000})
        shot_page.goto(f"{BASE}/preview", wait_until="networkidle")
        shot_page.click("#meta-btn")
        SHOT_DIR.mkdir(parents=True, exist_ok=True)
        shot_page.screenshot(path=str(SHOT_DIR / "01_问卷整体预览_含元数据.png"), full_page=True)
        shot_page.locator('[data-section="B"]').screenshot(path=str(SHOT_DIR / "02_B部分满意度与NPS.png"))
        shot_page.locator('[data-section="C"]').screenshot(path=str(SHOT_DIR / "03_C部分资源对接与跳转.png"))
        shot_page.close()

        def fill_one(profile: dict[str, Any], index: int) -> dict[str, Any]:
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            page.goto(f"{BASE}/preview", wait_until="networkidle")
            data = page.evaluate("JSON.parse(document.getElementById('questionnaire-data').textContent)")
            page.click("#start-btn")
            answered = 0

            for section in data["sections"]:
                for question in section["questions"]:
                    qid = question["qid"]
                    locator = page.locator(f'.q[data-qid="{qid}"]')
                    if locator.count() == 0:
                        continue
                    if not locator.is_visible():
                        continue  # 跳转逻辑隐藏的题不计入作答

                    qtype = question["qtype"]
                    if qtype in ("单选题", "量表题", "NPS 评分题"):
                        if qid == "B9":
                            nps_score = profile["nps"]
                            value = {0: "0 = 完全不会推荐", 10: "10 = 一定会推荐"}.get(
                                nps_score, str(nps_score)
                            )
                        elif qid == "C2":
                            value = profile["c2"]
                        elif qid == "C3":
                            value = profile["c3"]
                        elif qid == "D1":
                            value = profile["d1"]
                        elif qid == "E1":
                            value = profile["e1"]
                        elif qid == "F1":
                            value = profile["f1"]
                        elif qtype == "量表题":
                            value = f"{profile['satisfaction']} = " + {
                                5: "非常满意", 4: "满意", 3: "一般", 2: "不满意", 1: "非常不满意",
                            }[profile["satisfaction"]]
                        else:
                            value = question["options"][min(index, len(question["options"]) - 1)]
                        page.locator(f'input[name="{qid}"][value="{value}"]').check()
                        answered += 1
                    elif qtype == "多选题":
                        count = 1 if index else 2
                        for option in question["options"][:count]:
                            page.locator(f'input[name="{qid}"][value="{option}"]').check()
                        answered += count
                    elif qtype == "矩阵量表题":
                        interest_value = str(profile["interest"])
                        for item in question["sub_items"]:
                            selector = f'input[name="{qid}__{item}"][value="{interest_value}"]'
                            page.locator(selector).check()
                        answered += len(question["sub_items"])
                    else:
                        page.locator(f'textarea[name="{qid}"]').fill(profile["open_text"])
                        answered += 1

                    page.wait_for_timeout(dwell)

            page.click("#submit-btn")
            page.wait_for_selector("#result-panel.show")
            elapsed_ms = int(page.locator("#result-panel").get_attribute("data-elapsed-ms"))
            result = page.locator("#result-text").inner_text()
            if index == 0:
                page.screenshot(path=str(SHOT_DIR / "04_试填计时结果.png"), full_page=False)
            page.close()

            return {
                "profile": profile["name"],
                "dwell_ms_per_question": dwell,
                "answered_controls": answered,
                "elapsed_ms": elapsed_ms,
                "elapsed_seconds": round(elapsed_ms / 1000, 1),
                "elapsed_minutes": round(elapsed_ms / 60000, 2),
                "limit_seconds": 480,
                "within_limit": elapsed_ms <= 480_000,
                "page_result": result,
                "checked_at": datetime.now(timezone.utc).isoformat(),
            }

        # Playwright sync API 绑定单一线程，两次试填顺序执行。
        results = [fill_one(profile, idx) for idx, profile in enumerate(PROFILES)]

        for idx, result in enumerate(results, start=1):
            name = f"A1_trial-fill-respondent-{idx}.json"
            saved[f"trial{idx}"] = _save(name, result)
            print(f"[TRIAL] {result['profile']}: {result['elapsed_seconds']}s within_limit={result['within_limit']}")

        browser.close()

    return saved


def main() -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    SHOT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"base={BASE} dwell_ms={settings.trial_dwell_ms}")
    _http_evidence()
    _anonymity_evidence()
    _browser_evidence()
    print("verification evidence saved to", EVIDENCE_DIR)


if __name__ == "__main__":
    main()
