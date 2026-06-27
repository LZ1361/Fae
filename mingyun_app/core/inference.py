from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, time
from typing import Any

from mingyun_app.core.lunar_calendar import lunar_to_solar


STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
MONTH_BRANCHES = ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"]

ELEMENT_BY_STEM = {
    "甲": "wood",
    "乙": "wood",
    "丙": "fire",
    "丁": "fire",
    "戊": "earth",
    "己": "earth",
    "庚": "metal",
    "辛": "metal",
    "壬": "water",
    "癸": "water",
}
ELEMENT_BY_BRANCH = {
    "寅": "wood",
    "卯": "wood",
    "巳": "fire",
    "午": "fire",
    "辰": "earth",
    "戌": "earth",
    "丑": "earth",
    "未": "earth",
    "申": "metal",
    "酉": "metal",
    "亥": "water",
    "子": "water",
}
ELEMENT_LABELS = {
    "wood": "木",
    "fire": "火",
    "earth": "土",
    "metal": "金",
    "water": "水",
}
STEM_POLARITY = {
    "甲": "yang",
    "乙": "yin",
    "丙": "yang",
    "丁": "yin",
    "戊": "yang",
    "己": "yin",
    "庚": "yang",
    "辛": "yin",
    "壬": "yang",
    "癸": "yin",
}
ELEMENT_PRODUCES = {
    "wood": "fire",
    "fire": "earth",
    "earth": "metal",
    "metal": "water",
    "water": "wood",
}
ELEMENT_CONTROLS = {
    "wood": "earth",
    "earth": "water",
    "water": "fire",
    "fire": "metal",
    "metal": "wood",
}
STEMS_BY_ELEMENT = {
    "wood": ["甲", "乙"],
    "fire": ["丙", "丁"],
    "earth": ["戊", "己"],
    "metal": ["庚", "辛"],
    "water": ["壬", "癸"],
}
SIX_HARMONY = {
    "子": "丑",
    "丑": "子",
    "寅": "亥",
    "亥": "寅",
    "卯": "戌",
    "戌": "卯",
    "辰": "酉",
    "酉": "辰",
    "巳": "申",
    "申": "巳",
    "午": "未",
    "未": "午",
}
TRINE_GROUPS = [
    {"申", "子", "辰"},
    {"亥", "卯", "未"},
    {"寅", "午", "戌"},
    {"巳", "酉", "丑"},
]
HIDDEN_STEMS = {
    "子": ["癸"],
    "丑": ["己", "癸", "辛"],
    "寅": ["甲", "丙", "戊"],
    "卯": ["乙"],
    "辰": ["戊", "乙", "癸"],
    "巳": ["丙", "戊", "庚"],
    "午": ["丁", "己"],
    "未": ["己", "丁", "乙"],
    "申": ["庚", "壬", "戊"],
    "酉": ["辛"],
    "戌": ["戊", "辛", "丁"],
    "亥": ["壬", "甲"],
}
ZODIAC_ANIMALS = {
    "子": "鼠",
    "丑": "牛",
    "寅": "虎",
    "卯": "兔",
    "辰": "龙",
    "巳": "蛇",
    "午": "马",
    "未": "羊",
    "申": "猴",
    "酉": "鸡",
    "戌": "狗",
    "亥": "猪",
}
SOLAR_TERM_BOUNDARIES = [
    ((1, 6), "小寒", 11),
    ((2, 4), "立春", 0),
    ((3, 6), "惊蛰", 1),
    ((4, 5), "清明", 2),
    ((5, 6), "立夏", 3),
    ((6, 6), "芒种", 4),
    ((7, 7), "小暑", 5),
    ((8, 8), "立秋", 6),
    ((9, 8), "白露", 7),
    ((10, 8), "寒露", 8),
    ((11, 7), "立冬", 9),
    ((12, 7), "大雪", 10),
]
SOLAR_TERM_NAMES = [item[1] for item in SOLAR_TERM_BOUNDARIES]


def build_evidence_profile(payload: dict[str, Any]) -> dict[str, Any]:
    input_birth_date = _parse_date(str(payload.get("birth_date", "")))
    calendar_type = str(payload.get("calendar_type") or "solar")
    birth_date, calendar_conversion = _resolve_birth_date(input_birth_date, calendar_type, payload)
    birth_time = _parse_time(str(payload.get("birth_time", "")))
    accuracy = str(payload.get("birth_time_accuracy") or "unknown")
    gender = str(payload.get("gender") or "unspecified")
    psychology_answers = payload.get("psychology_answers") or {}
    focus_theories = payload.get("focus_theories") or []

    western_zodiac = _western_zodiac(birth_date)
    bazi = _calculate_bazi(birth_date, birth_time, accuracy)
    element_scores = _element_scores(bazi)
    ten_gods = _ten_gods_profile(bazi)
    psychology = _psychology_scores(psychology_answers)
    life_topics = _life_topics(bazi, element_scores, ten_gods, psychology, accuracy, gender)
    relationship_profile = _relationship_profile(bazi, ten_gods, element_scores, psychology, gender)
    matchmaking = _matchmaking_profile(bazi, element_scores, ten_gods, gender)
    confidence = _confidence(accuracy, bool(psychology_answers), bazi)
    evidence = _evidence(payload, western_zodiac, bazi, element_scores, ten_gods, psychology, calendar_conversion)
    limits = _limits(accuracy, focus_theories)

    return {
        "input_summary": {
            "birth_date": input_birth_date.isoformat(),
            "solar_birth_date": birth_date.isoformat(),
            "birth_time": birth_time.strftime("%H:%M") if birth_time else None,
            "birth_time_accuracy": accuracy,
            "birth_city": payload.get("birth_city") or "",
            "gender": gender,
            "calendar_type": calendar_type,
            "lunar_is_leap": bool(payload.get("lunar_is_leap")),
            "calendar_conversion": calendar_conversion,
            "focus_theories": focus_theories,
        },
        "western_zodiac": western_zodiac,
        "bazi": bazi,
        "elements": element_scores,
        "ten_gods": ten_gods,
        "psychology": psychology,
        "life_topics": life_topics,
        "relationship_profile": relationship_profile,
        "matchmaking": matchmaking,
        "confidence": confidence,
        "evidence": evidence,
        "limits": limits,
        "truth_policy": {
            "model_role": "大模型只能解释 evidence_profile 中的证据，不得编造未计算出的命理结论。",
            "deterministic_layer": "星座、四柱近似排盘、生肖、节气、藏干、五行权重、十神关系和心理题分数由本地算法计算。",
        },
    }


def _parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError("birth_date must use YYYY-MM-DD") from exc


def _parse_time(value: str) -> time | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%H:%M").time()
    except ValueError as exc:
        raise ValueError("birth_time must use HH:MM") from exc


def _resolve_birth_date(
    input_birth_date: date, calendar_type: str, payload: dict[str, Any]
) -> tuple[date, dict[str, Any]]:
    if calendar_type == "lunar":
        converted = lunar_to_solar(
            input_birth_date.year,
            input_birth_date.month,
            input_birth_date.day,
            bool(payload.get("lunar_is_leap")),
        )
        return converted, {
            "input_calendar": "lunar",
            "input_calendar_label": "农历",
            "input_date": input_birth_date.isoformat(),
            "solar_date": converted.isoformat(),
            "basis": "农历日期已按 1900-2050 年常见农历表换算为公历后再计算星座和八字。",
        }
    return input_birth_date, {
        "input_calendar": "solar",
        "input_calendar_label": "公历",
        "input_date": input_birth_date.isoformat(),
        "solar_date": input_birth_date.isoformat(),
        "basis": "用户输入为公历，直接用于星座和八字推导。",
    }


def _western_zodiac(birth_date: date) -> dict[str, str]:
    month_day = (birth_date.month, birth_date.day)
    signs = [
        ((1, 20), "水瓶座", "air"),
        ((2, 19), "双鱼座", "water"),
        ((3, 21), "白羊座", "fire"),
        ((4, 20), "金牛座", "earth"),
        ((5, 21), "双子座", "air"),
        ((6, 22), "巨蟹座", "water"),
        ((7, 23), "狮子座", "fire"),
        ((8, 23), "处女座", "earth"),
        ((9, 23), "天秤座", "air"),
        ((10, 24), "天蝎座", "water"),
        ((11, 23), "射手座", "fire"),
        ((12, 22), "摩羯座", "earth"),
    ]
    current = ("摩羯座", "earth")
    for start, sign, element in signs:
        if month_day >= start:
            current = (sign, element)
    return {"sign": current[0], "element": current[1], "basis": "按公历生日计算太阳星座"}


def _calculate_bazi(birth_date: date, birth_time: time | None, accuracy: str) -> dict[str, Any]:
    ganzhi_year = birth_date.year - 1 if (birth_date.month, birth_date.day) < (2, 4) else birth_date.year
    year_stem = STEMS[(ganzhi_year - 4) % 10]
    year_branch = BRANCHES[(ganzhi_year - 4) % 12]

    solar_term = _solar_term(birth_date)
    month_index = solar_term["month_index"]
    month_branch = MONTH_BRANCHES[month_index]
    month_stem = STEMS[(_first_month_stem_index(year_stem) + month_index) % 10]

    day_index = (_julian_day_number(birth_date) + 49) % 60
    day_stem = STEMS[day_index % 10]
    day_branch = BRANCHES[day_index % 12]

    hour_branch = None if accuracy == "unknown" or birth_time is None else _hour_branch(birth_time)
    hour_stem = _hour_stem(day_stem, hour_branch) if hour_branch else None

    pillars = {
        "year": _pillar("year", year_stem, year_branch, "年柱按立春约 2 月 4 日切换"),
        "month": _pillar("month", month_stem, month_branch, f"月柱按节气 {solar_term['current']['name']} 近似切换"),
        "day": _pillar("day", day_stem, day_branch, "日柱按 Gregorian JDN + 49 的常见六十甲子算法计算"),
        "hour": _pillar("hour", hour_stem, hour_branch, "时柱按两小时一支，并由日干推时干"),
    }
    hidden_stems = {
        branch: HIDDEN_STEMS[branch]
        for branch in [year_branch, month_branch, day_branch, hour_branch]
        if branch
    }
    zodiac = {
        "animal": ZODIAC_ANIMALS[year_branch],
        "branch": year_branch,
        "basis": "生肖由年支推导，年支按立春节气近似切换。",
    }

    return {
        "pillars": pillars,
        "zodiac": zodiac,
        "solar_term": solar_term,
        "hidden_stems": hidden_stems,
        "day_master": {
            "stem": day_stem,
            "element": ELEMENT_BY_STEM[day_stem],
            "element_label": ELEMENT_LABELS[ELEMENT_BY_STEM[day_stem]],
            "polarity": STEM_POLARITY[day_stem],
        },
        "calculation_level": "deterministic_common_calendar_approx",
        "basis": "年/月柱采用节气近似边界，日柱采用常见 JDN 六十甲子公式；未接入高精度天文历库。",
        # Backward-compatible aliases for older renderers/tests.
        "year_pillar": pillars["year"]["pillar"],
        "month_pillar": pillars["month"]["pillar"],
        "day_pillar": pillars["day"]["pillar"],
        "hour_pillar": pillars["hour"]["pillar"],
        "hour_branch": hour_branch,
    }


def _pillar(kind: str, stem: str | None, branch: str | None, basis: str) -> dict[str, Any]:
    pillar = f"{stem}{branch}" if stem and branch else None
    return {
        "kind": kind,
        "pillar": pillar,
        "stem": stem,
        "branch": branch,
        "stem_element": ELEMENT_BY_STEM.get(stem or ""),
        "branch_element": ELEMENT_BY_BRANCH.get(branch or ""),
        "hidden_stems": HIDDEN_STEMS.get(branch or "", []),
        "basis": basis,
    }


def _julian_day_number(birth_date: date) -> int:
    year = birth_date.year
    month = birth_date.month
    day = birth_date.day
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    return day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045


def _solar_term(birth_date: date) -> dict[str, Any]:
    md = (birth_date.month, birth_date.day)
    current_index = 0
    for idx, (boundary, _name, _month_index) in enumerate(SOLAR_TERM_BOUNDARIES):
        if md >= boundary:
            current_index = idx
    current_boundary, current_name, month_index = SOLAR_TERM_BOUNDARIES[current_index]
    next_index = (current_index + 1) % len(SOLAR_TERM_BOUNDARIES)
    next_boundary, next_name, _next_month = SOLAR_TERM_BOUNDARIES[next_index]
    return {
        "current": {"name": current_name, "approx_date": _month_day_text(current_boundary)},
        "next": {"name": next_name, "approx_date": _month_day_text(next_boundary)},
        "month_index": month_index,
        "basis": "MVP 使用固定节气近似日，后续可替换为高精度历法库。",
    }


def _month_day_text(value: tuple[int, int]) -> str:
    return f"{value[0]:02d}-{value[1]:02d}"


def _first_month_stem_index(year_stem: str) -> int:
    if year_stem in {"甲", "己"}:
        return 2
    if year_stem in {"乙", "庚"}:
        return 4
    if year_stem in {"丙", "辛"}:
        return 6
    if year_stem in {"丁", "壬"}:
        return 8
    return 0


def _hour_branch(birth_time: time) -> str:
    hour = birth_time.hour
    if hour == 23 or hour == 0:
        return "子"
    return BRANCHES[((hour + 1) // 2) % 12]


def _hour_stem(day_stem: str, hour_branch: str | None) -> str | None:
    if not hour_branch:
        return None
    first_stem_index = {
        "甲": 0,
        "己": 0,
        "乙": 2,
        "庚": 2,
        "丙": 4,
        "辛": 4,
        "丁": 6,
        "壬": 6,
        "戊": 8,
        "癸": 8,
    }[day_stem]
    return STEMS[(first_stem_index + BRANCHES.index(hour_branch)) % 10]


def _element_scores(bazi: dict[str, Any]) -> dict[str, Any]:
    counts: dict[str, float] = defaultdict(float)
    sources: dict[str, list[str]] = defaultdict(list)
    pillar_weights = {"year": 1.0, "month": 1.35, "day": 1.25, "hour": 0.95}
    hidden_weights = [0.45, 0.25, 0.15]

    for pillar_key, pillar in bazi["pillars"].items():
        if not pillar.get("pillar"):
            continue
        weight = pillar_weights[pillar_key]
        stem = pillar["stem"]
        branch = pillar["branch"]
        if stem:
            element = ELEMENT_BY_STEM[stem]
            counts[element] += weight
            sources[element].append(f"{_pillar_label(pillar_key)}天干{stem}")
        if branch:
            element = ELEMENT_BY_BRANCH[branch]
            counts[element] += weight
            sources[element].append(f"{_pillar_label(pillar_key)}地支{branch}")
            for idx, hidden_stem in enumerate(HIDDEN_STEMS[branch]):
                hidden_element = ELEMENT_BY_STEM[hidden_stem]
                counts[hidden_element] += hidden_weights[min(idx, len(hidden_weights) - 1)]
                sources[hidden_element].append(f"{_pillar_label(pillar_key)}藏干{hidden_stem}")

    total = sum(counts.values()) or 1.0
    scores = {}
    for key in ("wood", "fire", "earth", "metal", "water"):
        scores[key] = {
            "label": ELEMENT_LABELS[key],
            "score": round((counts[key] / total) * 100),
            "raw_weight": round(counts[key], 2),
            "sources": sources[key][:6],
        }
    return scores


def _ten_gods_profile(bazi: dict[str, Any]) -> dict[str, Any]:
    day_master = bazi["day_master"]
    visible_items = []
    distribution: Counter[str] = Counter()

    for pillar_key, pillar in bazi["pillars"].items():
        if pillar_key != "day" and pillar.get("stem"):
            god = _ten_god(day_master["stem"], pillar["stem"])
            visible_items.append(
                {
                    "position": f"{_pillar_label(pillar_key)}天干",
                    "stem": pillar["stem"],
                    "ten_god": god,
                    "basis": f"{pillar['stem']} 相对于日主 {day_master['stem']} 的生克关系",
                }
            )
            distribution[god] += 1
        for hidden_stem in pillar.get("hidden_stems") or []:
            god = _ten_god(day_master["stem"], hidden_stem)
            distribution[god] += 0.45

    return {
        "day_master": day_master,
        "visible": visible_items,
        "distribution": [
            {"name": name, "weight": round(weight, 2)} for name, weight in distribution.most_common()
        ],
        "symbolism": {
            "比肩": "自我、同辈、竞争与独立性",
            "劫财": "资源争夺、合作张力、行动冲劲",
            "食神": "表达、享受、稳定输出与创造",
            "伤官": "突破、质疑、才华外放与反规则",
            "正财": "稳定收入、现实经营、关系中的责任感",
            "偏财": "机会型资源、弹性收入、社交资源",
            "正官": "规则、责任、职业秩序与伴侣承诺",
            "七杀": "压力、竞争、决断力与外部挑战",
            "正印": "学习、保护、资质、长期支持",
            "偏印": "洞察、非典型学习、灵感与独处恢复",
        },
        "basis": "以日干为日主，按五行生克和阴阳同异推导十神。",
    }


def _ten_god(day_stem: str, other_stem: str) -> str:
    day_element = ELEMENT_BY_STEM[day_stem]
    other_element = ELEMENT_BY_STEM[other_stem]
    same_polarity = STEM_POLARITY[day_stem] == STEM_POLARITY[other_stem]

    if other_element == day_element:
        return "比肩" if same_polarity else "劫财"
    if ELEMENT_PRODUCES[day_element] == other_element:
        return "食神" if same_polarity else "伤官"
    if ELEMENT_CONTROLS[day_element] == other_element:
        return "偏财" if same_polarity else "正财"
    if ELEMENT_CONTROLS[other_element] == day_element:
        return "七杀" if same_polarity else "正官"
    return "偏印" if same_polarity else "正印"


def _psychology_scores(answers: dict[str, Any]) -> dict[str, Any]:
    def slider(name: str, default: int = 3) -> int:
        try:
            return max(1, min(5, int(answers.get(name, default))))
        except (TypeError, ValueError):
            return default

    energy = slider("energy_social")
    planning = slider("planning")
    emotion = slider("emotion_focus")
    novelty = slider("novelty")
    return {
        "source": "用户自评滑杆，不等同正式心理测评",
        "traits": {
            "introversion": round((6 - energy) / 5 * 100),
            "planning": round(planning / 5 * 100),
            "empathy_focus": round(emotion / 5 * 100),
            "openness_to_novelty": round(novelty / 5 * 100),
        },
        "mbti_tendencies": {
            "E_I": round((6 - energy) / 5 * 100),
            "S_N": round(novelty / 5 * 100),
            "T_F": round(emotion / 5 * 100),
            "J_P": round(planning / 5 * 100),
        },
    }


def _life_topics(
    bazi: dict[str, Any],
    elements: dict[str, Any],
    ten_gods: dict[str, Any],
    psychology: dict[str, Any],
    accuracy: str,
    gender: str,
) -> dict[str, Any]:
    distribution = {item["name"]: item["weight"] for item in ten_gods["distribution"]}
    strongest = sorted(elements.values(), key=lambda item: item["score"], reverse=True)[:2]
    weakest = sorted(elements.values(), key=lambda item: item["score"])[:1]
    time_confidence = {"accurate": 0.78, "approximate": 0.58, "unknown": 0.38}.get(accuracy, 0.45)

    return {
        "personality": _topic(
            "性格底色",
            ["日主", "五行分布", "心理自评"],
            f"日主为{bazi['day_master']['stem']}，五行较显的是{'、'.join(item['label'] for item in strongest)}，可优先解释行动方式与稳定偏好。",
            max(0.5, psychology["traits"]["planning"] / 100),
        ),
        "relationship": _topic(
            "婚恋与亲密关系",
            ["正官/七杀", "正财/偏财", "情绪关注自评"],
            _relationship_signal(distribution, psychology, gender),
            min(0.72, time_confidence + 0.08),
        ),
        "career": _topic(
            "事业与职业选择",
            ["官杀", "印星", "食伤", "规划自评"],
            _career_signal(distribution, psychology),
            min(0.76, time_confidence + 0.12),
        ),
        "wealth": _topic(
            "财运与资源经营",
            ["正财", "偏财", "五行强弱"],
            _wealth_signal(distribution, strongest),
            min(0.72, time_confidence + 0.1),
        ),
        "health_energy": _topic(
            "身心能量与节律",
            ["五行偏盛偏弱", "节气", "时间准确度"],
            f"当前只做能量节律提示：{strongest[0]['label']}较显、{weakest[0]['label']}较弱，适合提醒生活节奏和压力管理，不作医疗判断。",
            0.58,
        ),
        "study_growth": _topic(
            "学业、成长与学习方式",
            ["印星", "食伤", "新鲜感自评"],
            _study_signal(distribution, psychology),
            0.66,
        ),
        "social_family": _topic(
            "社交、人际与家庭支持",
            ["比劫", "印星", "社交能量自评"],
            _social_signal(distribution, psychology),
            0.64,
        ),
        "timing": _topic(
            "人生周期与阶段建议",
            ["节气", "年/月/日/时柱", "用户年龄"],
            "MVP 先给阶段性建议和可执行观察点；精确大运起运岁数、流年流月需要接入高精度历法与性别/顺逆排规则后再开放。",
            0.42,
        ),
    }


def _topic(title: str, basis: list[str], signal: str, confidence: float) -> dict[str, Any]:
    return {
        "title": title,
        "basis": basis,
        "signal": signal,
        "confidence": round(confidence, 2),
        "limits": ["这是由命盘证据推导出的倾向，不是绝对预测。"],
    }


def _relationship_profile(
    bazi: dict[str, Any],
    ten_gods: dict[str, Any],
    elements: dict[str, Any],
    psychology: dict[str, Any],
    gender: str,
) -> dict[str, Any]:
    distribution = {item["name"]: item["weight"] for item in ten_gods["distribution"]}
    officer = round(distribution.get("正官", 0) + distribution.get("七杀", 0), 2)
    wealth = round(distribution.get("正财", 0) + distribution.get("偏财", 0), 2)
    day_branch = bazi["pillars"]["day"]["branch"]
    compatible_branch = SIX_HARMONY.get(day_branch)
    weakest = sorted(elements.values(), key=lambda item: item["score"])[:2]
    partner_star = _partner_star_label(gender)
    relationship_tone = _relationship_signal(distribution, psychology, gender)
    return {
        "title": "姻缘分析",
        "partner_star": partner_star,
        "partner_star_weights": {"官杀": officer, "财星": wealth},
        "relationship_tone": relationship_tone,
        "day_branch_pairing": {
            "self_day_branch": day_branch,
            "six_harmony_branch": compatible_branch,
            "basis": "以日支作为亲密关系宫位的观察点，六合只作为加分项，不作绝对配对。",
        },
        "needs_to_balance": [item["label"] for item in weakest],
        "risk_notes": [
            "伴侣星强时，容易把承诺、责任或现实经营放大成压力。",
            "五行偏弱项适合由现实相处、作息和沟通方式共同补足，不能只看命盘。",
        ],
        "confidence": 0.7,
        "limits": ["姻缘结果是匹配倾向，不是婚姻成败预测。"],
    }


def _matchmaking_profile(
    bazi: dict[str, Any],
    elements: dict[str, Any],
    ten_gods: dict[str, Any],
    gender: str,
) -> dict[str, Any]:
    weakest_elements = sorted(elements.items(), key=lambda item: item[1]["score"])[:2]
    strongest_elements = sorted(elements.items(), key=lambda item: item[1]["score"], reverse=True)[:1]
    recommended_elements = [
        {
            "element": key,
            "label": value["label"],
            "reason": f"你的命盘中{value['label']}相对偏弱，伴侣画像可优先看能补足{value['label']}气质的人。",
            "candidate_day_stems": STEMS_BY_ELEMENT[key],
        }
        for key, value in weakest_elements
    ]
    day_branch = bazi["pillars"]["day"]["branch"]
    year_branch = bazi["pillars"]["year"]["branch"]
    favorable_branches = _favorable_partner_branches(day_branch, year_branch)
    return {
        "title": "更匹配的异性八字画像",
        "target_gender": {"female": "male", "male": "female"}.get(gender, "opposite_or_user_selected"),
        "recommended_elements": recommended_elements,
        "favorable_branches": favorable_branches,
        "partner_ten_god_focus": _partner_star_label(gender),
        "avoid_overemphasis": [
            f"你的{strongest_elements[0][1]['label']}已经较显，伴侣画像不必继续单一强化这一项。",
            "不要只按生肖或单柱筛选，至少同时看日主、日支、五行分布和现实互动。",
        ],
        "screening_questions": [
            "对方是否能补足你较弱的节律、沟通或执行方式？",
            "两人的责任分配是否清楚，而不是只靠吸引力推进？",
            "关系压力出现时，对方是稳定协商，还是放大冲突？",
        ],
        "confidence": 0.66,
        "basis": ["五行补偏", "日支六合", "三合参考", "伴侣星口径"],
    }


def _partner_star_label(gender: str) -> str:
    if gender == "female":
        return "女性传统口径重点看官杀：正官代表稳定承诺，七杀代表压力、吸引与挑战。"
    if gender == "male":
        return "男性传统口径重点看财星：正财代表稳定经营，偏财代表机会、吸引与资源流动。"
    return "未指定性别时同时参考官杀与财星，再由用户自行选择口径。"


def _favorable_partner_branches(day_branch: str, year_branch: str) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    if day_branch in SIX_HARMONY:
        candidates.append(
            {
                "branch": SIX_HARMONY[day_branch],
                "reason": f"与日支{day_branch}形成六合，可作为亲密关系宫位的加分参考。",
            }
        )
    if year_branch in SIX_HARMONY and SIX_HARMONY[year_branch] != candidates[0]["branch"]:
        candidates.append(
            {
                "branch": SIX_HARMONY[year_branch],
                "reason": f"与年支{year_branch}形成六合，可作为外在气场和家庭背景的辅助参考。",
            }
        )
    for group in TRINE_GROUPS:
        if day_branch in group:
            for branch in sorted(group):
                if branch != day_branch and all(item["branch"] != branch for item in candidates):
                    candidates.append(
                        {
                            "branch": branch,
                            "reason": f"与日支{day_branch}同属三合局，可作为次级匹配参考。",
                        }
                    )
            break
    return candidates[:4]


def _relationship_signal(distribution: dict[str, float], psychology: dict[str, Any], gender: str) -> str:
    officer = distribution.get("正官", 0) + distribution.get("七杀", 0)
    wealth = distribution.get("正财", 0) + distribution.get("偏财", 0)
    empathy = psychology["traits"]["empathy_focus"]
    if gender == "female":
        return f"按传统十神口径，女性婚恋多参考官杀；当前官杀权重 {round(officer, 2)}，情绪关注自评 {empathy}，应结合现实互动看承诺、边界和压力。"
    if gender == "male":
        return f"按传统十神口径，男性婚恋多参考财星；当前财星权重 {round(wealth, 2)}，情绪关注自评 {empathy}，应结合现实互动看责任、资源安排和沟通质量。"
    if officer >= wealth and officer >= 1:
        return f"官杀信号较明显，亲密关系里更重承诺、边界和责任；情绪关注自评 {empathy}，需避免把责任感变成压力。"
    if wealth >= 1:
        return f"财星信号较明显，更容易从现实经营、共同目标和资源安排理解关系；情绪关注自评 {empathy}，沟通要避免只谈效率。"
    return f"伴侣星不算突出，关系解读应放在互动习惯和心理自评上；情绪关注自评 {empathy}。"


def _career_signal(distribution: dict[str, float], psychology: dict[str, Any]) -> str:
    officer = distribution.get("正官", 0) + distribution.get("七杀", 0)
    resource = distribution.get("正印", 0) + distribution.get("偏印", 0)
    output = distribution.get("食神", 0) + distribution.get("伤官", 0)
    planning = psychology["traits"]["planning"]
    if officer >= max(resource, output):
        return f"官杀强于其他事业信号，更适合有责任、目标和评价标准的路径；规划自评 {planning}，适合把压力转成阶段目标。"
    if resource >= output:
        return f"印星信号较明显，学习、资质、研究和长期积累更能带来职业安全感；规划自评 {planning}。"
    return f"食伤信号较明显，表达、创造、产品化输出和解决具体问题更容易形成职业优势；规划自评 {planning}。"


def _wealth_signal(distribution: dict[str, float], strongest: list[dict[str, Any]]) -> str:
    stable = distribution.get("正财", 0)
    flexible = distribution.get("偏财", 0)
    if stable >= flexible and stable > 0:
        return f"正财权重高于偏财，财务倾向宜重稳定现金流、预算和长期复利；五行较显的是{'、'.join(item['label'] for item in strongest)}。"
    if flexible > 0:
        return f"偏财信号较明显，机会型资源和人脉信息值得关注，但需要用预算和止损规则约束；五行较显的是{'、'.join(item['label'] for item in strongest)}。"
    return f"财星不突出，财运部分应保守解读为资源经营习惯，而不是断言财富结果；五行较显的是{'、'.join(item['label'] for item in strongest)}。"


def _study_signal(distribution: dict[str, float], psychology: dict[str, Any]) -> str:
    resource = distribution.get("正印", 0) + distribution.get("偏印", 0)
    output = distribution.get("食神", 0) + distribution.get("伤官", 0)
    novelty = psychology["traits"]["openness_to_novelty"]
    if resource >= output:
        return f"印星不弱，适合系统学习、证书型目标或稳定输入；新鲜感自评 {novelty}，可用项目制保持动力。"
    return f"食伤较显，适合边做边学、输出倒逼输入；新鲜感自评 {novelty}，要防止兴趣跳转过快。"


def _social_signal(distribution: dict[str, float], psychology: dict[str, Any]) -> str:
    peers = distribution.get("比肩", 0) + distribution.get("劫财", 0)
    resource = distribution.get("正印", 0) + distribution.get("偏印", 0)
    introversion = psychology["traits"]["introversion"]
    if peers >= resource:
        return f"比劫信号较明显，同辈、团队和竞争关系对状态影响较大；内倾自评 {introversion}，社交需要可控边界。"
    return f"印星支持感较明显，家庭、导师或稳定支持系统会影响决策安全感；内倾自评 {introversion}。"


def _confidence(accuracy: str, has_psychology: bool, bazi: dict[str, Any]) -> dict[str, float]:
    time_sensitive = {"accurate": 0.86, "approximate": 0.62, "unknown": 0.35}.get(accuracy, 0.45)
    deterministic = 0.82 if bazi.get("calculation_level") == "deterministic_common_calendar_approx" else 0.72
    psychology = 0.72 if has_psychology else 0.42
    overall = round((time_sensitive * 0.25) + (deterministic * 0.4) + (psychology * 0.35), 2)
    return {
        "overall": overall,
        "time_sensitive": time_sensitive,
        "deterministic_calculation": deterministic,
        "psychology": psychology,
    }


def _evidence(
    payload: dict[str, Any],
    western_zodiac: dict[str, str],
    bazi: dict[str, Any],
    element_scores: dict[str, Any],
    ten_gods: dict[str, Any],
    psychology: dict[str, Any],
    calendar_conversion: dict[str, Any],
) -> list[dict[str, Any]]:
    strongest_elements = sorted(
        element_scores.items(), key=lambda item: item[1]["score"], reverse=True
    )[:2]
    pillars = bazi["pillars"]
    visible_ten_gods = "、".join(
        f"{item['position']}{item['stem']}={item['ten_god']}" for item in ten_gods["visible"][:4]
    )
    return [
        {
            "label": "历法换算",
            "value": f"{calendar_conversion['input_calendar_label']} {calendar_conversion['input_date']} -> 公历 {calendar_conversion['solar_date']}",
            "basis": calendar_conversion["basis"],
            "confidence": 0.82,
        },
        {
            "label": "四柱",
            "value": " / ".join(
                filter(
                    None,
                    [
                        pillars["year"]["pillar"],
                        pillars["month"]["pillar"],
                        pillars["day"]["pillar"],
                        pillars["hour"]["pillar"],
                    ],
                )
            ),
            "basis": "年/月按节气近似，日柱按 JDN 六十甲子，时柱由日干与时支推导",
            "confidence": 0.82,
        },
        {
            "label": "生肖与节气",
            "value": f"{bazi['zodiac']['animal']} / {bazi['solar_term']['current']['name']}",
            "basis": "生肖由年支推导，节气采用固定近似日",
            "confidence": 0.76,
        },
        {
            "label": "太阳星座",
            "value": western_zodiac["sign"],
            "basis": western_zodiac["basis"],
            "confidence": 0.9,
        },
        {
            "label": "日主",
            "value": f"{bazi['day_master']['stem']}（{bazi['day_master']['element_label']}）",
            "basis": "日干作为十神推导的参照点",
            "confidence": 0.82,
        },
        {
            "label": "五行较显",
            "value": "、".join(f"{v['label']}({v['score']})" for _, v in strongest_elements),
            "basis": "来自四柱天干、地支和藏干的加权计数",
            "confidence": 0.72,
        },
        {
            "label": "十神可见关系",
            "value": visible_ten_gods or "无可见天干关系",
            "basis": ten_gods["basis"],
            "confidence": 0.78,
        },
        {
            "label": "心理自评",
            "value": psychology["traits"],
            "basis": psychology["source"],
            "confidence": 0.72 if payload.get("psychology_answers") else 0.42,
        },
    ]


def _limits(accuracy: str, focus_theories: list[str]) -> list[str]:
    limits = [
        "当前版本使用常见历法近似算法，未接入高精度天文历库；节气交界日、真太阳时、农历换算仍需后续校准。",
        "MBTI 倾向来自轻量自评题和行为倾向，不等同正式心理测评。",
        "报告只用于娱乐和自我反思，不应用于医疗、投资、法律或重大人生决策。",
        "大运、流年、流月等周期分析当前先做方向性提示，精确起运和顺逆排盘需要更完整的历法与性别规则。",
    ]
    if accuracy == "unknown":
        limits.append("出生时间不确定，涉及时柱、时柱十神和时间敏感结论的置信度已降低。")
    if "天干地支" not in focus_theories:
        limits.append("用户未重点选择天干地支，命理部分应保持简短。")
    return limits


def _pillar_label(value: str) -> str:
    return {"year": "年柱", "month": "月柱", "day": "日柱", "hour": "时柱"}.get(value, value)
