from __future__ import annotations

import json
from typing import Any

from mingyun_app.providers.base import ProviderResult


class MockProvider:
    def generate_json(self, messages: list[dict[str, str]], model_config: dict[str, Any]) -> ProviderResult:
        evidence_profile = _extract_evidence_profile(messages)
        bazi = evidence_profile.get("bazi") or {}
        pillars = bazi.get("pillars") or {}
        elements = evidence_profile.get("elements") or {}
        life_topics = evidence_profile.get("life_topics") or {}
        ten_gods = evidence_profile.get("ten_gods") or {}
        relationship_profile = evidence_profile.get("relationship_profile") or {}
        matchmaking = evidence_profile.get("matchmaking") or {}

        content = {
            "title": "命运测试报告",
            "summary": "这是基于本地可计算证据生成的离线示例报告。真实模型只能扩写这些证据，不应自行补充未计算结论。",
            "truthfulness_note": "结论来自四柱、生肖、节气、藏干、五行权重、十神关系、星座和心理自评；近似项会明确标注。",
            "plain_takeaways": {
                "direct_answer": "你的报告更适合当作自我观察清单，不是命令式预测。",
                "key_points": [
                    "土、火信号较明显，做事更看重责任和结果。",
                    "亲密关系里要注意别把责任感变成压力。",
                    "事业和财务建议应落实到计划、预算和反馈。",
                ],
                "suggested_actions": [
                    "先选一条最像自己的结论，观察一周。",
                    "把事业或感情建议改成一个今天能做的小动作。",
                    "遇到重大决定时，用现实信息校验报告。",
                ],
                "do_not_overread": [
                    "这不是绝对命运预测。",
                    "不能替代医疗、投资、法律建议。",
                    "出生时间不准时，部分结论会变弱。",
                ],
            },
            "chart_overview": _chart_overview(bazi),
            "derived_facts": _derived_facts(bazi, elements, ten_gods),
            "dimensions": [
                {
                    "id": "personality",
                    "title": "性格底色",
                    "claim": life_topics.get("personality", {}).get(
                        "signal", "优先把命盘证据解释为可观察的行为倾向，而不是宿命判断。"
                    ),
                    "basis": life_topics.get("personality", {}).get("basis", ["日主", "五行分布", "心理自评"]),
                    "confidence": life_topics.get("personality", {}).get("confidence", 0.66),
                    "limits": ["离线示例不会生成额外命理断言。"],
                    "suggestions": ["把长期目标拆成 30 天可验证的小实验。"],
                }
            ],
            "life_topics": _life_topic_cards(life_topics),
            "relationship_profile": relationship_profile,
            "matchmaking": matchmaking,
            "cross_theory": {
                "aligned": ["四柱、五行、十神和心理自评都只作为倾向证据，不能替代现实观察。"],
                "tensions": ["出生时间、节气交界和真太阳时会影响时柱及部分十神判断。"],
            },
            "questions_to_reflect": [
                "最近三个月，哪些决定更像来自责任感，哪些来自真实兴趣？",
                "在人际关系里，你更容易过度承担，还是回避表达需求？",
                "财务和职业选择中，哪些规则能帮你降低冲动？",
            ],
            "safety_notes": ["AI 生成，仅供娱乐和自我反思参考，不作为医疗、投资、法律或重大人生决策依据。"],
        }
        return ProviderResult(
            provider="mock",
            model=model_config.get("model_id", "mock-local"),
            content=content,
            raw_text="mock",
            usage={"input_tokens": 0, "output_tokens": 0, "estimated_cost_usd": 0},
        )


def _extract_evidence_profile(messages: list[dict[str, str]]) -> dict[str, Any]:
    for message in reversed(messages):
        if message.get("role") != "user":
            continue
        try:
            parsed = json.loads(message.get("content") or "{}")
        except json.JSONDecodeError:
            continue
        return parsed.get("evidence_profile") or {}
    return {}


def _chart_overview(bazi: dict[str, Any]) -> dict[str, Any]:
    pillars = bazi.get("pillars") or {}
    pillar_values = [
        pillars.get("year", {}).get("pillar"),
        pillars.get("month", {}).get("pillar"),
        pillars.get("day", {}).get("pillar"),
        pillars.get("hour", {}).get("pillar"),
    ]
    day_master = bazi.get("day_master") or {}
    zodiac = bazi.get("zodiac") or {}
    solar_term = bazi.get("solar_term") or {}
    current_term = (solar_term.get("current") or {}).get("name")
    return {
        "pillars": [value for value in pillar_values if value],
        "day_master": f"{day_master.get('stem', '')}日主 / {day_master.get('element_label', '')}",
        "zodiac": zodiac.get("animal", ""),
        "solar_term": current_term or "",
        "headline": "先看命盘结构，再看生活议题，所有判断都回到证据。",
    }


def _derived_facts(
    bazi: dict[str, Any], elements: dict[str, Any], ten_gods: dict[str, Any]
) -> list[dict[str, Any]]:
    strongest = sorted(elements.values(), key=lambda item: item.get("score", 0), reverse=True)[:3]
    visible_ten_gods = ten_gods.get("visible") or []
    return [
        {
            "title": "五行分布",
            "value": "、".join(f"{item.get('label')} {item.get('score')}" for item in strongest),
            "basis": ["四柱天干", "地支", "藏干加权"],
            "confidence": 0.72,
        },
        {
            "title": "藏干",
            "value": "；".join(f"{branch}:{'/'.join(stems)}" for branch, stems in (bazi.get("hidden_stems") or {}).items()),
            "basis": ["地支藏干表"],
            "confidence": 0.78,
        },
        {
            "title": "可见十神",
            "value": "、".join(f"{item.get('stem')}={item.get('ten_god')}" for item in visible_ten_gods[:4]),
            "basis": ["以日干为日主", "按五行生克与阴阳推导"],
            "confidence": 0.78,
        },
    ]


def _life_topic_cards(life_topics: dict[str, Any]) -> list[dict[str, Any]]:
    order = [
        "personality",
        "relationship",
        "career",
        "wealth",
        "health_energy",
        "study_growth",
        "social_family",
        "timing",
    ]
    return [
        {
            "id": key,
            "title": item.get("title", key),
            "insight": item.get("signal", ""),
            "basis": item.get("basis", []),
            "confidence": item.get("confidence", 0.5),
            "actionable_suggestions": _suggestions_for_topic(key),
            "limits": item.get("limits", ["这是由命盘证据推导出的倾向，不是绝对预测。"]),
        }
        for key in order
        if (item := life_topics.get(key))
    ]


def _suggestions_for_topic(key: str) -> list[str]:
    return {
        "personality": ["用一周记录验证报告中的行为倾向。"],
        "relationship": ["把亲密关系建议改写成可沟通的边界和需求。"],
        "career": ["把职业判断拆成技能、环境、压力源三个观察点。"],
        "wealth": ["只把财运内容当作资源管理提醒，不作投资判断。"],
        "health_energy": ["观察作息与压力节律，不作医疗判断。"],
        "study_growth": ["选择一个可输出的小项目验证学习方式。"],
        "social_family": ["区分支持关系和消耗关系。"],
        "timing": ["先看阶段主题，再结合现实计划调整。"],
    }.get(key, ["保留观察，不做绝对结论。"])
