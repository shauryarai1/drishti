"""KAVACH Nakshatra knowledge profiles (owner-approved transit abstractions).

These describe the MODE of the TRANSITING Moon, never a person's permanent
character. Nothing here is a GOOD/BAD label: every profile carries a core
theme, a constructive expression, a challenging expression, a behavioural mode,
a suitable focus and a caution.

Only the concepts the owner supplied are stored. `ruler` comes from the
existing authoritative NAKSHATRA_LORDS table (one source of truth) and
`zodiac_span` is derived from the canonical ordering - neither is duplicated
here. Deity and guna are deliberately ABSENT because no owner source for them
has been supplied.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Mapping, Tuple

from navtara.constants import NAKSHATRAS

# name -> the owner-approved concept sets (transit mode).
_PROFILES = {
    "Ashwini": {
        "core": ("initiation", "speed", "restoration", "action"),
        "constructive": ("quick response", "beginning", "helping", "restoring momentum"),
        "challenging": ("haste", "impulsiveness", "weak follow-through"),
        "mode": ("initiate", "accelerate", "restore"),
        "focus": ("beginnings", "action", "breaking stagnation"),
        "caution": ("rushing before enough attention has been given",),
    },
    "Bharani": {
        "core": ("carrying", "containing", "creating", "responsibility"),
        "constructive": ("endurance", "restraint", "responsibility", "handling demanding work"),
        "challenging": ("taking on too much", "pressure", "being caught in appearances"),
        "mode": ("carry", "contain", "create"),
        "focus": ("responsibilities", "sustained effort", "handling demanding matters"),
        "caution": ("unnecessary burden or pressure",),
    },
    "Krittika": {
        "core": ("cutting", "clarity", "purification", "discernment"),
        "constructive": ("decisiveness", "initiative", "removing what is unnecessary"),
        "challenging": ("impatience", "excessive criticism", "intolerance"),
        "mode": ("cut", "clarify", "purify"),
        "focus": ("decisions", "simplification", "correction", "removing obstacles"),
        "caution": ("becoming overly sharp or critical",),
    },
    "Rohini": {
        "core": ("growth", "creation", "nourishment", "development"),
        "constructive": ("creativity", "expression", "development", "making ideas tangible"),
        "challenging": ("possessiveness", "over-attachment", "imagination without action"),
        "mode": ("grow", "create", "nourish"),
        "focus": ("development", "creative work", "building something useful"),
        "caution": ("attachment or remaining only in imagination",),
    },
    "Mrigashira": {
        "core": ("search", "exploration", "discovery", "curiosity"),
        "constructive": ("investigation", "learning", "exploring alternatives", "movement"),
        "challenging": ("distraction", "uncertainty", "restlessness", "loss of continuity"),
        "mode": ("search", "explore", "discover"),
        "focus": ("research", "learning", "comparing options", "exploration"),
        "caution": ("scattered attention and repeated second-guessing",),
    },
    "Ardra": {
        "core": ("intensity", "effort", "transformation", "rebuilding"),
        "constructive": ("persistence", "confronting difficult work", "rebuilding"),
        "challenging": ("pushing excessively", "dissatisfaction", "imbalance"),
        "mode": ("intensify", "work through", "transform"),
        "focus": ("difficult tasks", "clearing problems", "rebuilding"),
        "caution": ("forcing progress or allowing intensity to dominate",),
    },
    "Punarvasu": {
        "core": ("renewal", "return", "restoration", "resetting"),
        "constructive": ("second chances", "recovering direction", "restoring what works"),
        "challenging": ("repeating an old cycle instead of genuinely renewing",),
        "mode": ("renew", "return", "restore"),
        "focus": ("resetting", "revisiting", "repairing", "beginning again intelligently"),
        "caution": ("mistaking repetition for progress",),
    },
    "Pushya": {
        "core": ("nourishment", "support", "consolidation", "strengthening"),
        "constructive": ("helping", "learning deeply", "sustaining", "strengthening"),
        "challenging": ("overcommitment", "doubt", "excessive caution", "attachment"),
        "mode": ("nourish", "support", "consolidate"),
        "focus": ("support", "learning", "strengthening foundations"),
        "caution": ("taking on more responsibility than necessary",),
    },
    "Ashlesha": {
        "core": ("binding", "penetration", "investigation", "depth"),
        "constructive": ("deep observation", "commitment", "protection",
                         "discovering what lies underneath"),
        "challenging": ("clinging", "possessiveness", "difficulty releasing"),
        "mode": ("bind", "penetrate", "investigate"),
        "focus": ("deep examination", "commitment", "understanding hidden complexity"),
        "caution": ("holding onto something beyond its usefulness",),
    },
    "Magha": {
        "core": ("honour", "preservation", "inheritance", "elevation"),
        "constructive": ("responsibility", "tradition", "management",
                         "improving an existing structure"),
        "challenging": ("living too much through the past", "losing attention to the present"),
        "mode": ("honour", "preserve", "elevate"),
        "focus": ("responsibility", "leadership", "maintaining valuable foundations"),
        "caution": ("allowing past expectations to control present decisions",),
    },
    "Purva Phalguni": {
        "core": ("enjoyment", "expression", "connection", "creativity"),
        "constructive": ("creativity", "sociability", "warmth", "generosity"),
        "challenging": ("overconfidence", "impulsiveness", "attempting too much"),
        "mode": ("enjoy", "express", "connect"),
        "focus": ("creative work", "social connection", "expression"),
        "caution": ("excess or overestimating capacity",),
    },
    "Uttara Phalguni": {
        "core": ("commitment", "organisation", "continuation", "responsibility"),
        "constructive": ("dependable cooperation", "agreements", "responsibility",
                         "sustaining progress"),
        "challenging": ("rigidity or carrying obligation too heavily",),
        "mode": ("commit", "organise", "sustain"),
        "focus": ("agreements", "cooperation", "long-term responsibilities"),
        "caution": ("turning responsibility into unnecessary burden",),
    },
    "Hasta": {
        "core": ("manifestation", "craftsmanship", "execution", "practical skill"),
        "constructive": ("practical action", "concentration", "adaptability",
                         "turning ideas into results"),
        "challenging": ("insecurity or unnecessary conflict around execution",),
        "mode": ("manifest", "craft", "execute"),
        "focus": ("hands-on work", "implementation", "practical completion"),
        "caution": ("trying to control every detail",),
    },
    "Chitra": {
        "core": ("design", "construction", "improvement", "creative structure"),
        "constructive": ("creativity", "craftsmanship", "recognising opportunities",
                         "improvement"),
        "challenging": ("ego", "judgment", "argument", "appearance over substance"),
        "mode": ("design", "build", "improve"),
        "focus": ("designing", "refining", "constructing", "improving"),
        "caution": ("prioritising presentation over substance",),
    },
    "Swati": {
        "core": ("independence", "adaptation", "learning", "movement"),
        "constructive": ("freedom", "flexibility", "communication", "learning through experience"),
        "challenging": ("restlessness", "stubborn independence", "indecision"),
        "mode": ("adapt independently", "learn", "move"),
        "focus": ("learning", "communication", "flexible independent action"),
        "caution": ("changing direction simply to avoid constraint",),
    },
    "Vishakha": {
        "core": ("focus", "purpose", "pursuit", "achievement"),
        "constructive": ("skill-building", "persistence", "meeting challenges",
                         "purposeful effort"),
        "challenging": ("excessive competitiveness", "restlessness", "fault-finding"),
        "mode": ("focus", "pursue", "achieve"),
        "focus": ("goals", "skill development", "concentrated effort"),
        "caution": ("turning purpose into unnecessary competition",),
    },
    "Anuradha": {
        "core": ("connection", "cooperation", "friendship", "bridging"),
        "constructive": ("communication", "partnership", "reconciliation",
                         "patient manifestation"),
        "challenging": ("sensitivity", "pressure", "tension between speed and patience"),
        "mode": ("connect", "bridge", "cooperate"),
        "focus": ("partnership", "teamwork", "communication", "repairing cooperation"),
        "caution": ("forcing harmony instead of building it patiently",),
    },
    "Jyeshtha": {
        "core": ("leadership", "protection", "responsibility", "governance"),
        "constructive": ("administration", "handling difficult situations",
                         "responsible leadership"),
        "challenging": ("dominance", "stubbornness", "reactive anger",
                        "excessive concern with image"),
        "mode": ("lead", "protect", "govern"),
        "focus": ("responsibility", "organisation", "difficult decisions"),
        "caution": ("turning responsibility into control",),
    },
    "Mula": {
        "core": ("roots", "investigation", "removal", "fundamental truth"),
        "constructive": ("research", "truth-seeking", "identifying and removing a root problem"),
        "challenging": ("harshness", "carelessness", "unnecessary destruction"),
        "mode": ("investigate", "uproot", "reach the root"),
        "focus": ("root-cause analysis", "research", "clearing fundamental problems"),
        "caution": ("destroying something that only needed correction",),
    },
    "Purva Ashadha": {
        "core": ("aspiration", "advocacy", "advancement", "enthusiasm"),
        "constructive": ("vision", "focused pursuit", "advice", "supporting others"),
        "challenging": ("impulsive decisions", "impatience", "susceptibility to praise"),
        "mode": ("aspire", "advocate", "advance"),
        "focus": ("vision", "encouragement", "purposeful advancement"),
        "caution": ("letting enthusiasm outrun judgment",),
    },
    "Uttara Ashadha": {
        "core": ("establishment", "accomplishment", "endurance", "integrity"),
        "constructive": ("steady advancement", "detailed work", "long-term accomplishment"),
        "challenging": ("rigidity and harshness",),
        "mode": ("establish", "accomplish", "endure"),
        "focus": ("long-term goals", "structured progress", "dependable execution"),
        "caution": ("becoming inflexible about how success must occur",),
    },
    "Shravana": {
        "core": ("listening", "learning", "communication", "connection"),
        "constructive": ("observation", "learning", "communication", "responsible execution"),
        "challenging": ("perfectionism", "sensitivity to criticism", "excessive talking"),
        "mode": ("listen", "learn", "communicate"),
        "focus": ("learning", "information", "conversation", "understanding before acting"),
        "caution": ("speaking before fully listening or demanding perfection",),
    },
    "Dhanishta": {
        "core": ("coordination", "organisation", "progress", "collective activity"),
        "constructive": ("teamwork", "adaptability", "organisation", "sharing",
                         "confident action"),
        "challenging": ("social influence", "excessive ambition", "flamboyance"),
        "mode": ("coordinate", "organise", "progress"),
        "focus": ("teamwork", "planning", "coordinated action", "forward movement"),
        "caution": ("letting status or social pressure dictate decisions",),
    },
    "Shatabhisha": {
        "core": ("examination", "correction", "independence", "restoration"),
        "constructive": ("problem-solving", "disciplined investigation",
                         "focused corrective work"),
        "challenging": ("secrecy", "fixed opinions", "isolation", "sudden reactions"),
        "mode": ("examine", "repair", "work independently"),
        "focus": ("analysis", "correction", "focused independent work"),
        "caution": ("withdrawing too far or becoming inflexible",),
    },
    "Purva Bhadrapada": {
        "core": ("commitment", "protection", "upliftment", "concentrated purpose"),
        "constructive": ("sincerity", "concentrated effort", "principled action",
                         "helping others"),
        "challenging": ("haste or overstepping",),
        "mode": ("commit", "protect", "uplift"),
        "focus": ("purposeful work", "principled action", "helping constructively"),
        "caution": ("pushing beyond appropriate limits",),
    },
    "Uttara Bhadrapada": {
        "core": ("stability", "depth", "foundation", "manifestation"),
        "constructive": ("patience", "dependability", "foundations",
                         "making subtle ideas practical"),
        "challenging": ("excessive slowness or carrying responsibility too heavily",),
        "mode": ("stabilise", "deepen", "manifest"),
        "focus": ("foundations", "patient implementation", "dependable completion"),
        "caution": ("allowing patience to become inactivity",),
    },
    "Revati": {
        "core": ("completion", "nourishment", "release", "transition"),
        "constructive": ("support", "care", "peaceful completion", "restoration"),
        "challenging": ("excessive expectations", "taking on others' burdens",
                        "weak initiative"),
        "mode": ("complete", "nourish", "release"),
        "focus": ("completion", "transition", "support", "bringing matters to a peaceful close"),
        "caution": ("absorbing responsibilities that belong to others",),
    },
}

# Canonical order + one immutable mapping, built from the existing ordering.
NAKSHATRA_PROFILES: Mapping[str, Mapping[str, Tuple[str, ...]]] = MappingProxyType({
    name: MappingProxyType(_PROFILES[name]) for name in NAKSHATRAS
})

PROFILE_FIELDS = ("core", "constructive", "challenging", "mode", "focus", "caution")


def profile_for(nakshatra: str) -> Mapping[str, Tuple[str, ...]]:
    """The transit profile for a canonical Nakshatra name (raises if unknown)."""
    from navtara.constants import canonical_nakshatra

    canonical = canonical_nakshatra(nakshatra)
    # canonical_nakshatra returns the input unchanged when unknown, so the
    # membership check is what rejects a Rashi or any non-Nakshatra name.
    if canonical not in NAKSHATRA_PROFILES:
        raise ValueError(f"Unknown Nakshatra: {nakshatra!r}")
    return NAKSHATRA_PROFILES[canonical]
