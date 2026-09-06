"""
DRISHTI — Interpretation layer.

Takes the raw chart from generate_chart(), extracts Mars's position,
computes the Mars Rule (4th and 8th aspects), and returns ONLY the
user-facing interpretation. No astrological terminology is exposed.

Three sections:
  1. Danger Area   — 4th aspect (where to be careful)
  2. Protect Area  — 8th aspect (what to safeguard)
  3. Sudden Changes — derived from the 8th aspect (unexpected developments)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from calculator import generate_chart
from models import BirthData, ChartResponse


# ---------------------------------------------------------------------------
# Aspect-to-area mapping — completely rewritten copy
# ---------------------------------------------------------------------------

SIGN_TO_AREA: Dict[str, Dict[str, Any]] = {
    "Aries": {
        "area": "Decision Making",
        "severity": "moderate",
        "hook": "There's one area of your life where you really can't afford to be careless.",
        "description": "Your decisions are where things can go sideways. You have a habit of acting fast — and sometimes that works brilliantly. But some of your biggest mistakes may come from choosing before you're ready.",
        "potential_impact": "A rushed decision could cost you an opportunity, damage a relationship, or create a problem that didn't need to exist. The pressure to act quickly is real. But so are the consequences.",
        "mindful_of": [
            "Making big choices when you're frustrated or emotional",
            "Saying \"yes\" or \"no\" before you've really thought it through",
            "Ignoring your gut feeling when something feels off",
            "Treating every situation like it needs an immediate response",
        ],
        "takeaway": "When the decision matters, give clarity time to arrive.",
        "sudden_hook": "And this is where things get interesting...",
        "sudden_description": "An unexpected shift in how you make decisions could change everything. Something may push you to rethink an approach you've been using for a long time.",
        "sudden_impact": "Be open to a change of direction here. What feels like disruption now could turn into a breakthrough — if you don't resist it.",
    },
    "Taurus": {
        "area": "Money & Finances",
        "severity": "moderate",
        "hook": "Your chart points to an area that deserves more attention than you probably give it.",
        "description": "Your relationship with money is more fragile than it looks. You may feel secure — until you don't. Watch where your money goes. Not every expense is what it seems.",
        "potential_impact": "A bad investment, an impulsive purchase, or a financial arrangement you didn't fully understand could create serious stress. Money problems don't announce themselves. They creep in.",
        "mindful_of": [
            "Spending money to feel better in the moment",
            "Trusting financial advice without verifying it yourself",
            "Lending money to people who may not return it",
            "Ignoring small financial leaks that add up over time",
        ],
        "takeaway": "Protect your resources. Not everything that glitters is worth your money.",
        "sudden_hook": "And this is where things get interesting...",
        "sudden_description": "Something unexpected could shift in your financial picture. An opportunity that appears suddenly — or a cost you didn't see coming.",
        "sudden_impact": "Stay alert here. Surprise developments around money can go either way. How you respond in the moment will determine the outcome.",
    },
    "Gemini": {
        "area": "Communication",
        "severity": "moderate",
        "hook": "This is the part of your chart I would NOT ignore.",
        "description": "Your words carry more weight than you think. Something you say — or fail to say — could create an unexpected problem. A casual comment might be taken the wrong way at the worst time.",
        "potential_impact": "A miscommunication could damage an important relationship or create conflict that was completely avoidable. The words you choose now matter more than usual.",
        "mindful_of": [
            "Speaking too quickly during disagreements",
            "Making promises you haven't fully thought through",
            "Sharing information that wasn't yours to share",
            "Assuming people understood what you meant",
        ],
        "takeaway": "Say less. Mean more. Choose your words with care.",
        "sudden_hook": "And this is where things get interesting...",
        "sudden_description": "A conversation or message could arrive unexpectedly — and change the direction of something important. What someone says to you (or what you say to them) may carry more weight than either of you realizes.",
        "sudden_impact": "Pay attention to what gets said — and what doesn't. A surprise development in communication could shift a relationship or an opportunity.",
    },
    "Cancer": {
        "area": "Home & Family",
        "severity": "moderate",
        "hook": "There's a reason this area stands out in your chart.",
        "description": "Something at home or within your family needs your attention. It may be a situation you've been avoiding. The longer you ignore it, the bigger it gets.",
        "potential_impact": "Family tensions, unresolved conflicts, or neglecting your home environment could quietly build into something harder to fix. Your emotional safety starts here — don't let it crack.",
        "mindful_of": [
            "Avoiding difficult conversations with family members",
            "Neglecting your home environment while chasing other goals",
            "Letting emotions build up without expressing them",
            "Assuming your family knows how you feel without saying it",
        ],
        "takeaway": "Your home is your foundation. Keep it strong.",
        "sudden_hook": "And this is where things get interesting...",
        "sudden_description": "An unexpected change at home or within your family could catch you off guard. Something that seemed stable may shift — or something you ignored may finally demand attention.",
        "sudden_impact": "If something moves fast here, don't assume it's random. There may be a pattern you haven't noticed yet.",
    },
    "Leo": {
        "area": "Ego & Recognition",
        "severity": "moderate",
        "hook": "This is the part I find interesting in your chart.",
        "description": "Watch your ego. You may find yourself in a situation where you need recognition, credit, or control — and it doesn't come. How you handle that moment says everything about you.",
        "potential_impact": "Pride can cost you the very thing you're chasing. A moment of ego could damage a relationship, burn a bridge, or close a door you needed open.",
        "mindful_of": [
            "Needing to be right in every conversation",
            "Taking credit that should be shared",
            "Making decisions to impress others rather than for the right reasons",
            "Letting pride prevent you from asking for help",
        ],
        "takeaway": "True strength is knowing when to step back.",
        "sudden_hook": "And this is where things get interesting...",
        "sudden_description": "Something may shift suddenly in how you're seen or recognized. An unexpected change in status, reputation, or how others respond to you.",
        "sudden_impact": "This could be a surprise opportunity — or a humbling moment. Either way, stay grounded. How you handle sudden attention or lack of it defines what comes next.",
    },
    "Virgo": {
        "area": "Health & Body",
        "severity": "moderate",
        "hook": "Your body is trying to tell you something. Don't ignore it.",
        "description": "Stress, fatigue, or small health issues you've been brushing aside could become a bigger problem. This isn't about panic — it's about paying attention before something forces you to.",
        "potential_impact": "Pushing through exhaustion or ignoring warning signs could lead to a health scare that forces you to slow down. Prevention is always cheaper than treatment.",
        "mindful_of": [
            "Skipping sleep to finish tasks",
            "Ignoring headaches, tension, or physical discomfort",
            "Overworking without proper breaks",
            "Treating your body like it can handle anything indefinitely",
        ],
        "takeaway": "Your body keeps the score. Listen to it before it forces you to.",
        "sudden_hook": "And this is where things get interesting...",
        "sudden_description": "A sudden change in energy, health, or physical well-being could appear. Something you've been ignoring may surface unexpectedly.",
        "sudden_impact": "If your body sends a signal, don't brush it aside. A surprise shift here could be a wake-up call — or an unexpected improvement.",
    },
    "Libra": {
        "area": "Relationships & Trust",
        "severity": "moderate",
        "hook": "This is an area where I'd suggest you stay alert.",
        "description": "Someone close to you may not be what they seem. Or maybe you've been too focused on keeping the peace to see what's really happening. Trust your instincts here.",
        "potential_impact": "A relationship that looks balanced on the surface may have hidden problems. A partnership, friendship, or agreement could shift in ways you didn't expect.",
        "mindful_of": [
            "Ignoring red flags because you want things to work out",
            "Sacrificing your own needs to keep others happy",
            "Trusting someone just because they're charming",
            "Avoiding conflict when something important needs to be said",
        ],
        "takeaway": "Not every smile hides good intentions. Pay attention.",
        "sudden_hook": "And this is where things get interesting...",
        "sudden_description": "Something unexpected could shift in a relationship. A truth may surface, a dynamic may change, or someone may show you who they really are.",
        "sudden_impact": "Don't resist what comes. If something changes suddenly here, it's clearing the way for something more honest.",
    },
    "Scorpio": {
        "area": "Change & Uncertainty",
        "severity": "moderate",
        "hook": "There's a reason this area stands out immediately in your chart.",
        "description": "Something in your life is about to shift — or it already has. You can't control what happens. But you can control how you respond. Resistance will make it worse.",
        "potential_impact": "Clinging to the familiar when change is necessary could hold you back from something better. But rushing into change without thinking could be equally dangerous.",
        "mindful_of": [
            "Refusing to let go of something that's no longer working",
            "Making impulsive changes out of fear or frustration",
            "Keeping secrets that could hurt you if revealed",
            "Using control as a shield against vulnerability",
        ],
        "takeaway": "Transformation isn't comfortable. But staying stuck is worse.",
        "sudden_hook": "And this is where things get interesting...",
        "sudden_description": "A sudden transformation or unexpected twist could change the direction of something you thought was settled. What feels like disruption now may be exactly what you need.",
        "sudden_impact": "Stay open to what comes. Surprise developments here can be powerful — if you let them.",
    },
    "Sagittarius": {
        "area": "Overconfidence & Blind Spots",
        "severity": "moderate",
        "hook": "Your chart reveals something you might be overlooking.",
        "description": "Your optimism is usually your strength. But right now, it could be your weakness. You might be overlooking something important because you're too sure everything will work out.",
        "potential_impact": "Overconfidence can make you miss warning signs. A plan you thought was solid might have a gap. A person you trust might not deserve it. Don't let your beliefs blind you to reality.",
        "mindful_of": [
            "Making plans based on best-case scenarios only",
            "Ignoring advice because you think you already know",
            "Trusting someone just because they seem honest",
            "Skipping details because you're eager to move forward",
        ],
        "takeaway": "Question everything — especially what you're most sure about.",
        "sudden_hook": "And this is where things get interesting...",
        "sudden_description": "Something that seemed certain may suddenly change. A plan, a belief, or an assumption could be challenged in ways you didn't expect.",
        "sudden_impact": "If something shifts suddenly here, don't dig in. Stay flexible. The surprise may be exactly the correction you needed.",
    },
    "Capricorn": {
        "area": "Work & Ambition",
        "severity": "moderate",
        "hook": "This is the part of your chart I'd keep my eyes on.",
        "description": "Your career or professional life needs careful attention right now. A decision you make at work — or one you avoid making — could have a bigger impact than you expect.",
        "potential_impact": "A conflict with authority, a missed opportunity, or a professional mistake could set you back. Don't let ambition make you blind to what's happening around you.",
        "mindful_of": [
            "Overcommitting yourself to prove your worth",
            "Ignoring office politics that could affect your position",
            "Sacrificing personal life for professional gain",
            "Trusting promises that haven't been put in writing",
        ],
        "takeaway": "Build your career with patience, not desperation.",
        "sudden_hook": "And this is where things get interesting...",
        "sudden_description": "An unexpected shift in your professional life could appear. A change in leadership, a surprise opportunity, or a sudden challenge at work.",
        "sudden_impact": "If something moves fast in your career, stay calm and strategic. What feels like disruption could be the push you needed.",
    },
    "Aquarius": {
        "area": "People & Loyalty",
        "severity": "moderate",
        "hook": "Watch the people around you. Not everyone who smiles at you is on your side.",
        "description": "Some relationships in your life may need a second look. A friend, colleague, or someone you rely on could disappoint you. Betrayal doesn't always come from enemies — sometimes it comes from people you trusted completely.",
        "potential_impact": "A friend, colleague, or someone you rely on could disappoint you. Betrayal doesn't always come from enemies — sometimes it comes from people you trusted completely.",
        "mindful_of": [
            "Sharing your plans with people who haven't earned your trust",
            "Ignoring signs that someone is using you",
            "Assuming loyalty just because of history",
            "Being too available for people who aren't there for you",
        ],
        "takeaway": "Choose your circle wisely. Not everyone deserves a seat at your table.",
        "sudden_hook": "And this is where things get interesting...",
        "sudden_description": "Someone's true colors may surface suddenly. A friendship, alliance, or connection could shift in ways you didn't expect.",
        "sudden_impact": "If a relationship changes fast, pay attention. What emerges may be surprising — but it's better to know than to guess.",
    },
    "Pisces": {
        "area": "Inner World & Clarity",
        "severity": "moderate",
        "hook": "Your mind may not be as clear as you think.",
        "description": "Confusion, mixed signals, or self-doubt could be affecting your decisions. Don't make important choices when your vision is clouded. Sometimes the best move is to wait.",
        "potential_impact": "Acting on unclear thoughts or emotions could lead to decisions you regret. When you can't think straight, the safest move is to wait — not to force an answer.",
        "mindful_of": [
            "Making decisions when you're emotionally overwhelmed",
            "Ignoring your intuition because logic says otherwise",
            "Escaping reality instead of facing difficult truths",
            "Trusting feelings that haven't been tested by facts",
        ],
        "takeaway": "Clarity comes to those who wait for it. Don't force what isn't ready.",
        "sudden_hook": "And this is where things get interesting...",
        "sudden_description": "A moment of unexpected clarity could arrive — or a situation could suddenly become confusing. Something that seemed straightforward may reveal hidden layers.",
        "sudden_impact": "If your perception shifts suddenly, don't panic. Sit with it. The confusion may be leading you somewhere important.",
    },
}


# Severity descriptions
SEVERITY_LABELS = {
    "low": "Worth Noting",
    "moderate": "Deserves Attention",
    "high": "Requires Care",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_interpretation(payload: BirthData) -> Dict[str, Any]:
    """
    Generate the user-facing interpretation from birth details.

    Internally:
      1. Generates the full chart
      2. Extracts Mars's sign position
      3. Computes the 4th and 8th aspects
      4. Maps aspects to life areas (danger + protect + sudden)
      5. Returns ONLY the user-facing interpretation

    Never exposes: planets, houses, signs, degrees, calculations,
    or any astrological terminology.
    """
    chart = generate_chart(payload)

    # Extract Mars
    mars = None
    for p in (chart.planets or []):
        if p.name == "Mars":
            mars = p
            break

    if mars is None:
        return {
            "status": "error",
            "message": "Unable to complete your reading. Please try again.",
        }

    mars_sign = mars.sign

    # Compute Mars Rule aspects (4th and 8th)
    RASHI_NAMES = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
    ]

    mars_index = RASHI_NAMES.index(mars_sign)
    fourth_aspect_sign = RASHI_NAMES[((mars_index) + 3) % 12]
    eighth_aspect_sign = RASHI_NAMES[((mars_index) + 7) % 12]

    # Map to areas
    primary = SIGN_TO_AREA.get(fourth_aspect_sign, SIGN_TO_AREA["Aries"])
    secondary = SIGN_TO_AREA.get(eighth_aspect_sign, SIGN_TO_AREA["Taurus"])

    # Build chart data for Kundli display
    chart_data = {
        "ascendant_sign": chart.ascendant.sign if chart.ascendant else None,
        "planets": [
            {
                "name": p.name,
                "sign": p.sign,
                "house": p.house,
                "degree": round(p.degree, 2),
            }
            for p in (chart.planets or [])
        ],
        "extra_planets": [
            {
                "name": p.name,
                "sign": p.sign,
                "house": p.house,
                "degree": round(p.degree, 2),
            }
            for p in (chart.extra_planets or [])
        ],
        "houses": [
            {"number": h.number, "sign": h.sign}
            for h in (chart.houses or [])
        ],
    }

    return {
        "status": "success",
        "primary": {
            "area": primary["area"],
            "severity": SEVERITY_LABELS.get(primary["severity"], "Deserves Attention"),
            "severity_level": primary["severity"],
            "hook": primary["hook"],
            "description": primary["description"],
            "potential_impact": primary["potential_impact"],
            "mindful_of": primary["mindful_of"],
            "takeaway": primary["takeaway"],
        },
        "secondary": {
            "area": secondary["area"],
            "severity": SEVERITY_LABELS.get(secondary["severity"], "Deserves Attention"),
            "severity_level": secondary["severity"],
            "hook": secondary["hook"],
            "description": secondary["description"],
            "potential_impact": secondary["potential_impact"],
            "mindful_of": secondary["mindful_of"],
            "takeaway": secondary["takeaway"],
        },
        "sudden": {
            "area": secondary["area"],
            "severity": "moderate",
            "severity_level": "moderate",
            "hook": secondary["sudden_hook"],
            "description": secondary["sudden_description"],
            "potential_impact": secondary["sudden_impact"],
            "mindful_of": [],
            "takeaway": "",
        },
        "chart": chart_data,
    }
