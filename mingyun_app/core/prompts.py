from __future__ import annotations

import json
from typing import Any


def build_reading_prompt(payload: dict[str, Any]) -> list[dict[str, str]]:
    evidence_profile = payload.get("evidence_profile") or {}
    style = payload.get("style") or "balanced"
    mysticism_level = int(payload.get("mysticism_level") or 50)
    system = (
        "你是《命运》测试软件的解释层。你不是自由算命师，"
        "只能解释用户提供的 evidence_profile。你必须输出合法 JSON。"
    )
    user = {
        "task": "基于 evidence_profile 生成命运/性格测试报告。",
        "hard_rules": [
            "不得编造 evidence_profile 中不存在的出生事实、干支、星盘、心理结果。",
            "每条重要结论必须包含依据、置信度和适用边界。",
            "不得为了情绪价值迎合用户，不得输出绝对化预测。",
            "不得提供医疗、法律、投资、死亡、灾祸等高风险断言。",
            "必须返回 json，不要输出 markdown，不要在 JSON 外添加文字。",
            "若 evidence_profile 标注为近似或缺失，必须在对应模块写出限制。",
            "请把术语翻译成普通用户能理解的表达，但保留关键依据名称。",
            "面向普通大众写作：先说结论，再说依据；少用术语，必须用短句、白话、可执行建议。",
            "避免绕口表达。每个核心模块都要回答：这说明什么、对我有什么用、我接下来可以怎么做。",
        ],
        "style": style,
        "mysticism_level": mysticism_level,
        "required_schema": {
            "title": "string",
            "summary": "string",
            "truthfulness_note": "string",
            "plain_takeaways": {
                "direct_answer": "string",
                "key_points": ["string"],
                "suggested_actions": ["string"],
                "do_not_overread": ["string"],
            },
            "chart_overview": {
                "pillars": ["string"],
                "day_master": "string",
                "zodiac": "string",
                "solar_term": "string",
                "headline": "string",
            },
            "derived_facts": [
                {
                    "title": "string",
                    "value": "string",
                    "basis": ["string"],
                    "confidence": 0.0,
                }
            ],
            "dimensions": [
                {
                    "id": "string",
                    "title": "string",
                    "claim": "string",
                    "basis": ["string"],
                    "confidence": 0.0,
                    "limits": ["string"],
                    "suggestions": ["string"],
                }
            ],
            "life_topics": [
                {
                    "id": "personality|relationship|career|wealth|health_energy|study_growth|social_family|timing",
                    "title": "string",
                    "insight": "string",
                    "basis": ["string"],
                    "confidence": 0.0,
                    "actionable_suggestions": ["string"],
                    "limits": ["string"],
                }
            ],
            "relationship_profile": {
                "title": "string",
                "partner_star": "string",
                "relationship_tone": "string",
                "day_branch_pairing": {"self_day_branch": "string", "six_harmony_branch": "string", "basis": "string"},
                "needs_to_balance": ["string"],
                "risk_notes": ["string"],
                "confidence": 0.0,
                "limits": ["string"],
            },
            "matchmaking": {
                "title": "string",
                "target_gender": "string",
                "recommended_elements": [
                    {
                        "label": "string",
                        "reason": "string",
                        "candidate_day_stems": ["string"],
                    }
                ],
                "favorable_branches": [{"branch": "string", "reason": "string"}],
                "partner_ten_god_focus": "string",
                "avoid_overemphasis": ["string"],
                "screening_questions": ["string"],
                "confidence": 0.0,
                "basis": ["string"],
            },
            "cross_theory": {"aligned": ["string"], "tensions": ["string"]},
            "questions_to_reflect": ["string"],
            "safety_notes": ["string"],
        },
        "content_guidance": {
            "chart_overview": "浓缩四柱、日主、生肖、节气，作为报告顶部摘要。",
            "plain_takeaways": "用直白语言写给普通用户。direct_answer 不超过 60 字；key_points 每条不超过 35 字；suggested_actions 必须是能立即做的小动作；do_not_overread 提醒不要把倾向当命令。",
            "derived_facts": "解释藏干、五行、十神这些推导事实，必须来自 evidence_profile。",
            "life_topics": "覆盖用户高频关注的性格、婚恋、事业、财运、身心节律、学习成长、人际家庭、阶段建议。",
            "relationship_profile": "单独输出姻缘分析，只能解释伴侣星、日支关系宫、五行补偏和心理自评。",
            "matchmaking": "输出更匹配的异性八字画像：建议五行、日主倾向、地支加分项和筛选问题，不要承诺具体对象。",
            "questions_to_reflect": "给 3-5 个低风险自我观察问题，避免宿命式结论。",
        },
        "evidence_profile": evidence_profile,
    }
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
    ]
