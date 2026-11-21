"""导入文件生成与读回校验测试（A5）。"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from app.exporters import (  # noqa: E402
    build_metadata_rows,
    build_wenjuanxing_text,
    write_csv,
    write_wenjuanxing_excel,
    write_wenjuanxing_text_file,
)
from app.questionnaire import QUESTIONS  # noqa: E402


def test_metadata_rows_complete(tmp_path: Path) -> None:
    rows = build_metadata_rows()
    assert len(rows) == len(QUESTIONS)
    required = ["题目序号", "题号", "题目内容", "题型", "选项", "是否必答", "跳转逻辑", "分析方式"]
    for row in rows:
        for key in required:
            assert str(row[key]).strip(), (row["题号"], key)


def test_text_import_format(tmp_path: Path) -> None:
    text = build_wenjuanxing_text()
    assert "【单选题】" in text
    assert "【多选题】" in text
    assert "【量表题|1-5分】" in text
    assert "【评分题|0-10分】" in text
    assert "【多行填空题】" in text
    path = write_wenjuanxing_text_file(tmp_path / "q.txt")
    assert path.read_text(encoding="utf-8") == text


def test_excel_readback(tmp_path: Path) -> None:
    path = write_wenjuanxing_excel(tmp_path / "q.xlsx")
    wb = load_workbook(path)
    assert wb.sheetnames == ["问卷星导入", "腾讯问卷导入", "题目元数据"]
    ws = wb["问卷星导入"]
    assert ws.max_row == len(QUESTIONS) + 1
    assert ws.cell(row=1, column=1).value == "题目序号"
    assert ws.cell(row=2, column=2).value == QUESTIONS[0].title
    meta = wb["题目元数据"]
    headers = [meta.cell(row=1, column=c).value for c in range(1, meta.max_column + 1)]
    for key in ("题型", "选项", "是否必答", "跳转逻辑", "分析方式"):
        assert key in headers


def test_csv_readback(tmp_path: Path) -> None:
    path = write_csv(tmp_path / "q.csv")
    with open(path, encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == len(QUESTIONS)
    assert rows[0]["题号"] == "A1"
    assert rows[-1]["题号"] == "H1"
