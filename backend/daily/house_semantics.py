"""House semantics for the Daily composer - NAKSHATRA-AGNOSTIC.

Each house supplies its OWN life-area, its generic NEEDS (concept relevance), a
generic CONTEXT (used to express a concept appropriately) and a small set of
generic sentence predicates. It never names a Nakshatra concept.

No house astrology meaning is changed.
"""

from __future__ import annotations

from typing import Dict

HOUSE_SEMANTICS: Dict[int, Dict[str, object]] = {
    1: {
        "needs": frozenset({"self", "decision", "response", "observe"}), "context": "personal",
        "area": "Your own mood and needs are the focus today",
        "predicates": ("matters more than reacting quickly.", "is worth a moment before you decide."),
        "love": "You are more aware of your own needs than your partner's; {focus} keeps that from becoming distance.",
        "health": "Your energy follows your own state, and {gift} helps you pace it.",
        "career": "Personal priorities compete with work; {focus} helps keep them in order.",
    },
    2: {
        "needs": frozenset({"resources", "family", "speech", "communication"}), "context": "practical",
        "area": "Money and family matters are in the foreground",
        "predicates": ("will serve a decision about resources.", "is worth applying before you commit."),
        "love": "Practical support counts as affection, and {gift} helps a family decision.",
        "health": "Food and routine deserve attention, and {gift} helps steady them.",
        "career": "Financial work moves well when {focus} guides it.",
    },
    3: {
        "needs": frozenset({"communication", "skill", "movement", "learning"}), "context": "communicative",
        "area": "Conversations, messages and short journeys shape the day",
        "predicates": ("keeps them useful.", "helps the day run smoothly."),
        "love": "Conversation keeps the connection moving; {gift} deepens it.",
        "health": "Restlessness settles when you channel it into {gift}.",
        "career": "Quick, practical work goes well through {focus}.",
    },
    4: {
        "needs": frozenset({"home", "understanding", "family", "communication"}), "context": "domestic",
        "area": "Home and family set the tone today",
        "predicates": ("will do more good here than rushing.", "is worth the extra patience today."),
        "love": "Warmth at home supports closeness, and {gift} deepens it.",
        "health": "Rest and comfort support recovery, and {gift} helps you rest well.",
        "career": "Work may feel secondary to domestic matters; {gift} keeps it moving.",
    },
    5: {
        "needs": frozenset({"learning", "creativity", "affection"}), "context": "creative",
        "area": "Creativity, enjoyment and the heart are highlighted",
        "predicates": ("may spark something worth following.", "opens the day up nicely."),
        "love": "Romance is supported, and {gift} warms it.",
        "health": "Enjoyment lifts your energy, and {gift} keeps it light.",
        "career": "Creative work helps while routine feels slow, so lean on {focus}.",
    },
    6: {
        "needs": frozenset({"tasks", "correction", "effort", "execution"}), "context": "active",
        "area": "Work and routine want attention",
        "predicates": ("helps clear what is pending.", "keeps the day moving."),
        "love": "Work pressure can crowd out a partner, and {gift} protects the connection.",
        "health": "Routine strain is worth watching, and {gift} helps you pace it.",
        "career": "Focused effort pays off, and {gift} clears a pending task.",
    },
    7: {
        "needs": frozenset({"communication", "agreement", "cooperation"}), "context": "relational",
        "area": "Partners, clients and agreements are central today",
        "predicates": ("keeps the exchange on solid ground.", "helps the terms land well."),
        "love": "One-to-one attention is highlighted, and {gift} strengthens it.",
        "health": "Wellbeing depends on balance with others, and {gift} helps.",
        "career": "Meetings and agreements are favoured through {focus}.",
    },
    8: {
        "needs": frozenset({"investigation", "uncertainty", "information"}), "context": "investigative",
        "area": "Hidden matters and unanswered questions may surface",
        "predicates": ("brings the missing information to light.", "reveals what has been unclear."),
        "love": "Unspoken matters need patience, and {gift} helps.",
        "health": "Uncertainty can be draining, and {gift} helps you steady it.",
        "career": "Research suits the day better than bold moves, so rely on {focus}.",
    },
    9: {
        "needs": frozenset({"learning", "guidance", "perspective"}), "context": "reflective",
        "area": "Learning, guidance and the bigger picture draw your attention",
        "predicates": ("can shift your perspective.", "opens a wider view."),
        "love": "Shared values matter more than daily details, and {focus} connects you.",
        "health": "Perspective supports emotional balance, and {focus} helps.",
        "career": "Planning and long-term direction are favoured through {focus}.",
    },
    10: {
        "needs": frozenset({"execution", "decision", "responsibility", "communication"}), "context": "active",
        "area": "Career matters and professional decisions take priority today",
        "predicates": ("is what carries you through them.", "matters more than speed right now."),
        "love": "Work focus leaves less room for personal attention, so {gift} prevents distance.",
        "health": "Steady effort is fine but overwork is not, and {gift} helps you stop in time.",
        "career": "Results are in focus, and {gift} influences progress.",
    },
    11: {
        "needs": frozenset({"connection", "opportunity", "cooperation", "communication"}), "context": "social",
        "area": "Friends, groups and networks are active today",
        "predicates": ("is what moves things forward through other people.", "opens doors through your circle."),
        "love": "Social life is busy and private time is shorter, so {gift} keeps closeness.",
        "health": "Shared activity lifts energy, and {focus} supports it.",
        "career": "Networks and opportunities are favoured through {focus}.",
    },
    12: {
        "needs": frozenset({"reflection", "release", "quiet", "rest"}), "context": "reflective",
        "area": "A quieter day suits rest and reflection",
        "predicates": ("serves you better than pushing.", "is the wiser pace for today."),
        "love": "You may need space rather than closeness, so {gift} keeps it kind.",
        "health": "Rest and sleep deserve priority, and {gift} helps you settle.",
        "career": "Behind-the-scenes work suits the day, and {focus} helps.",
    },
}
