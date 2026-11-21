"""生成全部交付物（单一数据源：app.questionnaire）。

运行：python -m scripts.generate_assets
产出目录：交付物/
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from app.config import settings  # noqa: E402
from app.exporters import (  # noqa: E402
    build_metadata_rows,
    write_csv,
    write_wenjuanxing_excel,
    write_wenjuanxing_text_file,
)
from app.nps import grouping_rule_text  # noqa: E402
from app.questionnaire import (  # noqa: E402
    SECTIONS,
    QUESTIONS,
    get_questionnaire,
    validate_questionnaire,
)


def _out() -> Path:
    path = ROOT / settings.output_dir
    path.mkdir(parents=True, exist_ok=True)
    return path


def generate_preview_html() -> Path:
    template = ROOT / "src" / "app" / "static" / "preview_template.html"
    html = template.read_text(encoding="utf-8")
    payload = json.dumps(get_questionnaire(), ensure_ascii=False).replace("</script>", "<\\/script>")
    html = html.replace("__QUESTIONNAIRE_JSON__", payload)
    target = ROOT / "src" / "app" / "static" / "preview.html"
    target.write_text(html, encoding="utf-8")
    return target


def generate_question_document(out: Path) -> Path:
    lines: list[str] = [
        "# 会员问卷题目文档 · S1-INT-008",
        "",
        "> 会员空间平台 · 会员问卷：满意度、NPS 与资源对接诉求",
        "> 版本 1.0.0　|　生成自结构化题目定义（单一数据源：`src/app/questionnaire.py`）",
        "",
        "## 一、问卷说明",
        "",
        "- **匿名承诺**：本问卷不收集企业名称、姓名与任何联系方式；回访意愿题仅表达意愿，由会员经理按既有会员档案线下联系。",
        "- **作答对象**：约 100 家会员企业的对接人。",
        f"- **题量**：{len(QUESTIONS)} 题（要求 20–30 题），分 7 个部分 A–G，另设 1 道可选回访意愿题 H。",
        "- **预计用时**：≤ 8 分钟（以 2 次真实浏览器试填计时验证，见验收报告）。",
        "- **数据用途**：仅用于聚合分析，最小分组样本 n<5 时不展示交叉表。",
        "- **测试数据**：全部为虚构数据，不含任何真实个人或企业信息，文档中不出现客户名称。",
        "",
        "## 二、题目总览",
        "",
        "| 部分 | 主题 | 题数 | 题号 |",
        "|---|---|---|---|",
    ]
    for code, title in SECTIONS:
        qids = [q.qid for q in QUESTIONS if q.section == code]
        lines.append(f"| {code} | {title} | {len(qids)} | {', '.join(qids)} |")
    lines.extend([
        f"| **合计** | — | **{len(QUESTIONS)}** | — |",
        "",
        "## 三、题目明细",
        "",
        "> 每题均标注：题型、选项、是否必填、跳转逻辑、分析方式。",
        "",
    ])

    for code, title in SECTIONS:
        lines.extend([f"### {code} · {title}", ""])
        for index, q in enumerate([q for q in QUESTIONS if q.section == code], start=1):
            lines.extend([
                f"#### {q.qid}　{q.title}",
                "",
                f"- **题型**：{q.qtype}" + (f"（{q.scale}）" if q.scale else ""),
                f"- **选项**：" + ("；".join(q.options) if q.options else "开放式填空，无预设选项"),
            ])
            if q.sub_items:
                lines.append(f"- **矩阵子项**：{'；'.join(q.sub_items)}")
            lines.extend([
                f"- **是否必填**：{'是' if q.required else '否（选填）'}",
                f"- **跳转逻辑**：{q.jump}",
                f"- **分析方式**：{q.analysis}",
            ])
            if q.note:
                lines.append(f"- **说明**：{q.note}")
            lines.append("")
        lines.append("---")
        lines.append("")

    lines.extend([
        "## 四、匿名性自查",
        "",
        "问卷字段、题干、选项与说明中不含：企业名称/公司名称、姓名、联系人、手机号、电话、邮箱、微信/微信号、",
        "通讯地址、身份证号、营业执照号。仅采集行业、规模区间、入驻年限区间、办公人数区间等聚合画像字段。",
        "自动扫描结果见 `验收结果/本地验证/A3_anonymity_scan.json`。",
        "",
        "## 五、可导入文件",
        "",
        "| 文件 | 用途 |",
        "|---|---|",
        "| `问卷导入_问卷星.txt` | 问卷星「文本快速导入」格式（官方标记语法） |",
        "| `问卷导入_问卷星.xlsx` | 问卷星 Excel 导入 sheet + 腾讯问卷导入 sheet + 题目元数据 sheet |",
        "| `问卷导入_通用.csv` | UTF-8-BOM 通用 CSV，字段映射来源 |",
        "",
        "导入平台后请按本文件逐题核对题型、必填与跳转逻辑。平台模板若调整，需按当前模板映射列。",
        "预览截图见 `交付物/预览截图/`。",
    ])
    target = out / "问卷题目文档.md"
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def generate_nps_doc(out: Path) -> Path:
    rule = grouping_rule_text()
    lines = [
        "# NPS 计算说明 · S1-INT-008",
        "",
        "> 对应问卷 B9 题：「您有多大可能将本空间推荐给其他企业？」（0–10 分，必答）",
        "",
        "## 一、分组规则",
        "",
        "| 分组 | 分值范围 | 含义 |",
        "|---|---|---|",
        f"| 推荐者 Promoter | 9–10 分 | {rule['推荐者']} |",
        f"| 中立者 Passive | 7–8 分 | {rule['中立者']} |",
        f"| 贬损者 Detractor | 0–6 分 | {rule['贬损者']} |",
        "",
        "## 二、计算公式",
        "",
        "```text",
        "NPS = 推荐者占比(%) − 贬损者占比(%)",
        "    = (推荐者人数 − 贬损者人数) / 有效答卷数 × 100",
        "```",
        "",
        f"- 取值范围：{rule['取值范围']}。",
        "- 中立者计入分母（有效答卷数），但不计入分子。",
        "- 结果按四舍五入取整数（ROUND_HALF_UP，避免银行家舍入造成的偏差）。",
        "- 无效答卷（作答时长 < 90 秒、重复提交）在计算前剔除；有效答卷数为 0 时不输出 NPS。",
        "",
        "## 三、算例",
        "",
        "假设回收 100 份有效答卷：推荐者 45 人、中立者 35 人、贬损者 20 人。",
        "",
        "```text",
        "推荐者占比 = 45 / 100 × 100 = 45%",
        "贬损者占比 = 20 / 100 × 100 = 20%",
        "NPS = 45 − 20 = +25",
        "```",
        "",
        "边界校验（由 `src/app/nps.py` 自动化测试覆盖）：",
        "",
        "| 输入分数 | 分组 | 说明 |",
        "|---|---|---|",
        "| 0 / 6 | 贬损者 | 区间下界与上界 |",
        "| 7 / 8 | 中立者 | 区间下界与上界 |",
        "| 9 / 10 | 推荐者 | 区间下界与上界 |",
        "| 空列表 | 不计算 | 返回 nps=null，避免除零 |",
        "| 非整数 / 越界 | 拒绝 | 返回 422 校验错误 |",
        "",
        "## 四、分析口径",
        "",
        "1. 总览：整体 NPS + 三组占比，按月对比趋势。",
        "2. 分层：按行业(A1)、员工规模(A2)、入驻年限(A3)分组计算 NPS；n<5 不展示。",
        "3. 驱动：将 B1–B8 满意度均值与 B9 做相关分析，定位对 NPS 影响最大的服务项。",
        "4. 闭环：贬损者样本结合 F2 续约影响因素与 G1/G2 开放题文本，形成改进清单。",
        "",
        "## 五、接口",
        "",
        "- `GET /api/v1/nps/rules`：分组规则与公式。",
        "- `POST /api/v1/nps/calculate`：请求体 `{\"scores\": [9,10,7,6,...]}`，返回分组计数、占比与 NPS。",
        "",
        "实现代码：`src/app/nps.py`；单元测试：`src/tests/test_nps.py`。",
    ]
    target = out / "NPS计算说明.md"
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def generate_analysis_plan(out: Path) -> Path:
    lines = [
        "# 分析计划 · S1-INT-008",
        "",
        "> 会员问卷：满意度、NPS 与资源对接诉求　|　面向约 100 家会员企业对接人（匿名）",
        "",
        "## 一、研究目标",
        "",
        "1. 量化会员空间整体服务满意度与 NPS 基线，形成可持续追踪的仪表盘指标。",
        "2. 识别 8 项服务触点中拉低满意度与 NPS 的关键短板。",
        "3. 摸清会员对资源对接、活动内容和数字化办理的需求优先级。",
        "4. 评估续约意向并定位流失风险因素，输出可执行的改进清单。",
        "",
        "## 二、数据采集与有效性",
        "",
        "- 目标样本：约 100 家会员企业，每家 1 名对接人；目标回收 ≥ 60 份有效答卷。",
        "- 无效答卷规则：作答时长 < 90 秒；同设备/IP 重复提交仅保留首份；量表全同分且开放题空白者标记待复核。",
        "- 匿名约束：不采集企业/个人标识与联系方式，无法按答卷追溯具体企业；分层分析仅使用画像区间字段。",
        "",
        "## 三、指标定义",
        "",
        "| 指标 | 定义 | 数据来源 |",
        "|---|---|---|",
        "| 分项满意度均值 | 各服务项 1–5 分算术平均 | B1–B8 |",
        "| 好评率 | 该项 4–5 分占比 | B1–B8 |",
        "| NPS | 推荐者占比 − 贬损者占比 | B9 |",
        "| 对接获得率 | C2=“是”的占比 | C2 |",
        "| 对接有效率 | C3 中“很有帮助+有帮助”占 C2=“是”的比例 | C2/C3 |",
        "| 数字化使用率 | E1“经常+偶尔”占比 | E1 |",
        "| 数字化需求率 | E3 各事项选择率 | E3 |",
        "| 续约意向率 | F1“肯定+可能”占比 | F1 |",
        "",
        "## 四、分析步骤",
        "",
        "| 阶段 | 方法 | 产出 |",
        "|---|---|---|",
        "| 1 描述统计 | 频数/百分比、均值、标准差、好评率 | 问卷总览表 |",
        "| 2 交叉分析 | 行业(A1)/规模(A2)/入驻年限(A3) × 满意度、NPS、续约意向 | 分层对比表（n<5 不外显） |",
        "| 3 驱动分析 | B1–B8 均值与 B9、F1 的相关性排序 | 关键驱动Top5 |",
        "| 4 需求优先级 | C1、D2、D3、E3 选择率排序 | 资源/活动/数字化排期清单 |",
        "| 5 定性编码 | G1/G2 文本主题归类（设施/服务/社群/数字化/价格/其他） | 主题频次 + 代表性原话 |",
        "| 6 行动建议 | 短板项 → 责任触点 → 目标分值 → 复测时间 | 改进清单与复测计划 |",
        "",
        "## 五、跳转逻辑对分析的影响",
        "",
        "- C3 仅 C2=“是”者作答：对接有效率分母为 C2=“是”人数，不可使用全体样本。",
        "- E2 仅小程序使用者作答：功能使用率分母为 E1“经常+偶尔”人数。",
        "- 统计时选项未展示即视为“不适用”，与“未作答”区分处理。",
        "",
        "## 六、隐私与合规",
        "",
        "- 仅输出聚合结果；最小分组 n<5 不展示，避免间接识别。",
        "- 不采集任何身份与联系方式字段；原始答卷不含可直接定位企业的信息。",
        "- 交付测试数据全部为虚构；不引入向境外发送数据的第三方 SDK。",
        "",
        "## 七、交付节奏",
        "",
        "1. 问卷定稿与平台导入（本次交付）。",
        "2. 试填计时与题目修正（本次交付 2 次试填证据）。",
        "3. 投放与回收（客户执行）。",
        "4. 数据清洗 → 指标计算 → 报告输出（可按回收数据复用本计划的指标定义）。",
    ]
    target = out / "分析计划.md"
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def generate_delivery_manifest(out: Path) -> Path:
    metadata = build_metadata_rows()
    report = validate_questionnaire()
    lines = [
        "# 交付清单 · S1-INT-008",
        "",
        f"- 问卷题目数：{report['question_count']}（要求 20–30）",
        f"- 部分数：{report['section_count']}（A–G + H 回访意愿）",
        f"- 满意度服务项：{report['satisfaction_items']}（要求 ≥ 8，1–5 分）",
        f"- NPS 量表：0–10 分，分组与公式见 NPS计算说明.md",
        f"- 匿名性扫描命中：{len(report['sensitive_hits'])}（要求 0）",
        f"- 结构校验：{'通过' if report['passed'] else '未通过'}",
        "",
        "## 文件清单",
        "",
        "| 文件 | 类型 | 说明 |",
        "|---|---|---|",
        "| 问卷题目文档.md | 文档 | 28 题完整定义（题型/选项/必填/跳转/分析方式） |",
        "| 问卷导入_问卷星.txt | 导入文件 | 问卷星文本快速导入 |",
        "| 问卷导入_问卷星.xlsx | 导入文件 | 问卷星 Excel + 腾讯问卷映射 + 元数据 |",
        "| 问卷导入_通用.csv | 导入文件 | UTF-8-BOM 通用 CSV |",
        "| NPS计算说明.md | 文档 | 分组规则、公式、算例、边界 |",
        "| 分析计划.md | 文档 | 指标定义、分析步骤、隐私约束 |",
        "| 预览截图/*.png | 截图 | 问卷平台样式预览与试填计时结果 |",
        "",
        "## 题目序号映射",
        "",
        "| 序号 | 题号 | 题型 | 必填 |",
        "|---|---|---|---|",
    ]
    for row in metadata:
        lines.append(f"| {row['题目序号']} | {row['题号']} | {row['题型']} | {row['是否必答']} |")
    target = out / "交付清单.md"
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def main() -> None:
    out = _out()
    produced = [
        generate_preview_html(),
        generate_question_document(out),
        generate_nps_doc(out),
        generate_analysis_plan(out),
        generate_delivery_manifest(out),
        write_wenjuanxing_text_file(out / "问卷导入_问卷星.txt"),
        write_wenjuanxing_excel(out / "问卷导入_问卷星.xlsx"),
        write_csv(out / "问卷导入_通用.csv"),
    ]
    for item in produced:
        print(f"generated: {item} ({item.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
