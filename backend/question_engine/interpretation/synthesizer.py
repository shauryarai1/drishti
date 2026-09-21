"""Deterministic synthesis: one assessment from the relevant channel evidence.

No numeric scoring, no fake confidence. Evidence tags come from the knowledge
layer (supportive / caution / neutral), plus at most one supplementary Daily
Moon signal.
"""

from __future__ import annotations

from typing import Any, Dict, List

TOPIC_LABELS: Dict[str, str] = {
    "career": "your work situation",
    "money": "earnings and resources",
    "relationship": "your relationships",
    "decision": "this decision",
    "general_period": "the coming period",
    "personal": "the coming period",
    "general": "the coming period",
    "inner": "your inner state",
    "emotional": "how you are feeling",
    "obstacle": "the current difficulty",
    "home": "matters at home",
    "education": "your studies",
}

ASSESSMENTS = ("supportive", "mixed", "extra_care", "unclear")


def synthesize(evaluation: Dict[str, Any]) -> Dict[str, Any]:
    channels = evaluation.get("channels") or {}
    relevant = evaluation.get("relevant_channels") or {}
    primary = relevant.get("primary")
    supporting: List[str] = list(relevant.get("supporting") or [])

    used: List[str] = ([primary] if primary else []) + supporting[:1]
    evidence: List[str] = []
    for name in used:
        channel = channels.get(name) or {}
        if channel.get("available"):
            evidence.append(channel.get("assessment", "neutral"))

    # The Daily Moon rule contributes at most one additional signal.
    daily = evaluation.get("daily_moon_signal")
    if daily == "extra_care":
        evidence.append("caution")
    elif daily == "supportive":
        evidence.append("supportive")

    supportive = evidence.count("supportive")
    caution = evidence.count("caution")
    if supportive and caution:
        assessment = "mixed"
    elif caution:
        assessment = "extra_care"
    elif supportive:
        assessment = "supportive"
    else:
        assessment = "unclear"

    primary_channel = channels.get(primary or "") or {}
    main_theme = primary_channel.get("channel_interpretation")
    watch_for = list(primary_channel.get("watch_for") or [])
    caution_note = watch_for[0] if watch_for else None
    guidance = list(primary_channel.get("guidance") or [])
    guidance_note = guidance[0] if guidance else None

    topic = TOPIC_LABELS.get(evaluation.get("topic", ""), "your situation")
    return {
        "assessment": assessment,
        "topic_label": topic,
        "main_theme": main_theme,
        "caution": caution_note,
        "guidance": guidance_note,
        "evidence": evidence,
        "channels_used": used,
        "daily_moon_signal": daily,
        "provenance": {
            "synthesis": {"source_type": "kavach_custom", "source": "kavach_astrologer_rule", "status": "approved"},
            "knowledge": {"source_type": "standard_jyotish"},
        },
    }
