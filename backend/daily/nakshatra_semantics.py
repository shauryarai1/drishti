"""Generic language renderer over the APPROVED Nakshatra profiles.

NO second Nakshatra database lives here. Everything is read at runtime from
`nakshatra_knowledge.profiles` (the single source of truth). This module only
holds generic language data: how a concept word is phrased, and which generic
house "need" a concept satisfies. It never assigns astrology meaning.

Roles map to existing approved profile fields:
    gift -> constructive,  focus -> focus,  action -> mode,  caution -> caution
"""

from __future__ import annotations

from typing import Iterable, Sequence

from nakshatra_knowledge.profiles import profile_for

ROLE_FIELD = {"gift": "constructive", "focus": "focus", "action": "mode", "caution": "caution"}

# Generic noun-phrase rendering for approved concept words. Not astrology -
# only grammar. Unknown concepts fall back to the token itself.
RENDER = {
    "observation": "careful observation", "learning": "careful learning",
    "communication": "clear communication", "responsible execution": "responsible follow-through",
    "information": "useful information", "conversation": "an honest conversation",
    "understanding before acting": "a clear understanding before you act",
    "endurance": "steady endurance", "restraint": "restraint", "responsibility": "responsibility",
    "handling demanding work": "handling demanding work", "responsibilities": "your responsibilities",
    "sustained effort": "sustained effort", "handling demanding matters": "handling demanding matters",
    "helping": "practical help", "learning deeply": "deep learning", "sustaining": "steady support",
    "strengthening": "strengthening", "support": "steady support",
    "strengthening foundations": "strengthening the foundations",
    "practical action": "practical action", "concentration": "steady concentration",
    "adaptability": "adaptability", "turning ideas into results": "turning ideas into results",
    "hands-on work": "hands-on work", "implementation": "careful implementation",
    "practical completion": "practical completion", "freedom": "freedom", "flexibility": "flexibility",
    "learning through experience": "learning through experience",
    "flexible independent action": "flexible, independent action",
    "skill-building": "building your skills", "persistence": "persistence",
    "meeting challenges": "meeting challenges", "purposeful effort": "purposeful effort",
    "goals": "your goals", "skill development": "developing your skills",
    "concentrated effort": "concentrated effort", "problem-solving": "problem-solving",
    "disciplined investigation": "disciplined investigation",
    "focused corrective work": "focused, corrective work", "analysis": "careful analysis",
    "correction": "correction", "focused independent work": "focused, independent work",
    "care": "genuine care", "peaceful completion": "a calm, complete finish",
    "restoration": "restoring your energy", "completion": "completion", "transition": "transition",
    "bringing matters to a peaceful close": "bringing matters to a peaceful close",
    "quick response": "a quick response", "beginning": "a fresh start",
    "restoring momentum": "a way to get things moving again", "decisiveness": "clear decisions",
    "initiative": "taking the initiative", "removing what is unnecessary": "cutting out what is unnecessary",
    "creativity": "creativity", "expression": "open expression", "development": "steady development",
    "making ideas tangible": "turning ideas into something real", "investigation": "careful investigation",
    "exploring alternatives": "exploring the options", "movement": "movement", "research": "deeper research",
    "truth-seeking": "getting to the truth",
    "identifying and removing a root problem": "finding and fixing the real problem",
}

# Generic "need" tags for approved concept words, used to match a house's needs.
TAGS = {
    "observation": {"observe", "understanding"}, "learning": {"learning"},
    "communication": {"communication"}, "responsible execution": {"execution", "responsibility"},
    "information": {"information"}, "conversation": {"communication"},
    "understanding before acting": {"understanding", "decision"},
    "endurance": {"effort", "persistence"}, "restraint": {"restraint", "patience"},
    "responsibility": {"responsibility"}, "handling demanding work": {"execution", "effort"},
    "responsibilities": {"responsibility"}, "sustained effort": {"effort"},
    "handling demanding matters": {"execution", "effort"}, "helping": {"support"},
    "learning deeply": {"learning"}, "sustaining": {"support"}, "strengthening": {"growth", "support"},
    "strengthening foundations": {"foundation", "growth"}, "practical action": {"action", "execution"},
    "concentration": {"focus"}, "adaptability": {"flexibility"},
    "turning ideas into results": {"execution", "growth"}, "hands-on work": {"execution", "tasks"},
    "implementation": {"execution"}, "practical completion": {"completion", "execution"},
    "freedom": {"freedom"}, "flexibility": {"flexibility"},
    "learning through experience": {"learning"}, "flexible independent action": {"action", "flexibility"},
    "skill-building": {"skill", "learning"}, "persistence": {"effort", "persistence"},
    "meeting challenges": {"effort"}, "purposeful effort": {"effort", "purpose"},
    "goals": {"goal"}, "skill development": {"skill", "learning"}, "concentrated effort": {"effort", "focus"},
    "problem-solving": {"investigation", "correction"}, "disciplined investigation": {"investigation"},
    "focused corrective work": {"correction", "execution"}, "analysis": {"investigation"},
    "correction": {"correction"}, "focused independent work": {"focus", "execution"},
    "support": {"support"}, "care": {"support", "care"}, "peaceful completion": {"completion", "release"},
    "restoration": {"restore"}, "completion": {"completion"}, "transition": {"release", "transition"},
    "bringing matters to a peaceful close": {"completion", "release"},
}

_FALLBACK = {"gift": "steady, careful effort", "focus": "the day's practical matters",
             "action": "moving with the day's rhythm", "caution": "moving without enough thought"}

# Generic CONCEPT -> behaviour clause (imperative). This is language/behaviour,
# not astrology: it says how a concept acts, never which Nakshatra it belongs to.
CONCEPT_BEHAVIOUR = {
    "observation": "watch what is really going on", "learning": "learn what it has to teach",
    "communication": "talk it through openly", "responsible execution": "see it through carefully",
    "information": "gather the facts first", "conversation": "talk it through openly",
    "understanding before acting": "understand it before you act",
    "endurance": "meet it with patience", "restraint": "hold back where it helps",
    "responsibility": "take it seriously", "handling demanding work": "work through what is demanding",
    "responsibilities": "take it seriously", "sustained effort": "keep at it steadily",
    "handling demanding matters": "work through what is demanding", "helping": "offer practical help",
    "learning deeply": "study it properly", "sustaining": "keep it steady",
    "strengthening": "build it up", "strengthening foundations": "strengthen the foundations",
    "support": "give it steady support", "practical action": "act on it practically",
    "concentration": "focus on it closely", "adaptability": "stay flexible about it",
    "turning ideas into results": "turn the idea into something real", "hands-on work": "get hands-on with it",
    "implementation": "put it into practice", "practical completion": "finish it properly",
    "freedom": "keep it open and unforced", "flexibility": "stay flexible about it",
    "learning through experience": "learn as you go",
    "flexible independent action": "act independently and flexibly", "skill-building": "build the skill",
    "persistence": "keep at it steadily", "meeting challenges": "face it directly",
    "purposeful effort": "work at it with purpose", "goals": "keep the goal in view",
    "skill development": "develop the skill", "concentrated effort": "give it your focus",
    "problem-solving": "work the problem", "disciplined investigation": "investigate it carefully",
    "focused corrective work": "correct it carefully", "analysis": "look into it closely",
    "correction": "put it right", "focused independent work": "work on it steadily",
    "care": "handle it with care", "peaceful completion": "bring it to a calm finish",
    "restoration": "restore what has slipped", "completion": "bring it to a close",
    "transition": "ease the transition",
    "bringing matters to a peaceful close": "bring it to a calm finish",
    "quick response": "respond quickly", "beginning": "make a fresh start",
    "restoring momentum": "get things moving again", "decisiveness": "decide clearly",
    "initiative": "take the initiative", "removing what is unnecessary": "clear out what is not needed",
    "creativity": "bring some creativity to it", "expression": "express it openly",
    "development": "develop it steadily", "making ideas tangible": "make the idea real",
    "investigation": "look into it more closely", "exploring alternatives": "weigh the options",
    "movement": "keep it moving", "research": "research it properly",
    "truth-seeking": "get to the truth of it",
    "identifying and removing a root problem": "find and fix the real problem",
    "partnership": "build it together", "teamwork": "work on it together",
    "repairing cooperation": "repair the cooperation", "second chances": "give it another go",
    "restoring what works": "restore what works", "recovering direction": "find your direction again",
    "rebuilding": "rebuild it", "confronting difficult work": "face the difficult work",
}

FALLBACK_BEHAVIOUR = "handle it thoughtfully"


def _join(items: Sequence[str]) -> str:
    out = []
    for item in items:
        words = str(item).split()
        # Generic dedup: drop a repeated leading modifier (e.g. "careful" twice).
        if out and words and words[0].lower() == out[-1].split()[0].lower():
            words = words[1:]
        out.append(" ".join(words) if words else str(item))
    out = [value for value in out if value]
    if not out:
        return ""
    if len(out) == 1:
        return out[0]
    return ", ".join(out[:-1]) + " and " + out[-1]


def _same_shape(first: str, second: str) -> bool:
    """Generic phrase-shape check so a noun and a gerund are not coordinated."""
    return first.split()[0].lower().endswith("ing") == second.split()[0].lower().endswith("ing")


def _tags(concept: str) -> set:
    return TAGS.get(concept, {w.lower() for w in concept.split()})


def select_concepts(concepts: Iterable[str], needs: set, limit: int = 2) -> list:
    """Choose the 1-2 approved concepts whose generic tags best fit the house."""
    ordered = list(concepts)
    ranked = sorted(range(len(ordered)), key=lambda i: (-len(_tags(ordered[i]) & needs), i))
    picked = [ordered[i] for i in ranked if _tags(ordered[i]) & needs][:limit]
    if len(picked) < limit:
        for token in ordered:
            if token not in picked and len(picked) < limit:
                picked.append(token)
    return picked[:limit]


def role_selection(nakshatra: str, role: str, needs: set):
    """(profile field, selected concepts, rendered phrase) from the approved profile."""
    field = ROLE_FIELD[role]
    try:
        profile = profile_for(nakshatra)
    except ValueError:
        return field, [], _FALLBACK[role]
    if role == "caution":
        token = (profile.get("caution") or (_FALLBACK["caution"],))[0]
        return field, [token], str(token)
    picked = select_concepts(profile.get(field) or (), needs)
    rendered = [RENDER.get(token, token) for token in picked]
    # If two concepts would not coordinate grammatically, keep the strongest one.
    if len(rendered) == 2 and not _same_shape(rendered[0], rendered[1]):
        picked, rendered = picked[:1], rendered[:1]
    phrase = _join(rendered) or _FALLBACK[role]
    return field, picked, phrase


def role_phrase(nakshatra: str, role: str, needs: set) -> str:
    return role_selection(nakshatra, role, needs)[2]


# Generic BEHAVIOUR of a concept: how that concept operates inside any life
# area. Language only - it never says which Nakshatra a concept belongs to.
BEHAVIOUR = {
    "observation": "noticing what is really going on", "learning": "learning from what you hear",
    "communication": "clarifying things through conversation",
    "responsible execution": "following through responsibly", "information": "gathering the information you need",
    "conversation": "talking things through", "understanding before acting": "understanding before you act",
    "endurance": "staying patient and steady", "restraint": "holding back and staying measured",
    "responsibility": "carrying your responsibilities steadily", "handling demanding work": "working through demanding tasks",
    "responsibilities": "carrying your responsibilities steadily", "sustained effort": "keeping up steady effort",
    "handling demanding matters": "working through demanding matters", "helping": "offering practical help",
    "learning deeply": "studying things properly", "sustaining": "giving steady support",
    "strengthening": "strengthening what already works", "support": "offering steady support",
    "strengthening foundations": "strengthening the foundations", "practical action": "taking practical action",
    "concentration": "keeping your concentration", "adaptability": "adapting as things change",
    "turning ideas into results": "turning ideas into results", "hands-on work": "getting hands-on with the work",
    "implementation": "putting plans into practice", "practical completion": "finishing things properly",
    "freedom": "keeping your independence", "flexibility": "staying flexible",
    "learning through experience": "learning through experience",
    "flexible independent action": "acting independently and flexibly", "skill-building": "building your skills",
    "persistence": "persisting steadily", "meeting challenges": "meeting the challenge directly",
    "purposeful effort": "making purposeful effort", "goals": "keeping your goals in view",
    "skill development": "developing your skills", "concentrated effort": "concentrating your effort",
    "problem-solving": "solving the problem at hand", "disciplined investigation": "investigating carefully",
    "focused corrective work": "correcting what is off", "analysis": "analysing things carefully",
    "correction": "correcting what is off", "focused independent work": "working carefully on your own",
    "care": "showing genuine care", "peaceful completion": "bringing things to a close",
    "restoration": "restoring what has drifted", "completion": "bringing things to a close",
    "transition": "managing the transition", "bringing matters to a peaceful close": "bringing things to a close",
    "quick response": "acting without delay", "beginning": "making a fresh start",
    "restoring momentum": "getting things moving again", "decisiveness": "deciding clearly",
    "initiative": "taking the initiative", "removing what is unnecessary": "cutting to what matters",
    "creativity": "bringing a creative touch", "expression": "expressing what you feel",
    "development": "developing things steadily", "making ideas tangible": "turning ideas into something real",
    "investigation": "looking more carefully into things", "exploring alternatives": "exploring the options",
    "movement": "staying active", "research": "researching more deeply", "truth-seeking": "getting to the truth",
    "identifying and removing a root problem": "getting to the root of the problem",
    "administration": "organising responsibilities carefully",
    "second chances": "giving things another constructive try",
}
_FALLBACK_BEHAVIOUR = "handling it thoughtfully"

# Generic CONTEXT adjustment: an action concept expressed in a REFLECTIVE house
# is not "keep pushing". Language only - keyed by concept, never by Nakshatra.
REFLECTIVE_BEHAVIOUR = {
    "persistence": "staying patiently with your reflection",
    "quick response": "moving at an unhurried pace",
    "initiative": "taking your time with what needs doing",
    "decisiveness": "letting clarity come in its own time",
    "meeting challenges": "sitting with what feels difficult",
    "purposeful effort": "working gently and steadily",
    "focused independent work": "working quietly on your own",
    "concentrated effort": "giving it quiet attention",
}


def behaviour_selection(nakshatra: str, needs: set, context: str = "active"):
    """(profile field, selected concept, behaviour phrase) from the approved profile."""
    try:
        profile = profile_for(nakshatra)
    except ValueError:
        return "constructive", [], _FALLBACK_BEHAVIOUR
    picked = select_concepts(profile.get("constructive") or (), needs, limit=1)
    token = picked[0] if picked else ""
    if context == "reflective" and token in REFLECTIVE_BEHAVIOUR:
        phrase = REFLECTIVE_BEHAVIOUR[token]
    else:
        phrase = BEHAVIOUR.get(token, _FALLBACK_BEHAVIOUR)
    return "constructive", picked, phrase
