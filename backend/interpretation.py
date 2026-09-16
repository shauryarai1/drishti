"""DRISHTI's user-facing interpretation copy and Mars Rule mapping."""

from __future__ import annotations

from typing import Any, Dict

from calculator import generate_chart
from models import BirthData
from timing import calculate_caution_windows


# These meanings are the source of truth for all three interpretation layers.
RASHI_GUIDANCE: Dict[str, Dict[str, str]] = {
    "Aries": {
        "area": "Impulsive decisions and unnecessary risks",
        "attention": "Do not act without thinking. Avoid impulsive decisions and unnecessary risks. Acting too quickly without considering the consequences can put you in difficult situations.",
        "protect": "Create stronger boundaries around quick decisions and unnecessary risks. Slow down before acting, and do not let pressure push you into a choice without thinking about the consequences.",
        "danger": "Be especially careful with impulsive decisions and unnecessary risks. Acting too quickly without considering the consequences can create serious problems. Ignoring the boundaries highlighted above can make this area harder to handle.",
    },
    "Taurus": {
        "area": "Food, speech, money, and savings",
        "attention": "Pay special attention to what you eat and drink. Be careful with your words, money matters, and savings. Carelessness in these areas can create problems for you.",
        "protect": "Create stronger boundaries around spending, saving, food, and speech. Avoid excess and do not make money-related decisions emotionally.",
        "danger": "Be especially careful with food, speech, money, and savings. Carelessness or excess in these areas can create bigger problems. Ignoring the boundaries highlighted above can make this area harder to handle.",
    },
    "Gemini": {
        "area": "Communication, arguments, and travel",
        "attention": "Be careful about what you say and whom you say it to. Avoid unnecessary arguments with people around you. Take extra care while travelling and do not be careless during journeys.",
        "protect": "Create boundaries around communication, arguments, and travel. Know when to stop an argument, think before speaking, and do not let carelessness take over during a journey.",
        "danger": "Be especially careful with communication, arguments, people around you, and travel. A careless conversation, unnecessary conflict, or lack of attention during a journey can create serious problems. Ignoring the boundaries highlighted above can make this area harder to handle.",
    },
    "Cancer": {
        "area": "Attachment, emotions, and decisions",
        "attention": "Your attachments and sensitive nature can create problems when they become too strong. The more emotionally attached you become, the harder it may be to think clearly. Avoid making important decisions purely from feelings and keep your emotional reactions under control.",
        "protect": "Create boundaries around attachment, emotional reactions, and decisions. Know when feelings are becoming too strong, and do not let craving or emotion push you beyond a healthy limit.",
        "danger": "Be especially careful when attachment, craving, or strong emotions start controlling your decisions. They can make problems harder to see clearly. Ignoring the boundaries highlighted above can make this area harder to handle.",
    },
    "Leo": {
        "area": "Comfort, enjoyment, showing off, and responsibility",
        "attention": "Be careful about becoming too focused on enjoyment, comfort, your comfort zone, or showing off. Avoid unnecessary politics and remember your responsibilities towards the people close to you.",
        "protect": "Create boundaries around comfort, enjoyment, showing off, and unnecessary politics. Know when to step out of your comfort zone and do not let these things distract you from your responsibilities.",
        "danger": "Be especially careful about too much comfort, enjoyment, showing off, or unnecessary politics. These can pull your attention away from important responsibilities and create bigger problems. Ignoring the boundaries highlighted above can make this area harder to handle.",
    },
    "Virgo": {
        "area": "Arguments, criticism, and correcting others",
        "attention": "Avoid unnecessary arguments and disputes. Do not constantly try to correct other people or point out every small mistake. This can create conflict and enemies. Pay attention to your own habits as well.",
        "protect": "Create boundaries around arguments, criticism, and the urge to correct others. Know when to stop. Taking these matters too far can create unnecessary conflict.",
        "danger": "You have many skills and significant potential. You can be an excellent worker and a valuable asset to an organisation, but lack of discipline and other unresolved weaknesses can prevent you from using that potential fully. If these weaknesses are repeatedly ignored, your plans, work and finances may face setbacks. Develop discipline, work consistently, correct weak areas, and understand the details of your work.",
    },
    "Libra": {
        "area": "Attraction, attachment, and relationships",
        "attention": "Be careful about becoming too strongly attracted or attached in relationships. Possessiveness, obsession, or trying to control your partner too much can damage the relationship. Maintain healthy boundaries.",
        "protect": "Create boundaries around attraction, attachment, and control in relationships. Give your partner space, and do not let possessiveness or obsession take over.",
        "danger": "Be especially careful about possessiveness, obsession, and trying to control a partner. These patterns can seriously damage a relationship. Ignoring the boundaries highlighted above can make this area harder to handle.",
    },
    "Scorpio": {
        "area": "Insecurity, jealousy, resentment, and mental strain",
        "attention": "Pay attention to feelings of insecurity. If insecurity grows, it can turn into jealousy, resentment, or revenge. Feeling constantly overworked or overburdened can also weaken your mental strength. Do not let your thinking become excessively negative, especially when dealing with sudden problems.",
        "protect": "Create boundaries around insecurity, jealousy, resentment, and mental strain. Know when to step back from overwork and negative thinking before they become harder to control.",
        "danger": "Be especially careful when insecurity turns into jealousy, resentment, or revenge. Overwork and excessively negative thinking can weaken your ability to handle sudden problems. Ignoring the boundaries highlighted above can make this area harder to handle.",
    },
    "Sagittarius": {
        "area": "Overconfidence, learning, and long journeys",
        "attention": "Do not let your knowledge make you overconfident. If you start believing you already know enough, you may stop learning and become careless. Take special care during long journeys and while visiting religious or spiritual places.",
        "protect": "Create boundaries around confidence, learning, and travel. Stay open to learning, check what you think you know, and take extra care during long journeys and visits to religious or spiritual places.",
        "danger": "Be especially careful when confidence turns into carelessness or when you stop learning. Take extra care during long journeys and while visiting religious or spiritual places. Ignoring the boundaries highlighted above can make this area harder to handle.",
    },
    "Capricorn": {
        "area": "Profession, workplace, and reputation",
        "attention": "Stay alert regarding your profession and workplace. Obstacles, controversies, office politics, or situations affecting your reputation may arise. Avoid unnecessarily becoming part of workplace disputes or scandals.",
        "protect": "Create boundaries around workplace disputes, office politics, and situations that can affect your reputation. Know when to stay out of a controversy and do not let professional pressure pull you into it.",
        "danger": "Your profession and workplace need serious attention. Stay away from unnecessary controversies, reputation problems, workplace disputes, and office politics. Carelessness here can create much bigger problems. Ignoring the boundaries highlighted above can make this area harder to handle.",
    },
    "Aquarius": {
        "area": "Communities, groups, trust, and loyalty",
        "attention": "Be careful about becoming too involved with communities, groups, or social circles. Be selective about whom you trust. Misunderstandings, betrayal, or people working against your interests can create problems.",
        "protect": "Create boundaries around community groups and social circles. Be selective about your involvement and do not trust everyone with your plans or personal matters.",
        "danger": "Be especially careful about groups, communities, and people you trust. Betrayal, misunderstandings, or people working against your interests can create serious problems. Ignoring the boundaries highlighted above can make this area harder to handle.",
    },
    "Pisces": {
        "area": "Ideals, rules, collaboration, stress, and sleep",
        "attention": "Your ideals, personal rules, or fixed way of thinking can sometimes make collaboration difficult. This can disturb your mental peace. Pay attention to stress and sleep, and do not allow rigid thinking to disturb your peace of mind.",
        "protect": "Create boundaries around ideals, personal rules, and fixed thinking. Make room for other people's views, and do not let stress or poor sleep take away your mental peace.",
        "danger": "Be especially careful when rigid thinking makes collaboration difficult or when stress and poor sleep build up. These problems can weaken your mental peace and make situations harder to handle. Ignoring the boundaries highlighted above can make this area harder to handle.",
    },
}

RASHI_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

AREA_TYPE_PRINCIPLES: Dict[str, str] = {
    "attention": "Mars concentrates energy here. This is a sensitive area requiring balance.",
    "protect": "Mars creates a strong protective and defensive instinct here. Conflict may arise when this area feels threatened.",
    "danger": "Mars demands transformation and correction here. Weaknesses left unresolved may produce setbacks in this area.",
}

HOUSE_LIFE_AREAS: Dict[int, str] = {
    1: "self, vitality, identity, and personal direction",
    2: "wealth, speech, family, and values",
    3: "courage, communication, skills, siblings, and short journeys",
    4: "home, emotional foundations, property, and inner security",
    5: "creativity, education, children, romance, and judgment",
    6: "work, service, health, discipline, obstacles, and debts",
    7: "marriage, partnerships, agreements, and public dealings",
    8: "transformation, shared resources, vulnerability, and sudden change",
    9: "beliefs, higher learning, teachers, long journeys, and fortune",
    10: "profession, authority, reputation, and public responsibilities",
    11: "gains, networks, friendships, aspirations, and community",
    12: "expenses, sleep, isolation, foreign places, and release",
}

RASHI_STRUCTURED_GUIDANCE: Dict[str, Dict[str, Dict[str, str]]] = {
    "Virgo": {
        "attention": {
            "strength": "many skills and significant potential",
            "weakness": "undisciplined criticism, correction, or attention to detail",
            "correction": "apply discipline and correct weak areas",
            "risk_pattern": "too much focus on flaws can consume useful energy",
            "development": "consistent, balanced attention to detail",
            "manifestation_template": "Mars concentrates energy in {life_area}. Your Virgo pattern gives you {strength}, but {weakness} can make this sensitive area consume too much of your effort. {correction}; balance this attention so it supports rather than overwhelms {life_area}.",
        },
        "protect": {
            "strength": "skill, usefulness, and careful attention to detail",
            "weakness": "a defensive urge to correct flaws or control details",
            "correction": "protect this area without turning correction into conflict",
            "risk_pattern": "feeling that imperfections threaten the area",
            "development": "measured protection and constructive communication",
            "manifestation_template": "Mars makes you instinctively protective of {life_area}. Your Virgo pattern values {strength}, but {weakness} may become defensive when {risk_pattern}. {correction}; develop {development}.",
        },
        "danger": {
            "strength": "many skills and significant potential",
            "weakness": "lack of discipline and other unresolved weaknesses",
            "correction": "correct weak areas and understand the details of what you are doing",
            "risk_pattern": "repeatedly ignoring these weaknesses",
            "development": "discipline and consistent work",
            "manifestation_template": "Mars highlights {life_area} for transformation and correction. You have {strength} and can become highly capable and valuable in this area, but {weakness} can prevent you from using that potential fully. Details matter here: {correction}. If you repeatedly ignore these weaknesses, this area may face setbacks. Develop {development} to unlock your potential.",
        },
    },
}


def _house_for_sign(chart: Any, sign: str) -> int:
    """Find a highlighted Rashi's house in the already-calculated D1 chart."""
    for house in chart.houses or []:
        if house.sign == sign:
            return house.number

    # Keep the lookup usable with lightweight chart fixtures lacking house rows.
    ascendant = chart.ascendant.sign if chart.ascendant else None
    if ascendant in RASHI_NAMES:
        return ((RASHI_NAMES.index(sign) - RASHI_NAMES.index(ascendant)) % 12) + 1
    raise ValueError(f"Unable to locate {sign} in the D1 chart")


def _reading_area(sign: str, layer: str, house_number: int) -> Dict[str, Any]:
    guidance = RASHI_GUIDANCE[sign]
    life_area = HOUSE_LIFE_AREAS[house_number]
    structured = RASHI_STRUCTURED_GUIDANCE.get(sign, {}).get(layer)
    if structured:
        description = structured["manifestation_template"].format(
            life_area=life_area,
            strength=structured["strength"],
            weakness=structured["weakness"],
            correction=structured["correction"],
            risk_pattern=structured["risk_pattern"],
            development=structured["development"],
        )
    else:
        description = f"{AREA_TYPE_PRINCIPLES[layer]} {guidance[layer]}"

    return {
        "area": f"House {house_number}: {life_area} — {guidance['area']}",
        "rashi": sign,
        "house": house_number,
        "life_area": life_area,
        "severity": "Requires Care" if layer == "danger" else "Deserves Attention",
        "severity_level": "high" if layer == "danger" else "moderate",
        "hook": "",
        "description": description,
        "potential_impact": "",
        "mindful_of": [],
        "takeaway": "",
    }


def compute_interpretation(payload: BirthData) -> Dict[str, Any]:
    """Return attention, boundary, danger, and transit guidance for a chart."""
    chart = generate_chart(payload)

    mars = next((planet for planet in (chart.planets or []) if planet.name == "Mars"), None)
    if mars is None:
        return {
            "status": "error",
            "message": "Unable to complete your reading. Please try again.",
        }

    mars_index = RASHI_NAMES.index(mars.sign)
    mars_sign = mars.sign
    fourth_aspect_sign = RASHI_NAMES[(mars_index + 3) % 12]
    eighth_aspect_sign = RASHI_NAMES[(mars_index + 7) % 12]
    attention_house = _house_for_sign(chart, mars_sign)
    protect_house = _house_for_sign(chart, fourth_aspect_sign)
    danger_house = _house_for_sign(chart, eighth_aspect_sign)

    chart_data = {
        "ascendant_sign": chart.ascendant.sign if chart.ascendant else None,
        "planets": [
            {
                "name": planet.name,
                "sign": planet.sign,
                "house": planet.house,
                "degree": round(planet.degree, 2),
            }
            for planet in (chart.planets or [])
        ],
        "extra_planets": [
            {
                "name": planet.name,
                "sign": planet.sign,
                "house": planet.house,
                "degree": round(planet.degree, 2),
            }
            for planet in (chart.extra_planets or [])
        ],
        "houses": [
            {"number": house.number, "sign": house.sign}
            for house in (chart.houses or [])
        ],
    }

    return {
        "status": "success",
        "attention": _reading_area(mars.sign, "attention", attention_house),
        "protect": _reading_area(fourth_aspect_sign, "protect", protect_house),
        "danger": _reading_area(eighth_aspect_sign, "danger", danger_house),
        "timing": calculate_caution_windows(
            [mars_sign, fourth_aspect_sign, eighth_aspect_sign],
            RASHI_GUIDANCE,
        ),
        "chart": chart_data,
    }
