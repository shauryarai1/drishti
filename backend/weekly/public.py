"""Customer-safe weekly output.

The public DTO contains NO private fields at all - privacy is structural, not a
text filter. Internal Tara names, positions and special roles never enter it.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from .models import MoonPeriod, WeeklyForecast

# Private classification -> customer-safe tone (3 levels only).
TONE_BY_TARA: Dict[str, str] = {
    "Janma": "personal",
    "Sampat": "supportive",
    "Vipat": "caution",
    "Kshema": "supportive",
    "Pratyari": "caution",
    "Sadhaka": "supportive",
    "Vadha": "strong_caution",
    "Mitra": "supportive",
    "AtiMitra": "supportive",
}

# Customer-safe guidance. These are tendencies, never guaranteed events.
GUIDANCE_BY_TARA: Dict[str, str] = {
    "Janma": ("A more personally focused period. Your own priorities, thoughts and "
              "wellbeing may need more attention."),
    "Sampat": ("Resources and practical matters receive a more supportive pattern. It can "
               "be useful to focus on money, useful opportunities or things that improve stability."),
    "Vipat": ("Move more carefully during this period. Misunderstandings or unexpected "
              "resistance can make rushed decisions less helpful."),
    "Kshema": ("A more supportive and comfortable period, especially for matters connected "
               "with personal happiness, security and wellbeing."),
    "Pratyari": ("You may meet more resistance from people or circumstances. Avoid forcing "
                 "agreement and give important decisions enough space."),
    "Sadhaka": ("A productive period for applying effort and moving something forward. "
                "Progress is better supported when you actively work toward the result."),
    "Vadha": ("This is a more demanding period. Important matters deserve extra care, and "
              "major new beginnings are better approached conservatively when possible."),
    "Mitra": ("You may be in a stronger position to support, cooperate with or help other "
              "people during this period."),
    "AtiMitra": ("Support from other people is stronger during this period. Cooperation, "
                 "assistance or helpful responses may be easier to receive."),
}

HEADLINES: Dict[str, str] = {
    "caution_supportive": "Take It Slowly Early, Better Flow Later",
    "supportive_caution": "Use the Earlier Part of the Day Well",
    "supportive_supportive": "A Generally Supportive Day",
    "caution_caution": "A Day for Patience and Care",
    "personal_supportive": "Personal Focus Gives Way to Practical Progress",
    "supportive_personal": "A Steady Personal Focus Later",
    "strong_caution_any": "A Day for Extra Care and Patience",
}

HIGHLIGHT_LABELS: Dict[str, str] = {
    "Vadha": "Extra Care",
    "Vipat": "Extra Care",
    "Pratyari": "Extra Care",
    "Kshema": "Supportive Window",
    "AtiMitra": "Support From Others",
    "Mitra": "Support From Others",
    "Sadhaka": "Good for Focused Effort",
    "Sampat": "Practical/Resource Focus",
}

WEEK_SUMMARY_TEMPLATES: Dict[str, str] = {
    "supportive": "This week holds supportive windows that are better used than waited on.",
    "caution": "Parts of this week ask for patience and a slower pace.",
    "strong_caution": "One stretch this week calls for extra care with important matters.",
    "personal": "Some of this week turns your attention back toward your own needs.",
    "mixed": "This week mixes supportive stretches with periods that ask for more care.",
}

BUCKET_ORDER = ("supportive", "personal", "caution", "strong_caution")

# Customer-safe sentence per highlight label (no methodology).
HIGHLIGHT_TEXT: Dict[str, str] = {
    "Extra Care": "Important matters deserve extra care during this stretch.",
    "Supportive Window": "Interactions and cooperation become easier during this period.",
    "Good for Focused Effort": "Progress is better supported when you actively work toward it.",
    "Support From Others": "Help, cooperation or favourable responses may be easier to receive.",
    "Practical/Resource Focus": "A useful stretch for practical matters and resources.",
}


def _label(moment: datetime) -> str:
    hour = moment.hour
    if hour < 6:
        return "Early Morning"
    if hour < 12:
        return "Morning"
    if hour < 17:
        return "Afternoon"
    if hour < 21:
        return "Evening"
    return "Night"


def _clock(iso: str) -> str:
    return iso[11:16]


def _bucket(tone: str) -> str:
    return tone if tone in BUCKET_ORDER else "personal"


def _day_headline(tones: List[str]) -> str:
    if not tones:
        return "A Steady Day"
    first, last = tones[0], tones[-1]
    if "strong_caution" in tones:
        return HEADLINES["strong_caution_any"]
    if len(tones) == 1:
        if first == "supportive":
            return HEADLINES["supportive_supportive"]
        if first == "caution":
            return HEADLINES["caution_caution"]
        return "A Day for Personal Focus"
    key = f"{first}_{last}"
    if key in HEADLINES:
        return HEADLINES[key]
    if first == "caution":
        return HEADLINES["caution_supportive"]
    if last == "caution":
        return HEADLINES["supportive_caution"]
    return HEADLINES["supportive_supportive"]


def _public_period(period: MoonPeriod) -> Dict[str, Any]:
    tone = TONE_BY_TARA.get(period.tara, "personal")
    start = datetime.fromisoformat(period.start)
    return {
        "label": _label(start),
        "start": _clock(period.start),
        "end": _clock(period.end) if period.end != period.start else _clock(period.start),
        "afterTime": _clock(period.start),
        "headline": HEADLINES.get("strong_caution_any") if tone == "strong_caution" else {
            "supportive": "Well supported",
            "caution": "Take it steadily",
            "personal": "Turn attention inward",
        }.get(tone, "Take it steadily"),
        "guidance": GUIDANCE_BY_TARA.get(period.tara, ""),
        "tone": tone,
    }


def to_public(week: WeeklyForecast) -> Dict[str, Any]:
    """Customer-safe week. Contains no private fields by construction."""
    days: List[Dict[str, Any]] = []
    counts = {bucket: 0 for bucket in BUCKET_ORDER}
    highlights: List[Dict[str, str]] = []
    seen_labels = set()

    for day in week.days:
        tones = [TONE_BY_TARA.get(period.tara, "personal") for period in day.periods]
        for tone in tones:
            counts[_bucket(tone)] += 1
        periods = [_public_period(period) for period in day.periods]

        # week highlights use customer-safe labels only
        for period in day.periods:
            label = HIGHLIGHT_LABELS.get(period.tara)
            if label and label not in seen_labels:
                seen_labels.add(label)
                highlights.append({
                    "label": label,
                    "date": day.date,
                    "time": _clock(period.start),
                    "text": HIGHLIGHT_TEXT.get(label, ""),
                })

        days.append({
            "date": day.date,
            "headline": _day_headline(tones),
            "summary": _day_summary(periods),
            "periods": periods,
        })

    dominant = max(counts, key=lambda key: counts[key]) if any(counts.values()) else "mixed"
    summary = WEEK_SUMMARY_TEMPLATES.get(dominant, WEEK_SUMMARY_TEMPLATES["mixed"])
    if counts["supportive"] and (counts["caution"] or counts["strong_caution"]):
        summary = WEEK_SUMMARY_TEMPLATES["mixed"]

    return {
        "startDate": week.start_date,
        "endDate": week.days[-1].date if week.days else week.start_date,
        "timezone": week.timezone,
        "days": days,
        "weekSummary": summary,
        "highlights": highlights,
        "methodologyVersion": "public-weekly-v1",
    }


def _day_summary(periods: List[Dict[str, Any]]) -> str:
    if not periods:
        return ""
    if len(periods) == 1:
        return periods[0]["guidance"]
    first, last = periods[0], periods[-1]
    return (
        f"Until {first['end']}, {first['guidance'].rstrip('.')}. "
        f"From {last['start']} onward, {last['guidance'].rstrip('.').lower()}"
    )
