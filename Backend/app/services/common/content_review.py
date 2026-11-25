import re


# 免责声明检测：报告解读结果末尾必须包含"仅供参考"字样
DISCLAIMER_PATTERN = re.compile(r"仅供参考")

# 越界诊断/用药建议关键词检测：禁止模型给出确定性诊断或具体用药指导
# 「您/你患有」需排除「如果/若/如/当…您患有」这类假设条件语境的误判
# （如「如果您患有高血压…」并非确定性诊断），用负向零宽断言排除常见条件连词。
_CONDITIONAL_GUARD = r"(?<![果若如当假令便])"
OVERREACH_PATTERNS = [
    re.compile(_CONDITIONAL_GUARD + r"您患有"),
    re.compile(_CONDITIONAL_GUARD + r"你患有"),
    re.compile(r"确诊为"),
    re.compile(r"建议服用"),
    re.compile(r"建议(?:您|你)?服药"),
    re.compile(r"请立即服用"),
]


def has_disclaimer(content: str) -> bool:
    """检测输出内容是否包含免责声明"""
    return bool(DISCLAIMER_PATTERN.search(content))


def find_overreach_phrases(content: str) -> list[str]:
    """检测输出内容中越界诊断/用药建议关键词，返回命中的关键词列表"""
    hits = []
    for pattern in OVERREACH_PATTERNS:
        match = pattern.search(content)
        if match:
            hits.append(match.group())
    return hits


def review_content(content: str) -> tuple[bool, str]:
    """
    输出内容审核：检查免责声明 + 越界诊断关键词

    Returns:
        (是否通过, 未通过原因)
    """
    if not has_disclaimer(content):
        return False, "缺少免责声明（仅供参考）"

    overreach_hits = find_overreach_phrases(content)
    if overreach_hits:
        return False, f"检测到越界诊断/用药建议表述：{', '.join(overreach_hits)}"

    return True, ""
