# S1-INT-008 · 会员问卷：满意度、NPS 与资源对接诉求

会员空间平台会员问卷交付包。面向约 100 家会员企业对接人的**匿名**问卷，28 题（要求 20–30 题），分 7 个部分 A–G，另设 1 道可选回访意愿题 H，预计填写 ≤ 8 分钟。

## 仓库内容

| 路径 | 说明 |
|---|---|
| `需求原文.md` | 客户需求原文（未改写） |
| `deliverables/` | **主要交付物**：问卷题目文档、可导入题目文件、NPS 计算说明、分析计划、交付清单 |
| `交付物/预览截图/` | 问卷平台样式预览截图（4 张，真实浏览器截取） |
| `src/` | 可运行代码：FastAPI 服务、题目单一数据源、NPS 计算、导入文件生成器、测试与验证脚本 |
| `00_acceptance/验收清单.md` | 验收清单（需求拆解 + 三态标记） |
| `验收报告.md` | 验收报告（证据、风险扫描、结论） |
| `验收结果/` | 本地与服务端的真实执行证据（接口响应、试填计时、匿名扫描、风险扫描） |

## 快速开始

```bash
cd src
python -m pip install -r requirements.txt
python -m scripts.generate_assets      # 重新生成全部交付物
python -m pytest tests -q              # 35 项测试
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
# 浏览器打开 http://127.0.0.1:8000/preview
```

## 交付物清单

- `deliverables/问卷题目文档.md` — 28 题完整定义：题型、选项、是否必填、跳转逻辑、分析方式
- `deliverables/问卷导入_问卷星.txt` — 问卷星文本快速导入格式
- `deliverables/问卷导入_问卷星.xlsx` — 问卷星导入 sheet + 腾讯问卷映射 sheet + 题目元数据 sheet
- `deliverables/问卷导入_通用.csv` — UTF-8-BOM 通用 CSV
- `deliverables/NPS计算说明.md` — 分组规则（推荐者 9–10 / 中立者 7–8 / 贬损者 0–6）、公式、算例、边界
- `deliverables/分析计划.md` — 指标定义、分析步骤、隐私约束
- `交付物/预览截图/` — 整体预览、B 部分、C 部分跳转、试填计时结果

## 验证摘要

- `pytest tests -q` → **35 passed**
- 2 次真实浏览器试填计时：225.5 秒 / 209.1 秒，均 ≤ 480 秒
- 匿名性敏感字段扫描：命中 0
- 13 个证据文件风险信号扫描：命中 0
- 核心接口 health / questionnaire / validate / nps / analysis-plan 均 HTTP 200

## 待客户确认（2 项，均为外部依赖）

1. **真人试填**：需求原文只要求"至少 2 人"，不限身份。任意 2 人试填并回传用时即可闭环。
2. **平台内预览截图**：需腾讯问卷或问卷星免费账号。注册与导入步骤见 `验收报告.md`。

## 技术说明

Python 3.11+ / FastAPI / Pydantic / openpyxl / httpx / pytest / Playwright。配置仅从环境变量读取，依赖工单为"无"，不引入向境外发送数据的 SDK，全部测试数据为虚构，交付物中不含客户名称。

详细对接点、目录结构与运行方法见 `src/README.md`。
