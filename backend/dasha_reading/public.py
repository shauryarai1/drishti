"""Customer-safe renderer for the Current Dasha Reading.

Deterministic synthesis of the three private classifications - no scores, no
good/bad labels, no methodology, no private terminology.
"""

from __future__ import annotations

from typing import Any, Dict, List

SUPPORTIVE = ("Sampat", "Kshema", "Sadhaka", "Mitra", "AtiMitra")
CAUTION = ("Vipat", "Pratyari", "Vadha")

SUPPORTS_TEXT: Dict[str, str] = {
    "Sampat": "Resources and practical matters can move in a more helpful direction.",
    "Kshema": "There can be more room for security, comfort and personal wellbeing.",
    "Sadhaka": "Progress comes through consistent effort and clear decisions.",
    "Mitra": "You may find it easier to support and cooperate with the people around you.",
    "AtiMitra": "Cooperation and help from other people can be easier to receive.",
}

CARE_TEXT: Dict[str, str] = {
    "Vipat": "Some plans may meet friction or misunderstanding, so detail and timing deserve attention.",
    "Pratyari": "Expectations may not always be met at once, and patience with others matters.",
    "Vadha": "One theme of this phase is more demanding and benefits from additional care.",
}

SELF_TEXT = "Attention may turn toward your own state, habits and personal direction."

GUIDANCE_TEXT: Dict[str, str] = {
    "effort": "Work with the period rather than against it: steady effort suits this phase better than pushing for quick results.",
    "resource": "Practical and resource-related matters are worth organising during this phase.",
    "patience": "Where something resists, give it space instead of forcing it.",
    "cooperation": "Let support from other people play a real part rather than carrying everything alone.",
    "personal": "Keeping your own wellbeing steady will help the rest of the phase run more smoothly.",
}

HEADLINES: Dict[str, str] = {
    "supportive": "A Phase That Favours Steady Progress",
    "mixed": "Progress With Patience",
    "caution": "A Demanding Phase That Rewards Care",
    "personal": "A Phase of Personal Reorientation",
    "cooperative": "A Phase Supported by Other People",
    "outward_support": "A Phase Where You Support Others",
    "effort": "A Phase Built on Consistent Effort",
}


def _opens(phases: List[str]) -> str:
    if not phases:
        return "This phase carries no strongly marked theme."
    single = {
        "supportive": "During this phase the general tone is supportive.",
        "mixed": "This phase mixes support with stretches that ask for patience.",
        "caution": "This phase asks for more care than usual.",
        "personal": "During this phase the focus turns inward.",
        "cooperative": "This phase leans on cooperation with other people.",
        "effort": "This phase is shaped by the effort you put in.",
    }
    return single.get(phases[0], "During this phase the tone is mixed.")


def render_reading(private: Dict[str, Any]) -> Dict[str, Any]:
    """Build the public DTO from the private classification."""
    taras = [item["tara"] for item in private.get("lordNakshatras", [])]
    supportive = [tara for tara in taras if tara in SUPPORTIVE]
    caution = [tara for tara in taras if tara in CAUTION]
    janma = [tara for tara in taras if tara == "Janma"]

    supports: List[str] = []
    for tara in supportive:
        text = SUPPORTS_TEXT.get(tara)
        if text and text not in supports:
            supports.append(text)
    if janma:
        supports.append(SELF_TEXT)

    care: List[str] = []
    for tara in caution:
        text = CARE_TEXT.get(tara)
        if text and text not in care:
            care.append(text)

    # headline bucket, precedence: caution > personal > cooperation > effort > all-supportive
    if caution and supportive:
        phases = ["mixed"]
    elif caution:
        phases = ["caution"]
    elif janma:
        phases = ["personal"]
    elif "AtiMitra" in supportive:
        phases = ["cooperative"]
    elif "Mitra" in supportive:
        phases = ["outward_support"]
    elif "Sadhaka" in supportive:
        phases = ["effort"]
    elif supportive:
        phases = ["supportive"]
    else:
        phases = []

    headline = HEADLINES.get(phases[0], "A Mixed Phase") if phases else "A Mixed Phase"

    summary_parts = [_opens(phases)]
    for tara in dict.fromkeys(taras):
        if tara in SUPPORTS_TEXT:
            summary_parts.append(SUPPORTS_TEXT[tara])
        elif tara in CARE_TEXT:
            summary_parts.append(CARE_TEXT[tara])
        elif tara == "Janma":
            summary_parts.append(SELF_TEXT)
    summary = " ".join(summary_parts)

    guidance_keys: List[str] = []
    if "Sadhaka" in supportive:
        guidance_keys.append("effort")
    if "Sampat" in supportive:
        guidance_keys.append("resource")
    if caution:
        guidance_keys.append("patience")
    if "Mitra" in supportive or "AtiMitra" in supportive:
        guidance_keys.append("cooperation")
    if janma:
        guidance_keys.append("personal")
    if not guidance_keys:
        guidance_keys.append("patience")
    guidance = " ".join(GUIDANCE_TEXT[key] for key in guidance_keys[:2])

    mahadasha = private.get("mahadasha") or {}
    antardasha = private.get("antardasha") or {}
    return {
        "asOf": private.get("asOf"),
        "timezone": private.get("timezone"),
        "mahadasha": {
            "name": mahadasha.get("lord"),
            "start": mahadasha.get("start"),
            "end": mahadasha.get("end"),
        },
        "antardasha": {
            "name": antardasha.get("lord"),
            "start": antardasha.get("start"),
            "end": antardasha.get("end"),
        },
        "headline": headline,
        "summary": summary,
        "supports": supports,
        "care": care,
        "guidance": guidance,
        "methodologyVersion": "public-current-dasha-v1",
    }
