"""问卷平台导入文件生成器。

产出三类文件：
1. 问卷星文本快速导入（.txt，官方标准标记语法）；
2. 问卷星 Excel 快速导入（.xlsx，官方列 + 元数据 sheet）；
3. 通用 CSV（UTF-8-BOM，可作为腾讯问卷 Excel 导入的字段映射来源）。

平台模板版本可能调整，实际导入前需按平台当前模板核对（见 README「对接点」）。
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from .questionnaire import Question, get_questions

TYPE_MARKERS: dict[str, str] = {
    "单选题": "单选题",
    "多选题": "多选题",
    "量表题": "量表题|1-5分",
    "NPS 评分题": "评分题|0-10分",
    "矩阵量表题": "矩阵量表题|1-5分",
    "多行填空题": "多行填空题",
}


def _option_texts(q: Question) -> list[str]:
    if q.sub_items:
        return list(q.sub_items)
    return list(q.options)


def build_metadata_rows(questions: list[Question] | None = None) -> list[dict[str, Any]]:
    """构造全量元数据行（含题型/选项/必填/跳转/分析方式）。"""
    qs = questions if questions is not None else get_questions()
    rows: list[dict[str, Any]] = []
    for index, q in enumerate(qs, start=1):
        rows.append(
            {
                "题目序号": index,
                "题号": q.qid,
                "所属部分": f"{q.section} {q.section_title}",
                "题目内容": q.title,
                "题型": q.qtype,
                "选项": " | ".join(_option_texts(q)) or "开放式填空（无预设选项）",
                "是否必答": "是" if q.required else "否",
                "跳转逻辑": q.jump,
                "分析方式": q.analysis,
                "量表范围": q.scale,
                "备注": q.note,
            }
        )
    return rows


def build_wenjuanxing_text(questions: list[Question] | None = None) -> str:
    """生成问卷星「文本快速导入」格式（官方标记语法）。"""
    qs = questions if questions is not None else get_questions()
    lines: list[str] = [
        "会员问卷：满意度、NPS 与资源对接诉求",
        "您好，本问卷为匿名调研，不收集企业名称、姓名与任何联系方式，约需 8 分钟，感谢支持。",
        "",
    ]
    for index, q in enumerate(qs, start=1):
        marker = TYPE_MARKERS.get(q.qtype, q.qtype)
        required = "" if q.required else "【非必答】"
        lines.append(f"{index}. {q.title}【{marker}】{required}")
        for opt in _option_texts(q):
            lines.append(f"  {opt}")
        if q.jump != "无条件进入下一题":
            lines.append(f"  （跳转逻辑：{q.jump}）")
        lines.append("")
    return "\n".join(lines)


def _style_header(ws: Any, headers: list[str]) -> None:
    fill = PatternFill("solid", fgColor="D9EAF7")
    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = Font(bold=True)
        cell.fill = fill
        cell.alignment = Alignment(vertical="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(col)].width = 22 if col > 3 else 18
    ws.freeze_panes = "A2"


def write_wenjuanxing_excel(path: str | Path, questions: list[Question] | None = None) -> Path:
    """生成 .xlsx：sheet1 问卷星导入（官方列），sheet2 腾讯问卷导入，sheet3 题目元数据。"""
    qs = questions if questions is not None else get_questions()
    metadata = build_metadata_rows(qs)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    wb = Workbook()

    # Sheet 1：问卷星 Excel 快速导入（官方前四列 + 必答列）
    max_options = max(len(_option_texts(q)) for q in qs)
    headers = ["题目序号", "题目内容", "题型", *[f"选项{i}" for i in range(1, max_options + 1)], "是否必答"]
    ws = wb.active
    ws.title = "问卷星导入"
    _style_header(ws, headers)
    for row_index, q in enumerate(qs, start=2):
        values: list[Any] = [row_index - 1, q.title, TYPE_MARKERS.get(q.qtype, q.qtype)]
        values.extend(_option_texts(q))
        values.extend([""] * (max_options - len(_option_texts(q))))
        values.append("是" if q.required else "否")
        for col, value in enumerate(values, start=1):
            ws.cell(row=row_index, column=col, value=value).alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[row_index].height = 30

    # Sheet 2：腾讯问卷导入（字段映射来源；选项以 | 分隔）
    ws2 = wb.create_sheet("腾讯问卷导入")
    headers2 = ["序号", "题目", "题型", "选项（以 | 分隔）", "必填", "跳转逻辑", "分析方式"]
    _style_header(ws2, headers2)
    for row_index, row in enumerate(metadata, start=2):
        values2 = [
            row["题目序号"], row["题目内容"], row["题型"], row["选项"],
            row["是否必答"], row["跳转逻辑"], row["分析方式"],
        ]
        for col, value in enumerate(values2, start=1):
            ws2.cell(row=row_index, column=col, value=value).alignment = Alignment(wrap_text=True, vertical="top")
        ws2.row_dimensions[row_index].height = 42

    # Sheet 3：完整元数据（每题题型/选项/必填/跳转/分析方式）
    ws3 = wb.create_sheet("题目元数据")
    headers3 = list(metadata[0].keys())
    _style_header(ws3, headers3)
    for row_index, row in enumerate(metadata, start=2):
        for col, key in enumerate(headers3, start=1):
            ws3.cell(row=row_index, column=col, value=row[key]).alignment = Alignment(wrap_text=True, vertical="top")
        ws3.row_dimensions[row_index].height = 42

    wb.save(path)
    return path


def write_csv(path: str | Path, questions: list[Question] | None = None) -> Path:
    """生成 UTF-8-BOM CSV（Excel 与问卷平台均可读，避免中文乱码）。"""
    metadata = build_metadata_rows(questions)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(metadata[0].keys()))
        writer.writeheader()
        writer.writerows(metadata)
    return path


def write_wenjuanxing_text_file(path: str | Path, questions: list[Question] | None = None) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_wenjuanxing_text(questions), encoding="utf-8")
    return path
