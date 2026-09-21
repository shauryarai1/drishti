"""Curated Life Summary interpretations: category x selected Panchang lord.

Each entry is written for THAT planet in THAT category. There is no generic
composition, no house placement, no self-respect and no Graha-in-Bhava. The Panchang
lord's natural nature IS the interpretation.

PROVENANCE: source_type = "standard_jyotish" (common planetary significations,
paraphrased into original wording; no source prose copied).
"""

from __future__ import annotations

from typing import Any, Dict


def E(summary: str, strengths, watch_for, guidance: str) -> Dict[str, Any]:
    return {
        "summary": summary,
        "strengths": list(strengths),
        "watch_for": list(watch_for),
        "guidance": guidance,
    }


LIFE_SUMMARY_INTERPRETATIONS: Dict[str, Dict[str, Dict[str, Any]]] = {
    # ------------------------------------------------------------------ #
    # VAAR LORD -> PERSONALITY
    # ------------------------------------------------------------------ #
    "personality": {
        "Sun": E(
            "You tend to be independent, confident and authoritative, with a strong sense of identity and a natural pull toward responsibility.",
            ["leadership", "responsibility", "strong sense of identity"],
            ["excessive pride", "rigidity or a need for control"],
            "You do best when your confidence stays open to other people's views.",
        ),
        "Moon": E(
            "You tend to be sensitive, receptive and caring, with a lively imagination and a quick response to the mood around you.",
            ["emotional awareness", "adaptability", "care for others"],
            ["changing moods", "being strongly affected by your surroundings"],
            "Emotional security and familiar comfort matter a great deal to how you function.",
        ),
        "Mars": E(
            "You tend to be energetic, courageous and direct, ready to act and comfortable confronting a challenge.",
            ["courage", "initiative", "independence"],
            ["impatience", "impulsiveness", "unnecessary confrontation"],
            "Your energy works best when it is aimed rather than scattered.",
        ),
        "Mercury": E(
            "You tend to be curious, intelligent and communicative, with an analytical mind that enjoys information and learning.",
            ["quick thinking", "communication", "adaptability"],
            ["overthinking", "nervous mental activity", "inconsistency"],
            "Give your mind a clear direction and it becomes a real strength.",
        ),
        "Jupiter": E(
            "You tend to be understanding, principled and optimistic, drawn to knowledge, meaning and wisdom.",
            ["good judgment", "generosity", "interest in growth"],
            ["overconfidence in your own understanding", "becoming too certain of your judgment"],
            "Wisdom keeps growing when you stay willing to learn from people who disagree.",
        ),
        "Venus": E(
            "You tend to be harmonious, affectionate and sociable, with a refined eye and a genuine appreciation of beauty, balance and comfort.",
            ["warmth", "diplomacy", "creativity"],
            ["seeking comfort too much", "avoiding necessary conflict"],
            "Peace chosen honestly lasts longer than peace kept at any cost.",
        ),
        "Saturn": E(
            "You tend to be serious, responsible and disciplined, patient with long efforts and conscious of duty.",
            ["persistence", "reliability", "self-control"],
            ["pessimism", "rigidity", "worry", "carrying too much responsibility"],
            "You can be dependable without carrying everything alone.",
        ),
        "Rahu": E(
            "You tend to be ambitious and unconventional, drawn to what is unfamiliar and unwilling to accept a limit too early.",
            ["drive", "originality", "willingness to explore"],
            ["restlessness", "rarely feeling satisfied for long"],
            "Aim the ambition at something you genuinely chose.",
        ),
        "Ketu": E(
            "You tend to be reflective and inwardly detached, at ease in your own company and less concerned with appearances.",
            ["insight", "independence from opinion", "calm"],
            ["withdrawal", "losing interest once something is understood"],
            "Let people see more of what you keep private.",
        ),
    },
    # ------------------------------------------------------------------ #
    # TITHI LORD -> RELATIONSHIP NATURE
    # ------------------------------------------------------------------ #
    "relationships": {
        "Sun": E(
            "In relationships you need respect, recognition and to feel valued, and you are loyal and protective toward the people close to you.",
            ["loyalty", "protection", "steadiness"],
            ["pride", "needing to be right", "balancing independence with mutual respect"],
            "Partnership works for you when both people are treated as equals.",
        ),
        "Moon": E(
            "In relationships you need emotional connection, care and understanding, and you are naturally responsive to your partner's feelings.",
            ["care", "emotional attentiveness", "responsiveness"],
            ["moods affecting how you relate", "needing reassurance"],
            "Saying what you feel plainly helps more than expecting to be sensed.",
        ),
        "Mars": E(
            "In relationships you are passionate, direct and active, and you protect the people you care about.",
            ["passion", "protection", "initiative"],
            ["impatience", "competitiveness", "conflict"],
            "Bring patience as deliberately as you bring passion.",
        ),
        "Mercury": E(
            "In relationships you need communication and mental connection, and you like discussing and understanding what is happening between you.",
            ["conversation", "adaptability", "understanding"],
            ["overthinking feelings", "turning emotional situations into debates"],
            "Sometimes listening matters more than explaining.",
        ),
        "Jupiter": E(
            "In relationships you look for understanding, trust, principles and growth, and you are supportive and generous.",
            ["generosity", "support", "shared values"],
            ["becoming preachy", "assuming your judgment is always right"],
            "Let your partner's view count as much as your own.",
        ),
        "Venus": E(
            "In relationships you are naturally affectionate and companionship-oriented, valuing harmony, attraction, balance and shared enjoyment.",
            ["affection", "harmony", "companionship"],
            ["avoiding necessary confrontation", "keeping peace at your own expense"],
            "Honest warmth is what keeps closeness real.",
        ),
        "Saturn": E(
            "In relationships you take commitment seriously and value reliability, responsibility and stability.",
            ["commitment", "loyalty", "reliability"],
            ["taking a long time to open up", "emotional distance"],
            "Once you commit you are loyal; let people see that earlier.",
        ),
        "Rahu": E(
            "In relationships strong desires and expectations can influence you, and you may be drawn to intense or unconventional connections.",
            ["intensity", "openness to the unusual"],
            ["obsession", "dissatisfaction", "always wanting something different"],
            "Choose the person, not only the intensity.",
        ),
        "Ketu": E(
            "In relationships you value sincerity and space, and you are not easily impressed by display.",
            ["sincerity", "acceptance", "space"],
            ["withdrawing", "keeping feelings private"],
            "Staying present matters more than staying safe.",
        ),
    },
    # ------------------------------------------------------------------ #
    # KARANA LORD -> PROFESSIONAL NATURE
    # ------------------------------------------------------------------ #
    "professional": {
        "Sun": E(
            "Professionally you are confident, independent and responsibility-oriented, comfortable leading, directing and making decisions.",
            ["leadership", "decision-making", "responsibility"],
            ["ego-driven professional decisions"],
            "Let the quality of the work be the reason you are respected.",
        ),
        "Moon": E(
            "Professionally you are adaptive and responsive, reading people and changing situations well and often relying on intuition.",
            ["people sense", "adaptability", "intuition"],
            ["needing emotional steadiness for consistent decisions"],
            "Check how you feel before letting it make the decision.",
        ),
        "Mars": E(
            "Professionally you are action-oriented, competitive, courageous and decisive, and you like progress, challenge and execution.",
            ["initiative", "execution", "courage"],
            ["impatience", "acting before enough consideration"],
            "Decide quickly, but check the ground you are standing on.",
        ),
        "Mercury": E(
            "Professionally you are analytical, communicative and information-driven, good at calculation, learning, negotiation and adapting to new information.",
            ["analysis", "negotiation", "learning"],
            ["overanalysing decisions"],
            "Set a decision time and keep it.",
        ),
        "Jupiter": E(
            "Professionally you use knowledge, principles, understanding and long-term judgment, and you are naturally suited to advising, teaching and seeing the wider picture.",
            ["judgment", "guidance", "long-term view"],
            ["assuming your judgment is automatically right"],
            "Your authority grows when you stay willing to be corrected.",
        ),
        "Venus": E(
            "Professionally you are diplomatic and cooperative, valuing balance, good relationships, presentation and negotiation.",
            ["diplomacy", "cooperation", "presentation"],
            ["avoiding uncomfortable decisions"],
            "Diplomacy works best when it still reaches a decision.",
        ),
        "Saturn": E(
            "Professionally you are disciplined, structured, responsible and persistent, preferring careful planning and long-term progress.",
            ["discipline", "reliability", "planning"],
            ["excessive caution", "being slow to act"],
            "Momentum is part of discipline too.",
        ),
        "Rahu": E(
            "Professionally you are ambitious and unconventional, willing to explore unusual opportunities and think beyond traditional paths.",
            ["ambition", "originality", "risk-taking"],
            ["shortcuts", "obsession", "restless professional decisions"],
            "Check the foundations of anything that looks fast.",
        ),
        "Ketu": E(
            "Professionally you are independent and inwardly analytical, less dependent on conventional approval and able to investigate deeply.",
            ["depth of analysis", "independence", "focus"],
            ["detachment from ordinary professional ambitions", "losing interest after understanding something"],
            "Choose work for the meaning it gives you, not only the position.",
        ),
    },
    # ------------------------------------------------------------------ #
    # NAKSHATRA LORD -> DEEP INNER NATURE
    # ------------------------------------------------------------------ #
    "subconscious": {
        "Sun": E(
            "At the back of your mind there is a running question about who you are and whether you are living up to your own standards, and you notice when you are not taken seriously even if you say nothing.",
            ["inner purpose", "self-respect", "self-direction"],
            ["measuring yourself against recognition"],
            "Your direction matters more than your visibility.",
        ),
        "Moon": E(
            "Your subconscious mind is tied to feelings, memory and emotional security, and it records how an experience felt as much as what happened.",
            ["emotional memory", "instinct", "belonging"],
            ["holding on to old feelings"],
            "Feeling safe inside is what lets the rest settle.",
        ),
        "Mars": E(
            "Your subconscious mind switches into action and defence quickly, often before you have consciously decided anything.",
            ["inner courage", "decisiveness", "self-defence"],
            ["reacting before reflecting"],
            "A short pause before action changes the outcome.",
        ),
        "Mercury": E(
            "Your subconscious mind keeps working on things after they are over, replaying conversations and searching for what you missed.",
            ["curiosity", "mental processing", "adaptability"],
            ["overthinking"],
            "Not every question needs to be answered tonight.",
        ),
        "Jupiter": E(
            "Your subconscious mind is always asking what something means and is rarely satisfied with the surface explanation.",
            ["inner guidance", "principle", "search for meaning"],
            ["assuming understanding is complete"],
            "Keep the search open; that is where your depth lives.",
        ),
        "Venus": E(
            "Your subconscious mind is tuned to closeness and atmosphere, registering the emotional temperature of a room before anything is said.",
            ["affection", "aesthetic sense", "love of harmony"],
            ["disliking disharmony so much that you avoid it"],
            "Closeness survives honest discomfort better than silence.",
        ),
        "Saturn": E(
            "Your subconscious mind is constantly checking consequences, and it has usually considered what could go wrong before you act.",
            ["responsibility", "patience", "endurance"],
            ["worry", "instinctive self-restraint"],
            "Not every consequence needs to be carried in advance.",
        ),
        "Rahu": E(
            "Your subconscious mind is drawn to what is missing or still out of reach and rarely settles on what is already here.",
            ["curiosity", "ambition", "appetite for experience"],
            ["fixation", "never feeling complete"],
            "Notice when wanting has quietly become the point.",
        ),
        "Ketu": E(
            "Your subconscious mind steps back and observes rather than participating, and it loses interest in anything that feels already understood.",
            ["introspection", "detachment", "inner observation"],
            ["withdrawing from what matters"],
            "What you step back from, you often understand best.",
        ),
    },
    # ------------------------------------------------------------------ #
    # YOGA LORD -> PROBLEM-SOLVING NATURE + PROTECTIVE SUPPORT
    # ------------------------------------------------------------------ #
    "problems": {
        "Sun": E(
            "When problems come you meet them through confidence, leadership, self-respect, responsibility and clarity of purpose. Within this tradition, protective support is associated with courage, integrity and a strong sense of direction.",
            ["courage", "clarity", "responsibility"],
            ["pride getting in the way of help"],
            "Let purpose, not pride, set the response.",
        ),
        "Moon": E(
            "When problems come you work through them with adaptability, emotional intelligence, receptivity and awareness of changing circumstances. Within this tradition, support is associated with emotional connection, care and the ability to adjust.",
            ["adaptability", "emotional intelligence", "receptivity"],
            ["moods making the problem feel larger"],
            "Adjusting to the situation is a strength, not a surrender.",
        ),
        "Mars": E(
            "When problems come you act: courage, initiative, confrontation and decisiveness are how you overcome obstacles. Within this tradition, protective support is associated with direct, determined action.",
            ["courage", "initiative", "decisiveness"],
            ["turning every problem into a battle"],
            "Fight the problem, not the people around it.",
        ),
        "Mercury": E(
            "When problems come you work through intelligence, analysis, communication, learning and finding alternatives. Within this tradition, support appears through information, reasoning and flexibility.",
            ["analysis", "communication", "flexibility"],
            ["analysing instead of deciding"],
            "Gather what you need, then choose.",
        ),
        "Jupiter": E(
            "When problems come you rely on wisdom, understanding, principles, knowledge and good judgment, and guidance, teachers and learning become important forms of support. Within this tradition, protective support is associated with perspective and the wider view.",
            ["judgment", "perspective", "learning"],
            ["over-certainty about the right answer"],
            "Seek counsel as readily as you give it.",
        ),
        "Venus": E(
            "When problems come you work through harmony, diplomacy, relationships, cooperation and restoring balance. Within this tradition, protective support is associated with good relationships, negotiation and avoiding unnecessary conflict.",
            ["diplomacy", "cooperation", "restoring balance"],
            ["keeping peace by avoiding the issue"],
            "Cooperation solves more than confrontation when it is honest.",
        ),
        "Saturn": E(
            "When problems come you work through patience, discipline, responsibility, endurance and persistence. Within this tradition, protection is associated with consistency and surviving difficulty rather than expecting an immediate solution.",
            ["endurance", "discipline", "steadiness"],
            ["expecting immediate relief"],
            "Steady effort is how this kind of difficulty is outlasted.",
        ),
        "Rahu": E(
            "When problems come you use unconventional thinking, ambition and a willingness to enter unfamiliar territory, which can reveal unusual solutions. Within this tradition, support is associated with adaptability and fearlessness about the unknown.",
            ["unconventional thinking", "ambition", "adaptability"],
            ["excessive risk", "obsession"],
            "Take the unusual route with your eyes open.",
        ),
        "Ketu": E(
            "When problems come you step back, simplify and see beyond unnecessary attachments, which often reveals what actually matters. Within this tradition, protective support is associated with detachment and clarity.",
            ["detachment", "simplicity", "insight"],
            ["withdrawing instead of addressing the problem"],
            "Stepping back is useful only if you then step back in.",
        ),
    },
}
