"""Freshly composed Life Summary paragraphs, one per category x planet.

These are written around the meaning of the approved KAVACH data, not assembled
from connectors. They describe the person: behaviour first, strengths and costs
flowing into each other, advice only where it belongs. No planet names.

The structured facts remain in knowledge.py as the source material (and for the
developer audit); this module is the finished prose.
"""

from __future__ import annotations

from typing import Dict, Optional

PARAGRAPHS: Dict[str, Dict[str, str]] = {
    "personality": {
        "Sun": (
            "You carry yourself with a fair amount of natural confidence, and you are comfortable being the one "
            "who takes charge when nobody else does. Recognition matters to you more than you tend to admit, and "
            "you would rather be respected than merely liked. The pattern to watch is defending your position a "
            "little too firmly when someone offers a different view."
        ),
        "Moon": (
            "You pick up on the mood in a room almost immediately, and how you feel tends to shape how you act "
            "more than you would like to admit. You are caring and quick to adapt, and people often find it easy "
            "to talk to you. The difficulty is that your own mood can change with the weather around you, and "
            "decisions made in a low moment rarely hold."
        ),
        "Mars": (
            "You are direct, energetic and happiest when something is actually happening. Waiting frustrates you, "
            "and you would rather take a first step and adjust than plan endlessly. That drive gets a lot done, "
            "though it can also make you sharp with people who move more slowly."
        ),
        "Mercury": (
            "You think quickly and you like to understand how things work, so you ask questions and read widely. "
            "Conversation keeps you interested, and you are good at explaining your thinking to other people. The "
            "trap is overthinking: you can turn a decision that was already made into another round of analysis."
        ),
        "Jupiter": (
            "You are curious about why things are the way they are, and you rarely accept an explanation at face "
            "value. Learning something properly matters to you, and people often come to you for a wider view. "
            "That breadth is a real strength, though it can slide into assuming you already understand a "
            "situation before you have really looked at it."
        ),
        "Venus": (
            "You are warm, sociable and attentive to the atmosphere around you, and you care about how things "
            "look and feel, not just whether they work. People find you easy company, and you would rather keep "
            "things pleasant than win an argument. The cost is that you can avoid a necessary disagreement until "
            "it becomes a bigger problem."
        ),
        "Saturn": (
            "You take life seriously and you are more comfortable earning your progress than being handed it. "
            "People rely on you because you follow through, and you rarely make promises you cannot keep. The "
            "pattern that holds you back is treating caution as a virtue in every situation, especially when "
            "things are actually going well."
        ),
        "Rahu": (
            "You are ambitious and drawn to whatever lies outside the ordinary, and you get restless when life "
            "becomes too predictable. You are willing to try things that others avoid, which opens doors most "
            "people never see. The difficulty is satisfaction: you can reach something you wanted and immediately "
            "start looking past it."
        ),
        "Ketu": (
            "You are reflective and comfortable in your own company, and you do not need much external approval "
            "to feel settled. You notice things other people miss because you are not busy performing. The risk is "
            "drifting out of situations that actually matter to you simply because you can live without them."
        ),
    },
    "relationships": {
        "Sun": (
            "In close relationships you want to be respected as much as loved, and you are loyal to the people "
            "who have earned your trust. You show care by protecting and providing rather than by talking about "
            "feelings. The strain comes when pride gets involved and a small apology becomes difficult to make."
        ),
        "Moon": (
            "You need to feel emotionally close to someone, not just committed to them, and you notice changes in "
            "their mood before they mention anything. You are caring and attentive, and you want the same "
            "attention returned. When you feel unsure of the connection, your own mood can swing and the "
            "relationship feels it."
        ),
        "Mars": (
            "You bring passion and directness to relationships, and you are quick to defend the people you love. "
            "Problems get raised rather than avoided, which is often useful. It becomes harmful when the same "
            "energy turns a disagreement into a contest."
        ),
        "Mercury": (
            "You connect through conversation, and a relationship feels alive to you when there is something to "
            "discuss and understand together. You are adaptable and fair-minded, and you like knowing where you "
            "stand. The trouble is that you can analyse a feeling instead of simply having it, and your partner "
            "may end up debating what they wanted to be heard on."
        ),
        "Jupiter": (
            "You look for warmth, trust and something meaningful in a relationship, and you are generous with the "
            "people you care about. You want a partner you can grow with, and you support their plans as readily "
            "as your own. The habit to watch is offering guidance when what is actually wanted is just company."
        ),
        "Venus": (
            "You are warm and attentive in close relationships, and you care about the atmosphere between you and "
            "the other person. Affection, shared pleasures and a sense of ease matter to you, and you would rather "
            "resolve something gently than turn it into a fight. The pattern to watch is agreeing too quickly "
            "just to keep things pleasant."
        ),
        "Saturn": (
            "You take commitment seriously and you would rather build something lasting than something exciting. "
            "You show loyalty by being dependable, and once you are committed you stay. What people around you may "
            "find hard is how long it takes you to let them in, and how easily you retreat into reserve when you "
            "feel hurt."
        ),
        "Rahu": (
            "Relationships can pull strongly on you, and you are drawn to people and experiences that feel intense "
            "or outside your usual world. That openness brings variety and depth. The pattern to watch is wanting "
            "something different once the intensity settles, or holding on more tightly than is good for you."
        ),
        "Ketu": (
            "You value sincerity and personal space in relationships, and you have little patience for display or "
            "games. You are accepting of people as they are, which makes you easy to be close to. The difficulty "
            "is that you can go quiet and distant exactly when someone needs you to be present."
        ),
    },
    "professional": {
        "Sun": (
            "At work you are comfortable being the one who decides, and you take responsibility for outcomes "
            "rather than waiting to be told. You want your contribution to be visible, and you do your best work "
            "when you are trusted with something that matters. The trap is letting your position matter more than "
            "the decision itself."
        ),
        "Moon": (
            "You read people and situations quickly at work, and you often go on instinct before the information "
            "is complete. You do better in a settled atmosphere than a chaotic one, and your judgment is affected "
            "by how steady you feel. The pattern to watch is deciding on a mood and having to revisit it later."
        ),
        "Mars": (
            "At work you would rather move than wait, and once you have decided something needs doing you are "
            "usually the one who starts it. Pressure and competition tend to sharpen you, and you handle a "
            "challenge better than most. What needs watching is pace: acting quickly is one of your strengths, "
            "but it works best when the important decisions get a second look."
        ),
        "Mercury": (
            "You are at your best professionally when the work needs analysis, clear communication or "
            "negotiation. You learn new material quickly and you adapt well when the information changes. The "
            "difficulty is knowing when to stop examining the options and commit to one."
        ),
        "Jupiter": (
            "You are trusted with judgment and the longer view, and you are usually the person who asks whether "
            "the direction makes sense, not just whether the task is finished. Advising, teaching and guiding come "
            "naturally to you. The habit to watch is assuming your reading of a situation is the correct one."
        ),
        "Venus": (
            "You work well through people. Negotiation, presentation and keeping relationships in good order are "
            "genuine strengths, and you are good at finding an arrangement everyone can accept. What gets in the "
            "way is avoiding a decision because it will be unpopular with someone."
        ),
        "Saturn": (
            "You are methodical and reliable, and you would rather build something that lasts than chase a quick "
            "result. You take on responsibility willingly and you do not need supervision to keep going. The "
            "limitation is speed: you can be so careful about getting it right that you delay acting on something "
            "that is already clear."
        ),
        "Rahu": (
            "You are willing to take professional routes other people avoid, and you are comfortable with risk "
            "when the opportunity feels significant. That brings access to things conventional paths miss. It "
            "needs watching when the appetite for a shortcut outruns the foundations underneath."
        ),
        "Ketu": (
            "You are more interested in the substance of your work than its status, and you will happily take on "
            "something difficult if it teaches you something. You are good at getting to the bottom of a problem. "
            "The difficulty is sustaining interest once you understand what you were curious about."
        ),
    },
    "subconscious": {
        "Sun": (
            "At the back of your mind there is a running question about who you are and whether you are living up "
            "to your own standards. You notice when you are not being taken seriously, even if you say nothing "
            "about it. That can make you quietly self-critical, and the habit to watch is measuring yourself "
            "against an image you have never clearly defined."
        ),
        "Moon": (
            "Your subconscious mind is strongly connected to feelings, memories and emotional security. You tend "
            "to remember not only what happened, but how an experience made you feel. Familiar people, places and "
            "routines can therefore become important sources of comfort. One habit to watch is holding on to old "
            "emotions longer than necessary, especially when something has affected you deeply."
        ),
        "Mars": (
            "Your subconscious mind is quick to switch into action and defence, often before you have consciously "
            "decided anything. When something feels threatening or unfair, your first impulse is to push back. The "
            "habit to watch is reacting first and forming the question later, because that instinct fires faster "
            "than your judgment."
        ),
        "Mercury": (
            "Your subconscious mind keeps working on things after they are over, replaying conversations and "
            "looking for what you missed. You process life by explaining it to yourself, which is where a lot of "
            "your insight comes from. The habit to watch is that this rarely switches off, so a small problem can "
            "travel with you for days."
        ),
        "Jupiter": (
            "Your subconscious mind is always asking what something means, and it is rarely satisfied with the "
            "surface explanation. You instinctively look for the principle underneath, and you tend to assume "
            "there is a reason even when there may not be one. The habit to watch is becoming attached to your own "
            "interpretation before you have tested it."
        ),
        "Venus": (
            "Your subconscious mind is tuned to closeness and atmosphere, and it registers the emotional "
            "temperature of a room before anything is said. You gravitate towards comfort, pleasant company and "
            "surroundings that feel harmonious. The habit to watch is avoiding a necessary discomfort so "
            "habitually that you stop noticing you have done it."
        ),
        "Saturn": (
            "Your subconscious mind is constantly checking consequences. Before you act, you have already "
            "considered what could go wrong, what it will cost and who is depending on you. That makes you "
            "reliable, and it also means you rarely feel fully off duty. The habit to watch is carrying "
            "responsibility that was never actually handed to you."
        ),
        "Rahu": (
            "Your subconscious mind is drawn to what is missing or still out of reach, and it rarely settles on "
            "what is already here. You are curious about experiences outside your usual world, and that curiosity "
            "operates almost automatically. The habit to watch is dissatisfaction: reaching something you wanted "
            "and immediately looking past it."
        ),
        "Ketu": (
            "Your subconscious mind steps back and observes rather than participating, and it loses interest in "
            "anything that feels already understood. You are comfortable with far less external stimulation than "
            "most people. The habit to watch is withdrawal, because it can quietly remove you from situations that "
            "would actually be worth staying in."
        ),
    },
    "problems": {
        "Sun": (
            "When something goes wrong you tend to take charge of it, and you would rather meet the problem "
            "directly than wait for it to pass. People often look to you in a crisis, and you usually rise to it. "
            "What helps is letting yourself be helped, because you can treat accepting support as losing dignity. "
            "Within this tradition, the courage to act is itself the protective pattern."
        ),
        "Moon": (
            "When something goes wrong you first feel your way through it, and you notice how it is affecting the "
            "people involved. You adapt, adjust and keep going. What makes it harder is that the problem and your "
            "mood get mixed together, so it is worth giving yourself a day before deciding anything. This tradition "
            "associates the ability to adapt with protection."
        ),
        "Mars": (
            "When something goes wrong your instinct is to confront it. You deal with difficulty by acting, and "
            "you are better than most at pushing through resistance. The thing to watch is making a battle out of a "
            "situation that would answer better to patience. This tradition associates direct, determined action "
            "with protection."
        ),
        "Mercury": (
            "When something goes wrong you start gathering information and looking for the options, and you are "
            "good at finding a third route nobody has suggested. The difficulty is that more understanding does "
            "not always bring you closer to deciding. This tradition associates understanding and flexibility "
            "with protection."
        ),
        "Jupiter": (
            "When something goes wrong you look for perspective first. Understanding why it happened, and what it "
            "means, is how you steady yourself, and you often find support through people who can explain the "
            "wider picture. Watch the temptation to be certain about the lesson before the dust has settled. This "
            "tradition associates perspective and good counsel with protection."
        ),
        "Venus": (
            "When something goes wrong, your instinct is to keep the relationship intact and find a way through "
            "that everyone can live with. You are better than most at lowering the temperature and getting people "
            "to cooperate. The limitation is that you can smooth over a problem instead of solving it. This "
            "tradition associates good relationships and negotiation with protection."
        ),
        "Saturn": (
            "When something goes wrong you get patient. You work through it steadily, take the responsibility you "
            "think is yours, and keep going long after other people have stopped. That endurance is a genuine "
            "strength. It helps to remember that persistence is not the same as carrying everything alone, and "
            "that some difficulties end simply with time. This tradition associates steadiness and endurance with "
            "protection."
        ),
        "Rahu": (
            "When something goes wrong you look for an unusual way out, and you are willing to go somewhere "
            "unfamiliar to find it. Your instinct for the unconventional can produce solutions nobody else "
            "considered. The caution is risk: it is worth checking whether the shortcut is really shorter. This "
            "tradition associates adaptability and fearlessness with protection."
        ),
        "Ketu": (
            "When something goes wrong you step back from it and see what actually matters. Simplifying and "
            "letting go of the unnecessary comes naturally and often clarifies the situation. The one to watch is "
            "stepping back as a habit, because sometimes the problem needs you to stay in it. This tradition "
            "associates clarity and detachment with protection."
        ),
    },
}


def paragraph_for(category: str, planet: Optional[str]) -> Optional[str]:
    return PARAGRAPHS.get(category, {}).get(planet or "")
