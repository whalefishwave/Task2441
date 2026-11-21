"""问卷题目结构化定义。

S1-INT-008 · 会员问卷：满意度、NPS 与资源对接诉求。

设计约束（来自客户需求原文）：
- 匿名问卷：不收集企业名称、姓名与任何联系方式；
- 题量 20–30 题，7 个部分 A–G，另设 1 道可选回访意愿题；
- 每题写明题型、选项、是否必填、跳转逻辑与分析方式。

全部测试数据均为虚构，不含任何真实个人或企业信息，亦不出现客户名称。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

# 满意度量表统一锚点（1–5 分）
SATISFACTION_SCALE: tuple[str, ...] = (
    "1 = 非常不满意",
    "2 = 不满意",
    "3 = 一般",
    "4 = 满意",
    "5 = 非常满意",
)

# 内容兴趣量表锚点（1–5 分）
INTEREST_SCALE: tuple[str, ...] = (
    "1 = 完全不感兴趣",
    "2 = 不太感兴趣",
    "3 = 一般",
    "4 = 比较感兴趣",
    "5 = 非常感兴趣",
)

# NPS 量表锚点（0–10 分）
NPS_SCALE: tuple[str, ...] = (
    "0 = 完全不会推荐",
    "1",
    "2",
    "3",
    "4",
    "5 = 中立",
    "6",
    "7",
    "8",
    "9",
    "10 = 一定会推荐",
)


@dataclass(frozen=True)
class Question:
    """单道题目的完整定义与元数据。"""

    qid: str
    section: str
    section_title: str
    title: str
    qtype: str
    options: tuple[str, ...] = ()
    required: bool = True
    jump: str = "无条件进入下一题"
    analysis: str = ""
    scale: str = ""
    sub_items: tuple[str, ...] = ()
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["options"] = list(self.options)
        data["sub_items"] = list(self.sub_items)
        return data


def _q(
    qid: str,
    section: str,
    section_title: str,
    title: str,
    qtype: str,
    options: tuple[str, ...] = (),
    required: bool = True,
    jump: str = "无条件进入下一题",
    analysis: str = "",
    scale: str = "",
    sub_items: tuple[str, ...] = (),
    note: str = "",
) -> Question:
    return Question(
        qid=qid,
        section=section,
        section_title=section_title,
        title=title,
        qtype=qtype,
        options=options,
        required=required,
        jump=jump,
        analysis=analysis,
        scale=scale,
        sub_items=sub_items,
        note=note,
    )


A = "A"
A_TITLE = "企业画像（匿名，不收集企业名称）"
B = "B"
B_TITLE = "空间与服务满意度 + NPS"
C = "C"
C_TITLE = "资源对接需求"
D = "D"
D_TITLE = "活动与内容"
E = "E"
E_TITLE = "数字化触点"
F = "F"
F_TITLE = "续约意向与主要影响因素"
G = "G"
G_TITLE = "开放题"
H = "H"
H_TITLE = "回访意愿（可选）"

QUESTIONS: tuple[Question, ...] = (
    # ---------- A 企业画像（4 题）----------
    _q(
        "A1", A, A_TITLE,
        "贵企业所属的行业是？",
        "单选题",
        ("科技/互联网与软件", "制造业", "金融与投资", "专业服务（法律/会计/咨询）",
         "教育培训", "医疗健康", "文化传媒与创意", "零售与消费", "物流与供应链",
         "建筑与房地产", "能源与环保", "其他"),
        analysis="频数与百分比分布；与 B 满意度、F 续约意向做交叉分析（按行业分组）。",
        note="仅收集行业类别，不收集企业名称。",
    ),
    _q(
        "A2", A, A_TITLE,
        "贵企业目前的员工规模区间是？",
        "单选题",
        ("1–20 人", "21–50 人", "51–100 人", "101–300 人", "301–1000 人", "1000 人以上"),
        analysis="频数分布；作为企业规模分层变量，与 NPS、资源需求做交叉分析。",
    ),
    _q(
        "A3", A, A_TITLE,
        "贵企业入驻空间的时长区间是？",
        "单选题",
        ("不足 6 个月", "6–12 个月", "1–2 年", "2–3 年", "3–5 年", "5 年以上"),
        analysis="频数分布；按入驻年限分组比较满意度与续约意向，识别新会员适应期问题。",
    ),
    _q(
        "A4", A, A_TITLE,
        "贵企业在空间内日常办公的人数区间是？",
        "单选题",
        ("1–5 人", "6–10 人", "11–20 人", "21–50 人", "50 人以上"),
        analysis="频数分布；与实际使用强度相关指标（会议室、活动参与）做交叉分析。",
    ),

    # ---------- B 满意度 + NPS（9 题）----------
    _q("B1", B, B_TITLE, "您对前台接待的满意度如何？", "量表题", SATISFACTION_SCALE,
       scale="1–5 分", analysis="计算均值、标准差与 4–5 分好评率；纳入满意度分项排行榜。"),
    _q("B2", B, B_TITLE, "您对会议室（可用性与设施）的满意度如何？", "量表题", SATISFACTION_SCALE,
       scale="1–5 分", analysis="计算均值、标准差与好评率；与 E3 会议室线上预订需求做交叉分析。"),
    _q("B3", B, B_TITLE, "您对网络（稳定性与速率）的满意度如何？", "量表题", SATISFACTION_SCALE,
       scale="1–5 分", analysis="计算均值与好评率；作为基础设施基线指标按区域/楼层拆分。"),
    _q("B4", B, B_TITLE, "您对保洁服务的满意度如何？", "量表题", SATISFACTION_SCALE,
       scale="1–5 分", analysis="计算均值与好评率；纳入物业服务分项对比。"),
    _q("B5", B, B_TITLE, "您对报修响应的满意度如何？", "量表题", SATISFACTION_SCALE,
       scale="1–5 分", analysis="计算均值与好评率；低分项（1–2 分）进入服务改进清单。"),
    _q("B6", B, B_TITLE, "您对活动组织的满意度如何？", "量表题", SATISFACTION_SCALE,
       scale="1–5 分", analysis="计算均值与好评率；与 D1 参与频次、D2 偏好类型做交叉分析。"),
    _q("B7", B, B_TITLE, "您对会员经理服务的满意度如何？", "量表题", SATISFACTION_SCALE,
       scale="1–5 分", analysis="计算均值与好评率；与 F1 续约意向做相关性分析。"),
    _q("B8", B, B_TITLE, "您对公共区域与安保的满意度如何？", "量表题", SATISFACTION_SCALE,
       scale="1–5 分", analysis="计算均值与好评率；纳入物业服务分项对比。"),
    _q(
        "B9", B, B_TITLE,
        "您有多大可能将本空间推荐给其他企业？",
        "NPS 评分题", NPS_SCALE,
        scale="0–10 分",
        analysis="按推荐者(9–10)/中立者(7–8)/贬损者(0–6)分组，计算 NPS = 推荐者占比 − 贬损者占比；"
                 "并与 B1–B8 分项满意度做驱动因素分析。详见《NPS计算说明.md》。",
    ),

    # ---------- C 资源对接需求（3 题）----------
    _q(
        "C1", C, C_TITLE,
        "您希望对接的资源类型有哪些？（最多选 3 项）",
        "多选题",
        ("客户", "供应商", "投资", "人才", "政策", "专家"),
        analysis="各选项选择率（多选口径，分母为有效答卷数）；与行业(A1)、规模(A2)交叉分析。",
        note="最多选 3 项，导入平台时设置多选上限。",
    ),
    _q(
        "C2", C, C_TITLE,
        "过去 12 个月，贵企业是否通过空间获得过资源对接？",
        "单选题", ("是", "否", "不确定/记不清"),
        analysis="计算对接获得率；作为 C3 的显示条件与资源对接成效的核心分母。",
        jump="选择“否”或“不确定/记不清” → 跳至 D1；选择“是” → 进入 C3。",
    ),
    _q(
        "C3", C, C_TITLE,
        "您对过去 12 个月通过空间获得的对接效果如何评价？",
        "单选题",
        ("很有帮助", "有帮助", "一般", "帮助不大", "没有帮助"),
        analysis="频数分布；计算“很有帮助+有帮助”占比作为对接有效率；与 C1 资源类型交叉分析。",
        jump="仅当 C2=“是”时作答；否则跳过本题。",
    ),

    # ---------- D 活动与内容（4 题）----------
    _q(
        "D1", D, D_TITLE,
        "贵企业参加空间活动的频次是？",
        "单选题",
        ("每周一次及以上", "每月 1–2 次", "每季度 1–2 次", "半年 1–2 次", "几乎不参加"),
        analysis="频数分布；与 B6 活动满意度、F1 续约意向做交叉分析。",
    ),
    _q(
        "D2", D, D_TITLE,
        "您偏好的活动类型有哪些？（最多选 3 项）",
        "多选题",
        ("行业论坛/峰会", "技术/业务培训", "投融资路演", "社交沙龙", "政策解读", "创始人分享", "其他"),
        analysis="各选项选择率；据此排定活动类型优先级。",
    ),
    _q(
        "D3", D, D_TITLE,
        "您偏好的活动时段有哪些？（可多选）",
        "多选题",
        ("工作日午间", "工作日晚间", "周末白天", "周末晚间"),
        analysis="各时段选择率；与 D1 参与频次交叉分析以确定排期。",
    ),
    _q(
        "D4", D, D_TITLE,
        "您对以下内容的兴趣程度如何？",
        "矩阵量表题", INTEREST_SCALE,
        scale="1–5 分",
        sub_items=("创始人播客", "行业知识内容"),
        analysis="逐项计算均值与高兴趣(4–5 分)占比；作为内容生产投入依据。",
    ),

    # ---------- E 数字化触点（3 题）----------
    _q(
        "E1", E, E_TITLE,
        "您是否使用过空间的现有小程序？",
        "单选题",
        ("经常使用", "偶尔使用", "听说过但未使用", "不知道有小程序"),
        analysis="使用率（经常+偶尔）与触达缺口（未使用+不知道）占比。",
        jump="选择“经常使用”或“偶尔使用” → 进入 E2；否则 → 跳至 E3。",
    ),
    _q(
        "E2", E, E_TITLE,
        "您常用小程序的哪些功能？（可多选）",
        "多选题",
        ("会议室预订", "报修", "账单查看", "访客邀请", "活动报名", "其他"),
        analysis="各功能使用率；与 B2/B5/B6 分项满意度做交叉分析，识别高频低分触点。",
        jump="仅当 E1=“经常使用”或“偶尔使用”时作答；否则跳过本题。",
    ),
    _q(
        "E3", E, E_TITLE,
        "您希望在小程序上办理哪些事项？（最多选 5 项）",
        "多选题",
        ("会议室预订", "报修", "账单查看", "访客邀请", "活动报名", "其他"),
        analysis="各事项需求率；与 E2 使用率做差距分析，输出数字化排期清单。",
    ),

    # ---------- F 续约意向（2 题）----------
    _q(
        "F1", F, F_TITLE,
        "当前租期到期后，您续约的可能性是？",
        "单选题",
        ("肯定会续约", "可能会续约", "不确定", "可能不续约", "肯定不续约"),
        analysis="计算续约意向率（肯定+可能）；与 B9 NPS、B1–B8 满意度做驱动分析。",
    ),
    _q(
        "F2", F, F_TITLE,
        "影响贵企业续约的主要因素有哪些？（最多选 3 项）",
        "多选题",
        ("区位与通勤", "空间费用", "硬件设施", "前台与物业服务", "会员经理服务",
         "社群与资源对接", "活动内容", "其他"),
        analysis="各因素影响率；对“可能不续约/肯定不续约”样本单独统计，定位流失主因。",
    ),

    # ---------- G 开放题（2 题）----------
    _q(
        "G1", G, G_TITLE,
        "您最希望空间在哪些方面改进？（开放题）",
        "多行填空题", (),
        required=False,
        analysis="文本编码归类（设施/服务/社群/数字化/价格/其他），统计主题频次并摘录代表性原话。",
        note="选填；不提示填写任何联系方式。",
    ),
    _q(
        "G2", G, G_TITLE,
        "其他建议或期望？（开放题）",
        "多行填空题", (),
        required=False,
        analysis="文本编码归类，作为满意度分项与 NPS 的定性补充解释。",
        note="选填；不提示填写任何联系方式。",
    ),

    # ---------- H 回访意愿（1 题，可选）----------
    _q(
        "H1", H, H_TITLE,
        "是否愿意接受会员经理的线下回访？",
        "单选题", ("愿意", "不愿意"),
        required=False,
        analysis="统计愿意回访占比；仅用于确定线下联系名单规模，问卷本身不收集任何联系方式。",
        jump="选择“愿意” → 由会员经理按既有会员档案线下联系（问卷不收集联系方式）；选择“不愿意” → 结束。",
        note="可选回答；本问卷不收集姓名、电话、邮箱、微信等任何联系方式。",
    ),
)

SECTIONS: tuple[tuple[str, str], ...] = (
    (A, A_TITLE),
    (B, B_TITLE),
    (C, C_TITLE),
    (D, D_TITLE),
    (E, E_TITLE),
    (F, F_TITLE),
    (G, G_TITLE),
    (H, H_TITLE),
)

# 匿名性扫描词表：命中即视为问卷收集了身份或联系方式信息。
SENSITIVE_PATTERNS: tuple[str, ...] = (
    "企业名称", "公司名称", "单位名称", "企业全称", "姓名", "真实姓名", "联系人",
    "手机号", "手机号码", "联系电话", "电话号码", "电话", "邮箱", "电子邮箱",
    "微信", "微信号", "QQ", "通讯地址", "联系地址", "住址", "身份证", "营业执照号",
)

# 允许在说明性文字中出现上述词表的白名单（例如声明“不收集联系方式”）。
SENSITIVE_ALLOWLIST_PREFIXES: tuple[str, ...] = (
    "不收集", "仅收集", "无需填写", "不提示", "问卷本身不收集", "否则跳过", "由会员经理",
)


def get_questions() -> list[Question]:
    """返回题目定义的浅拷贝列表。"""
    return list(QUESTIONS)


def get_question(qid: str) -> Question | None:
    for question in QUESTIONS:
        if question.qid == qid:
            return question
    return None


def get_questionnaire() -> dict[str, Any]:
    """返回可直接序列化的完整问卷结构。"""
    return {
        "code": "S1-INT-008",
        "title": "会员问卷：满意度、NPS 与资源对接诉求",
        "version": "1.0.0",
        "anonymous": True,
        "target_respondents": "约 100 家会员企业的对接人",
        "estimated_minutes": 8,
        "sections": [
            {"code": code, "title": title,
             "questions": [q.to_dict() for q in QUESTIONS if q.section == code]}
            for code, title in SECTIONS
        ],
        "question_count": len(QUESTIONS),
    }


def _sensitive_hits(text: str) -> list[str]:
    hits: list[str] = []
    for pattern in SENSITIVE_PATTERNS:
        if pattern not in text:
            continue
        # 白名单：该词出现在声明式否定语境中不算收集字段。
        prefix_window = text[max(0, text.index(pattern) - 12): text.index(pattern)]
        if any(p in prefix_window for p in SENSITIVE_ALLOWLIST_PREFIXES):
            continue
        hits.append(pattern)
    return hits


def validate_questionnaire() -> dict[str, Any]:
    """校验题量、元数据完整性、匿名性与量表配置。"""
    blocking_issues: list[dict[str, str]] = []
    advisories: list[dict[str, str]] = []

    count = len(QUESTIONS)
    if not 20 <= count <= 30:
        blocking_issues.append({"qid": "-", "field": "题量", "message": f"题量 {count} 不在 20–30 之间"})

    qids = [q.qid for q in QUESTIONS]
    if len(set(qids)) != len(qids):
        blocking_issues.append({"qid": "-", "field": "题号", "message": "题号存在重复"})

    required_fields = ("qid", "section", "section_title", "title", "qtype", "required", "jump", "analysis")
    for q in QUESTIONS:
        for field_name in required_fields:
            value = getattr(q, field_name)
            if value is None or (isinstance(value, str) and not value.strip()):
                blocking_issues.append({"qid": q.qid, "field": field_name, "message": "元数据为空"})
        if q.qtype in ("单选题", "多选题", "量表题", "NPS 评分题", "矩阵量表题") and not q.options and not q.sub_items:
            blocking_issues.append({"qid": q.qid, "field": "options", "message": "选择题缺少选项"})

    # 匿名性扫描：题干 + 选项 + 子项 + 备注。
    sensitive_hits: list[dict[str, str]] = []
    for q in QUESTIONS:
        scan_text = "；".join([q.title, *q.options, *q.sub_items, q.note])
        for hit in _sensitive_hits(scan_text):
            sensitive_hits.append({"qid": q.qid, "pattern": hit})
    if sensitive_hits:
        blocking_issues.append({"qid": "-", "field": "匿名性", "message": "检测到身份/联系方式字段"})

    satisfaction = [q for q in QUESTIONS if q.qid.startswith("B") and q.qid != "B9"]
    if len(satisfaction) < 8:
        blocking_issues.append({"qid": "-", "field": "满意度", "message": f"满意度服务项仅 {len(satisfaction)} 项，少于 8 项"})
    for q in satisfaction:
        if q.scale != "1–5 分":
            blocking_issues.append({"qid": q.qid, "field": "scale", "message": "满意度量表不是 1–5 分"})

    nps_questions = [q for q in QUESTIONS if q.qid == "B9"]
    if len(nps_questions) != 1 or nps_questions[0].scale != "0–10 分":
        blocking_issues.append({"qid": "B9", "field": "NPS", "message": "NPS 题缺失或量表不是 0–10 分"})

    return {
        "question_count": count,
        "section_count": len(SECTIONS),
        "satisfaction_items": len(satisfaction),
        "sensitive_hits": sensitive_hits,
        "blocking_issues": blocking_issues,
        "advisories": advisories,
        "passed": not blocking_issues,
    }
