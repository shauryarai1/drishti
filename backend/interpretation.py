"""DRISHTI's user-facing interpretation copy and Mars Rule mapping."""

from __future__ import annotations

from typing import Any, Dict

from calculator import generate_chart
from models import BirthData


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
        "danger": "Be especially careful with arguments, criticism, and disputes. Constantly correcting people or pointing out every small mistake can create serious conflict and enemies. Ignoring the boundaries highlighted above can make this area harder to handle.",
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


def _reading_area(sign: str, layer: str) -> Dict[str, Any]:
    guidance = RASHI_GUIDANCE[sign]
    return {
        "area": guidance["area"],
        "severity": "Requires Care" if layer == "danger" else "Deserves Attention",
        "severity_level": "high" if layer == "danger" else "moderate",
        "hook": "",
        "description": guidance[layer],
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
    fourth_aspect_sign = RASHI_NAMES[(mars_index + 3) % 12]
    eighth_aspect_sign = RASHI_NAMES[(mars_index + 7) % 12]

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
        "attention": _reading_area(mars.sign, "attention"),
        "protect": _reading_area(fourth_aspect_sign, "protect"),
        "danger": _reading_area(eighth_aspect_sign, "danger"),
        "transit": {
            "heading": "WHEN SHOULD YOU BE EXTRA CAREFUL?",
            "description": "When Saturn, Rahu, or Ketu moves through one of the highlighted Rashis, treat that period as a reminder to be more careful. Slow down, avoid unnecessary risks, and pay closer attention to the areas mentioned in your reading.",
        },
        "chart": chart_data,
    }
