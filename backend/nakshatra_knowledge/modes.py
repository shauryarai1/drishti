"""Composition: house context (WHERE) x Nakshatra mode (HOW) [+ Navtara tone].

Deterministic templates only. The composer may use nothing beyond the concepts
supplied by the existing HOUSE_PATTERNS, the selected NakshatraProfile and the
optional Navtara tone - it never invents astrology, and Daily never depends on
an LLM.
"""

from __future__ import annotations

from typing import Mapping, Optional, Sequence

from .profiles import profile_for

# Presentation-only tones for the DAILY result. The Navtara engine, its names,
# CAUTION_TARAS, STRONGEST_CAUTION and meanings are NOT modified.
NAVTARA_DAILY_TONE: Mapping[str, Mapping[str, str]] = {
    "Janma": {"tone": "increased personal demand and attention",
              "guidance": "pace yourself and use your energy deliberately"},
    "Sampat": {"tone": "supportive growth and resources",
               "guidance": "constructive progress may come more easily"},
    "Vipat": {"tone": "friction or complication",
              "guidance": "move carefully and avoid unnecessary haste"},
    "Kshema": {"tone": "stability and security",
               "guidance": "good for consolidation and maintaining direction"},
    "Pratyari": {"tone": "obstacles or resistance",
                 "guidance": "remain flexible rather than forcing progress"},
    "Sadhaka": {"tone": "productive fulfilment",
                "guidance": "conditions may support completion and useful progress"},
    "Vadha": {"tone": "stronger resistance or limitation",
              "guidance": "use patience and discipline, and avoid unnecessary confrontation"},
    "Mitra": {"tone": "comfort and cooperation",
              "guidance": "conditions may feel more cooperative and emotionally manageable"},
    "AtiMitra": {"tone": "gain and productive momentum",
                 "guidance": "use favourable momentum constructively"},
}


def _join(items: Sequence[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def transit_mode_line(nakshatra: str) -> str:
    """One day-level line describing how today's lunar influence tends to express."""
    profile = profile_for(nakshatra)
    return f"Today's lunar pattern supports {_join(profile['mode'])}."


def navtara_tone(tara: Optional[str]) -> Optional[Mapping[str, str]]:
    """Presentation tone for a Navtara result (None when unknown)."""
    if not tara:
        return None
    return NAVTARA_DAILY_TONE.get(tara)


def compose_guidance(house_theme: str, nakshatra: str,
                     navtara: Optional[str] = None) -> str:
    """Compose one Rashi's daily guidance from the house context and the
    transit Nakshatra mode. The house reading is modified, never replaced."""
    profile = profile_for(nakshatra)
    parts = [
        f"{house_theme} stays the day's main area.",
        f"The current lunar pattern supports {_join(profile['mode'])} here, "
        f"so this can be a useful time for {_join(profile['focus'])}.",
        f"Extra care may help around {_join(profile['caution'])}.",
    ]
    tone = navtara_tone(navtara)
    if tone:
        parts.append(f"Personally, this is a phase of {tone['tone']} - {tone['guidance']}.")
    return " ".join(parts)
