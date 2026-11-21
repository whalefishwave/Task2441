"""证据收尾：截图归档、文件非空检查、风险信号扫描（阶段 4/4.5）。

运行：python -m scripts.finalize_evidence
"""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SERVER_DIR = ROOT / "验收结果" / "服务器验证"
LOCAL_DIR = ROOT / "验收结果" / "本地验证"
SHOT_DIR = ROOT / "交付物" / "预览截图"
DATE_TAG = datetime.now().strftime("%Y%m%d")

RISK_PATTERN = re.compile(r"warning|fatal|error|fail|缺失|遗漏", re.IGNORECASE)
SCAN_COMMAND = 'grep -inE "warning|fatal|error|fail|缺失|遗漏" <结果文件>'

SHOT_MAP = {
    "01_问卷整体预览_含元数据.png": f"Task2441_{DATE_TAG}_A4_preview-full.png",
    "02_B部分满意度与NPS.png": f"Task2441_{DATE_TAG}_A4_preview-section-b.png",
    "03_C部分资源对接与跳转.png": f"Task2441_{DATE_TAG}_A4_preview-section-c.png",
    "04_试填计时结果.png": f"Task2441_{DATE_TAG}_A1_trial-fill-result.png",
}


def archive_screenshots() -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    SERVER_DIR.mkdir(parents=True, exist_ok=True)
    for source_name, target_name in SHOT_MAP.items():
        source = SHOT_DIR / source_name
        target = SERVER_DIR / target_name
        if not source.exists():
            records.append({"source": source_name, "target": target_name, "status": "源文件缺失"})
            continue
        shutil.copy2(source, target)
        records.append({
            "source": source_name,
            "target": target_name,
            "status": "已归档" if target.stat().st_size > 0 else "归档文件为空",
        })
    return records


def scan_all() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for path in sorted(SERVER_DIR.iterdir()):
        if not path.is_file():
            continue
        if path.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp", ".gif", ".pdf"):
            results.append({
                "file": path.name,
                "scan_command": "跳过（二进制文件）",
                "signal": None,
                "hit_count": 0,
                "hit_lines": [],
                "size_bytes": path.stat().st_size,
            })
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        hits = [
            {"line": index, "content": line.strip()[:300]}
            for index, line in enumerate(text.splitlines(), start=1)
            if RISK_PATTERN.search(line)
        ]
        results.append({
            "file": path.name,
            "scan_command": SCAN_COMMAND,
            "signal": ", ".join(sorted({m.group(0).lower() for line in hits for m in RISK_PATTERN.finditer(line["content"])})) or None,
            "hit_count": len(hits),
            "hit_lines": hits,
            "size_bytes": path.stat().st_size,
        })
    return results


def main() -> None:
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    archived = archive_screenshots()
    scans = scan_all()
    payload = {
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "scan_command_batch": 'grep -rinE "warning|fatal|error|fail|缺失|遗漏" 验收结果/服务器验证/',
        "screenshot_archive": archived,
        "files_scanned": len(scans),
        "total_hits": sum(item["hit_count"] for item in scans),
        "details": scans,
        "passed": all(item["hit_count"] == 0 and item["size_bytes"] > 0 for item in scans),
    }
    path = LOCAL_DIR / "risk_signal_scan.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"archived screenshots: {len(archived)}")
    print(f"files scanned: {payload['files_scanned']}, total risk hits: {payload['total_hits']}")
    print(f"report: {path}")


if __name__ == "__main__":
    main()
