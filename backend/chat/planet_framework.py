"""Owner-defined KAVACH Nine Planet Interpretation Framework.

Authoritative basic planetary-definition layer for Ask KAVACH.

This module is INTERPRETATION ONLY. It never calculates, never derives and
never alters a chart fact. Every placement (sign, house, degree, motion,
Lagna, Nakshatra, dasha) still comes exclusively from the existing KAVACH
Kundli engine (`kundli.build_kundli` - Swiss Ephemeris, Lahiri ayanamsha).

What this layer defines is WHAT each of the nine grahas fundamentally
represents in KAVACH, so Ask reasons from the owner's framework instead of
falling back to generic internet/Parashari astrology.

It is a BASIC layer. It does NOT replace or override any other owner-defined
KAVACH system - BNN, Navtara, directional relationships, retrograde rules,
combustion, Kartari, Atmakaraka, Yogakaraka, the Mars methodology, Dasha,
matchmaking or daily methodology. When another owner rule is applicable the
layers COMPOSE.

Definitions are stored here centrally (never scattered through route
handlers) so the provider prompt can be built deterministically. The public
answer must apply this reasoning to real placements - it must not recite the
definitions back as canned dictionary entries.
"""

from __future__ import annotations

from typing import Dict, List

FRAMEWORK_NAME = "KAVACH Nine Planet Interpretation Framework"

# The nine grahas in KAVACH order. Luna nodes are included: KAVACH treats
# Rahu and Ketu as full interpretive factors.
PLANETS: tuple = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
    "Rahu", "Ketu",
)

# Short mnemonic map. Mnemonic ONLY - see PLANET_MEANINGS for the
# authoritative definitions.
SHORT_MAP: Dict[str, str] = {
    "Sun": "REGULAR ACTIONS",
    "Moon": "CREATION",
    "Mars": "INNER SATISFACTION + ASPIRATIONS",
    "Mercury": "SKILLS + EXPERTISE / TOOL OF VICTORY",
    "Jupiter": "INNER-CIRCLE ASSOCIATIONS",
    "Venus": "OUTER CONNECTIONS",
    "Saturn": "NECESSITY + PRESSURE + MOTIVATION",
    "Rahu": "CONNECT + HOLD + STRENGTHEN + PURSUE",
    "Ketu": "PAST-LIFE RESULTS + ACCEPTANCE",
}

# Authoritative owner definitions: core principle, the interpretive lens and
# the guardrails that keep public output responsible.
PLANET_MEANINGS: Dict[str, Dict[str, object]] = {
    "Sun": {
        "core": "REGULAR ACTIONS / LIFE ACTIVITY",
        "meaning": (
            "Sun represents the actions and activities a person regularly "
            "performs. Its placement shows activities that repeatedly exist in "
            "the person's life and that they need to perform; life tends to "
            "revolve around those significations."
        ),
        "interpret_through": (
            "regular activities",
            "repeated actions",
            "things the person needs to perform",
            "an important recurring area of life",
            "the significations around which life activity revolves",
        ),
        "guardrail": (
            "Do not reduce Sun merely to generic 'ego, father, authority' "
            "language when this framework applies."
        ),
    },
    "Moon": {
        "core": "CREATION",
        "meaning": (
            "Moon represents creation. Its placement shows what the person "
            "tends to create, develop, generate or bring into their life. Read "
            "the sign and the surrounding chart context through this creation "
            "principle; for example Moon in Libra can indicate creation through "
            "meeting people, interaction, relationships and connections with "
            "others."
        ),
        "interpret_through": (
            "creation",
            "creativity",
            "what the person develops or generates",
            "bringing something into being in the area indicated",
        ),
        "guardrail": (
            "Do not replace this owner meaning with generic emotional-Moon "
            "language as the primary interpretation."
        ),
    },
    "Mars": {
        "core": "INNER SATISFACTION / ASPIRATIONS",
        "meaning": (
            "Mars represents actions that provide inner satisfaction. Its "
            "placement indicates activities that can give the person a sense of "
            "inner satisfaction when handled constructively - work that may feel "
            "important to perform properly. Mars also represents aspirations."
        ),
        "interpret_through": (
            "inner satisfaction",
            "actions that create satisfaction",
            "aspirations",
            "constructive action in the area indicated by its placement",
        ),
        "guardrail": (
            "Never turn this into medical diagnosis. Never tell a user that "
            "sleep problems, distress or other health symptoms prove their Mars "
            "is bad. Keep the answer non-medical and non-deterministic."
        ),
    },
    "Mercury": {
        "core": "SKILLS / EXPERTISE / TOOL OF VICTORY",
        "meaning": (
            "Mercury represents skills and expertise. Its placement shows areas "
            "where skills can be developed, expressed or applied effectively, "
            "including the ability to use the right skill at the right time and "
            "in the right place (the owner's 'Tool of Victory' concept)."
        ),
        "interpret_through": (
            "skills",
            "expertise",
            "practical application of ability",
            "using intelligence and skill appropriately",
            "strategic use of one's capabilities",
        ),
        "guardrail": "",
    },
    "Jupiter": {
        "core": "INNER CIRCLE / ASSOCIATION / COLLABORATION",
        "meaning": (
            "Jupiter represents the person's associations with their inner "
            "circle: family, friends, extended family, close and supportive "
            "people, collaboration with one's own people, and the respect and "
            "value given within that circle. It can also represent a "
            "comfort-zone type of association."
        ),
        "interpret_through": (
            "inner-circle associations",
            "collaboration with one's own people",
            "respect and value among close people",
            "family and extended-family association",
            "supportive, comfort-zone association",
        ),
        "guardrail": (
            "Preserve the owner distinction: VENUS is connection with the OUTER "
            "world/circle in pursuit of desires and goals; JUPITER is "
            "association with the INNER circle, collaboration, respect and "
            "value. Do not merge them."
        ),
    },
    "Venus": {
        "core": "CONNECTIONS / DESIRES / OUTER CIRCLE",
        "meaning": (
            "Venus represents the connections a person creates with the outer "
            "world, often developed in relation to goals, desires, things the "
            "person wants to achieve, and people or resources outside the "
            "immediate inner circle. Its placement shows where and how those "
            "outer connections are built."
        ),
        "interpret_through": (
            "connections",
            "outer-world connection building",
            "desires and goals pursued through others",
            "people and resources outside the inner circle",
        ),
        "guardrail": (
            "Outer circle. The INNER circle belongs to Jupiter - keep the "
            "distinction explicit when both are relevant."
        ),
    },
    "Saturn": {
        "core": "NECESSITY / PRESSURE / MOTIVATION",
        "meaning": (
            "Saturn represents areas where circumstances create pressure or "
            "necessity to act. Its placement can indicate responsibilities or "
            "activities the person feels compelled to handle because they are "
            "necessary - work that cannot simply be ignored."
        ),
        "interpret_through": (
            "necessity",
            "requirement",
            "responsibility",
            "pressure",
            "motivation created by circumstances",
            "work that cannot simply be ignored",
        ),
        "guardrail": (
            "Avoid fatalistic wording such as 'you have no choice'. Prefer: "
            "'This can become an area where circumstances repeatedly require "
            "your attention.'"
        ),
    },
    "Rahu": {
        "core": "CONNECT / HOLD / STRENGTHEN / CHASE",
        "meaning": (
            "Rahu represents things the person wants to connect with, hold onto "
            "and strengthen. Its placement can show an area the person strongly "
            "wants to pursue, acquire, preserve or remain connected with - the "
            "owner's analogy is Rahu's pursuit of Amrit."
        ),
        "interpret_through": (
            "connector",
            "attachment",
            "strengthening",
            "pursuit",
            "strong desire",
            "holding onto something",
            "chasing something intensely",
        ),
        "guardrail": (
            "Express strong pursuit but avoid extreme deterministic wording "
            "such as 'You will get this at any cost.' Prefer: 'This can become "
            "an area of unusually strong pursuit or attachment.'"
        ),
    },
    "Ketu": {
        "core": "PAST-LIFE RESULTS / ACCEPTANCE",
        "meaning": (
            "Within KAVACH's Vedic astrology framework Ketu represents results "
            "carried from past-life karma. Its placement - sign, house and "
            "relevant planetary context - indicates matters interpreted as "
            "coming from previous-life results, where the person may experience "
            "less direct control and may need to approach matters with "
            "acceptance and gratitude."
        ),
        "interpret_through": (
            "past-life results",
            "carried karma",
            "reduced sense of control",
            "acceptance",
            "gratitude",
            "experiencing results rather than chasing them",
        ),
        "guardrail": (
            "Present past-life statements explicitly as part of KAVACH's Vedic "
            "astrology framework, not as scientifically established facts. Avoid "
            "frightening or fatalistic language. Prefer: 'In KAVACH's "
            "interpretive framework, this placement is associated with "
            "past-life results...' rather than 'You have no control and must "
            "suffer this.'"
        ),
    },
}

# How Ask must USE the framework. This is the part that stops the model from
# parroting the definitions back instead of interpreting a real chart.
USAGE_RULES: tuple = (
    "Reason from these definitions internally. Do not recite them back.",
    "Do not open an answer with 'Sun means regular activities' or similar "
    "dictionary phrasing unless the user specifically asks what that planet "
    "means in KAVACH.",
    "Combine the planet principle with the ACTUAL sign (manner/nature), the "
    "ACTUAL house (area of life) and any other applicable owner-authorized "
    "KAVACH rule, then state what that means for this person's situation.",
    "When another owner-defined KAVACH rule is applicable (BNN, Navtara, "
    "directional relationships, retrograde, combustion, Kartari, Atmakaraka, "
    "Yogakaraka, the Mars methodology, Dasha, node/dispositor rules), COMPOSE "
    "the layers. Never delete or replace an owner rule with this basic layer.",
    "Do not keyword-match one sentence to one planet and answer immediately. "
    "Identify what genuinely bears on the question, then synthesise.",
    "Several planets can explain one problem at once. Explain the interaction "
    "naturally; never say 'your problem is because Mars is bad'.",
    "For a full Kundli overview, broader coverage of all nine is appropriate. "
    "For a focused question, use only the relevant factors - never pad with "
    "planets that have no bearing on it.",
)

# A problem lens: which KAVACH principles are likely to bear on a personal
# question. Used only to GUIDE reasoning, never as a lookup table.
PROBLEM_LENS: Dict[str, tuple] = {
    "career_work": ("Sun", "Saturn", "Mercury", "Mars"),
    "relationships": ("Venus", "Jupiter", "Moon"),
    "satisfaction_purpose": ("Mars", "Moon", "Sun"),
    "money_resources": ("Venus", "Jupiter", "Mercury"),
    "obsession_persistence": ("Rahu", "Saturn"),
    "responsibility_recurrence": ("Saturn", "Sun"),
    "family_inner_circle": ("Jupiter", "Moon"),
    "letting_go_acceptance": ("Ketu", "Rahu"),
    "skills_direction": ("Mercury", "Mars", "Sun"),
    "creation_output": ("Moon", "Mercury"),
}

_LENS_KEYWORDS: Dict[str, tuple] = {
    "career_work": ("career", "job", "work", "promotion", "profession", "business"),
    "relationships": ("relationship", "marriage", "partner", "friend", "friendship", "love"),
    "satisfaction_purpose": ("satisf", "fulfil", "purpose", "meaning", "unhappy", "unstuck"),
    "money_resources": ("money", "finance", "income", "savings", "wealth", "rich"),
    "obsession_persistence": ("chasing", "obsess", "can't let go", "keep going after", "craving"),
    "responsibility_recurrence": ("responsib", "keep coming back", "again and again", "burden", "duty"),
    "family_inner_circle": ("family", "relative", "parents", "sibling", "my people"),
    "letting_go_acceptance": ("let go", "leave this", "stuck in this", "move on", "accept"),
    "skills_direction": ("skill", "expert", "what should i focus", "good at", "talent"),
    "creation_output": ("create", "build", "start something", "project", "write"),
}


def meaning_for(planet: str) -> Dict[str, object]:
    """Owner definition for one graha (empty dict for an unknown name)."""
    return PLANET_MEANINGS.get(planet) or {}


def core_for(planet: str) -> str:
    """Short KAVACH core meaning for one graha."""
    return str(meaning_for(planet).get("core") or "")


def relevant_lenses(question: str) -> List[str]:
    """KAVACH problem lenses plausibly bearing on this question.

    Guidance only - the model still has to establish relevance against the
    actual calculated chart. Returns [] when nothing is recognisable.
    """
    text = (question or "").lower()
    return [lens for lens, keywords in _LENS_KEYWORDS.items()
            if any(keyword in text for keyword in keywords)]


def planets_for_lenses(lenses: List[str]) -> List[str]:
    """Union of grahas implied by the given lenses, in KAVACH order."""
    wanted = set()
    for lens in lenses or ():
        wanted.update(PROBLEM_LENS.get(lens) or ())
    return [planet for planet in PLANETS if planet in wanted]


def context_block() -> str:
    """Deterministic framework block for Ask's astrology context.

    Supplied alongside the calculated chart so the model reasons from KAVACH's
    definitions rather than remembering them from a vague system prompt.
    """
    lines = [
        f"[{FRAMEWORK_NAME} - KAVACH's authoritative basic planetary "
        "interpretation definitions. These define what each graha fundamentally "
        "means in KAVACH; apply them, do not recite them.]",
        "",
        "Short internal map (mnemonic only):",
    ]
    lines += [f"- {planet} = {SHORT_MAP[planet]}" for planet in PLANETS]
    lines += ["", "Authoritative definitions and how to read them:"]
    for planet in PLANETS:
        entry = PLANET_MEANINGS[planet]
        lines.append("")
        lines.append(f"{planet} - {entry['core']}")
        lines.append(str(entry["meaning"]).strip())
        lines.append("Interpret through: "
                     + ", ".join(str(item) for item in entry["interpret_through"]) + ".")
        if entry.get("guardrail"):
            lines.append(str(entry["guardrail"]).strip())
    lines += ["", "How to use this framework:"]
    lines += [f"- {rule}" for rule in USAGE_RULES]
    lines += [
        "",
        "Every placement, sign, house, degree, motion, Lagna, Nakshatra and "
        "dasha named in your answer must come from the calculated KAVACH chart "
        "supplied with this message. This framework interprets those facts; it "
        "never lets you derive a placement yourself.",
    ]
    return "\n".join(lines)


def lens_hint(question: str) -> str:
    """Short deterministic nudge about which principles may bear on a question.

    Returned only when the question recognisably maps to a KAVACH lens, and
    framed as guidance so it never becomes a rigid one-planet lookup.
    """
    lenses = relevant_lenses(question)
    if not lenses:
        return ""
    planets = planets_for_lenses(lenses)
    names = ", ".join(planets)
    return (
        "[KAVACH reasoning lens - guidance only, not a verdict] Themes that may "
        f"bear on this question: {', '.join(lenses)}. Graha principles worth "
        f"testing against the calculated chart: {names}. Establish which are "
        "genuinely supported by the real placements before using them, several "
        "may combine, and ignore any that the chart does not support."
    )
