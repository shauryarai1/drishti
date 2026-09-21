"""Traditional Tarot card meanings, paraphrased originally.

Core meanings follow the standard Rider-Waite-Smith tradition as commonly
taught (major arcana themes, suit elements, pip progressions, court ranks).
`contexts` holds our own structured interpretation for a specific question
domain. Nothing is scraped at runtime and no reference prose is copied.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

CARDS: Dict[str, Dict[str, Any]] = {}


def C(cid: str, name: str, suit: str, themes: List[str], up: str, rev: str,
      val: str, ctx: Optional[Dict[str, str]] = None) -> None:
    CARDS[cid] = {"id": cid, "name": name, "suit": suit, "themes": themes,
                  "upright": up, "reversed": rev, "valence": val,
                  "contexts": ctx or {}}


# --- Major Arcana --------------------------------------------------------
C("the_fool", "The Fool", "Major", ["new beginnings", "trust", "openness"], "a fresh start taken on trust", "hesitation, or rushing in unprepared", "mixed")
C("the_magician", "The Magician", "Major", ["ability", "resourcefulness", "focused will"], "you have what is needed to shape this", "scattered effort or unused ability", "positive")
C("the_high_priestess", "The High Priestess", "Major", ["intuition", "what is unspoken", "patience"], "the answer is felt before it is explained; wait", "ignoring instinct or forcing disclosure", "mixed")
C("the_empress", "The Empress", "Major", ["nurture", "growth", "comfort"], "steady growth and support; things develop naturally", "neglect, over-giving or stalled growth", "positive")
C("the_emperor", "The Emperor", "Major", ["structure", "authority", "boundaries"], "order and clear structure bring progress", "rigidity, or the lack of any structure", "mixed")
C("the_hierophant", "The Hierophant", "Major", ["guidance", "tradition", "learning"], "established guidance or a teacher helps here", "going against sound advice", "mixed")
C("the_lovers", "The Lovers", "Major", ["connection", "choice", "alignment"], "a meaningful connection, or a choice to be made honestly", "misalignment, or avoiding the choice", "positive")
C("the_chariot", "The Chariot", "Major", ["direction", "willpower", "momentum"], "progress through steady will and direction", "lack of direction or pushing too hard", "positive")
C("strength", "Strength", "Major", ["patience", "quiet courage", "self-control"], "calm persistence is what wins here", "doubt, impatience or lost composure", "positive")
C("the_hermit", "The Hermit", "Major", ["reflection", "solitude", "slowing down"], "step back and look inward before acting", "isolation, or refusing needed advice", "mixed")
C("wheel_of_fortune", "Wheel of Fortune", "Major", ["turning point", "cycles", "timing"], "circumstances are shifting; timing matters", "resisting a change already underway", "mixed")
C("justice", "Justice", "Major", ["fairness", "truth", "balance"], "honesty and balance decide the outcome", "avoiding responsibility, or a one-sided view", "mixed")
C("the_hanged_man", "The Hanged Man", "Major", ["pause", "perspective", "waiting"], "a pause now brings a better view later", "stalling, or refusing to see it differently", "mixed")
C("death", "Death", "Major", ["endings", "transition", "release"], "something is ending so something else can begin", "holding on to what has already finished", "mixed")
C("temperance", "Temperance", "Major", ["balance", "moderation", "patience"], "measured steps work better than extremes", "imbalance or impatience", "positive")
C("the_devil", "The Devil", "Major", ["attachment", "temptation", "restriction"], "a pattern or attachment is limiting the choice", "loosening a hold that was never real", "challenging")
C("the_tower", "The Tower", "Major", ["sudden change", "upheaval", "rebuilding"], "an abrupt change clears what could not stand", "a crisis postponed rather than resolved", "challenging")
C("the_star", "The Star", "Major", ["hope", "healing", "renewal"], "quiet hope and recovery; the direction is sound", "discouragement or lost faith in the process", "positive")
C("the_moon", "The Moon", "Major", ["uncertainty", "instinct", "confusion"], "not everything is visible yet; trust instinct and wait", "fears mistaken for facts", "challenging")
C("the_sun", "The Sun", "Major", ["clarity", "warmth", "success"], "clear, encouraging conditions and visible progress", "delays to something still favourable", "positive")
C("judgement", "Judgement", "Major", ["reckoning", "decision", "awakening"], "an honest reassessment leads to a real decision", "avoiding the reckoning or second-guessing", "mixed")
C("the_world", "The World", "Major", ["completion", "fulfilment", "arrival"], "a cycle completes well; the result is earned", "almost there; the last step unfinished", "positive")

# --- Wands ---------------------------------------------------------------
C("ace_of_wands", "Ace of Wands", "Wands", ["spark", "initiative", "new drive"], "a new opening with energy behind it", "a stalled start or a spark not acted on", "positive")
C("two_of_wands", "Two of Wands", "Wands", ["planning", "direction", "ambition"], "you are deciding which direction to commit to", "staying undecided, or delaying the choice", "mixed")
C("three_of_wands", "Three of Wands", "Wands",
  ["looking ahead", "confidence", "progress", "expansion", "preparation", "patience for results"],
  "effort is beginning to show results; progress is real but still forming",
  "delays, impatience with the pace, or waiting longer than expected", "positive",
  ctx={
    "education_exam": "You seem to be going into this with a fairly positive mindset. The preparation you have already done matters more than last-minute panic, and there is a sense that you expect your effort to produce a result. Stay confident, but do not let optimism replace final revision.",
    "love_attraction": "There is room for this to move forward, but patience matters. You may already be hoping for a particular answer, so try not to rush a response out of her. Give the situation space to develop in its own time.",
    "career_opportunity": "This looks worth seriously exploring, especially if it gives you room to grow beyond what you are doing now. Think beyond the immediate benefit and ask where it could put you a year or two from now.",
  })
C("four_of_wands", "Four of Wands", "Wands", ["celebration", "stability", "belonging"], "a settled stage or a milestone reached", "a celebration delayed or home unsettled", "positive")
C("five_of_wands", "Five of Wands", "Wands", ["competition", "friction", "rivalry"], "competing interests create friction but not defeat", "conflict easing, or avoided tension resurfacing", "challenging")
C("six_of_wands", "Six of Wands", "Wands", ["recognition", "victory", "confidence"], "recognition and a well-earned win", "recognition delayed or sought too eagerly", "positive")
C("seven_of_wands", "Seven of Wands", "Wands", ["defending", "pressure", "persistence"], "you hold your position under pressure", "overwhelm, or giving ground too easily", "challenging")
C("eight_of_wands", "Eight of Wands", "Wands", ["speed", "movement", "news"], "things move quickly and messages arrive", "delays, crossed signals or haste causing mistakes", "positive")
C("nine_of_wands", "Nine of Wands", "Wands", ["resilience", "caution", "endurance"], "tired but close; endurance carries you", "worn down, or defensive before it is needed", "mixed")
C("ten_of_wands", "Ten of Wands", "Wands", ["burden", "overload", "completion near"], "too much is being carried; the load needs reducing", "refusing help, or dropping something important", "challenging")
C("page_of_wands", "Page of Wands", "Wands", ["enthusiasm", "curiosity", "exploration"], "fresh interest and willingness to explore", "scattered enthusiasm or a false start", "mixed")
C("knight_of_wands", "Knight of Wands", "Wands", ["action", "boldness", "risk"], "bold, fast action drives this", "recklessness or impulsive moves", "mixed")
C("queen_of_wands", "Queen of Wands", "Wands", ["confidence", "warmth", "magnetism"], "warm confidence carries this", "self-doubt or jealousy", "positive")
C("king_of_wands", "King of Wands", "Wands", ["leadership", "vision", "decisive action"], "visionary, decisive leadership shapes the outcome", "domineering or impulsive leadership", "positive")

# --- Cups ----------------------------------------------------------------
C("ace_of_cups", "Ace of Cups", "Cups", ["new feeling", "openness", "compassion"], "a genuine new feeling or fresh opening", "guarded feelings or an opening missed", "positive")
C("two_of_cups", "Two of Cups", "Cups", ["mutual connection", "partnership", "attraction"], "mutual interest and genuine connection", "imbalance, or one side holding back", "positive")
C("three_of_cups", "Three of Cups", "Cups", ["friendship", "shared joy", "support"], "friendship and shared support are strong here", "social friction or overindulgence", "positive")
C("four_of_cups", "Four of Cups", "Cups", ["apathy", "reassessment", "missed offer"], "something on offer is being overlooked; look again", "renewed interest or emerging from withdrawal", "challenging")
C("five_of_cups", "Five of Cups", "Cups", ["loss", "regret", "what remains"], "attention is on what was lost rather than what remains", "acceptance and moving forward", "challenging")
C("six_of_cups", "Six of Cups", "Cups", ["nostalgia", "past connection", "familiarity"], "the past, or a familiar bond, plays a part", "being held back by the past", "mixed")
C("seven_of_cups", "Seven of Cups", "Cups", ["options", "fantasy", "wishful thinking"], "many options, some of them fantasy rather than real", "clearer choices, or disillusionment", "challenging")
C("eight_of_cups", "Eight of Cups", "Cups", ["walking away", "seeking meaning", "discontent"], "something is being left behind for something more meaningful", "returning, or leaving without closure", "mixed")
C("nine_of_cups", "Nine of Cups", "Cups", ["satisfaction", "contentment", "fulfilment"], "contentment, and a wish moving toward fulfilment", "surface satisfaction, or a wish unmet", "positive")
C("ten_of_cups", "Ten of Cups", "Cups", ["harmony", "family", "lasting contentment"], "lasting emotional harmony and shared happiness", "strained harmony or unrealistic ideals", "positive")
C("page_of_cups", "Page of Cups", "Cups", ["tender feeling", "message", "sensitivity"], "a gentle message or new feeling is emerging", "moodiness, or feelings left unspoken", "mixed")
C("knight_of_cups", "Knight of Cups", "Cups", ["romance", "offer", "following feeling"], "a heartfelt offer, or following feeling over logic", "moodiness, or an offer that is not solid", "mixed")
C("queen_of_cups", "Queen of Cups", "Cups", ["empathy", "care", "emotional depth"], "emotional intelligence and care define this", "emotional overwhelm or over-attachment", "positive")
C("king_of_cups", "King of Cups", "Cups", ["emotional balance", "maturity", "calm"], "calm, mature handling of feelings", "repressed feeling or emotional pressure", "positive")

# --- Swords --------------------------------------------------------------
C("ace_of_swords", "Ace of Swords", "Swords", ["clarity", "truth", "breakthrough"], "clarity cuts through; a decision becomes clear", "confusion, or truth used harshly", "positive")
C("two_of_swords", "Two of Swords", "Swords", ["stalemate", "avoidance", "hard choice"], "a decision is being avoided; the balance is fragile", "the standoff breaking, or clarity returning", "challenging")
C("three_of_swords", "Three of Swords", "Swords", ["hurt", "painful truth", "disappointment"], "a painful truth has to be acknowledged", "healing begins, or hurt is held on to", "challenging")
C("four_of_swords", "Four of Swords", "Swords", ["rest", "recovery", "pause"], "rest and recovery are needed before the next step", "restlessness, or pushing through exhaustion", "mixed")
C("five_of_swords", "Five of Swords", "Swords", ["conflict", "tension", "hollow victory"], "conflict exists; winning may cost more than it is worth", "conflict easing, or being left behind", "challenging")
C("six_of_swords", "Six of Swords", "Swords", ["transition", "moving on", "calmer waters"], "a difficult passage is being crossed toward calmer ground", "staying stuck, or carrying the past along", "mixed")
C("seven_of_swords", "Seven of Swords", "Swords", ["strategy", "evasion", "hidden action"], "not everything is open; care and strategy are needed", "secrecy coming to light", "challenging")
C("eight_of_swords", "Eight of Swords", "Swords", ["feeling trapped", "fear", "narrow view"], "the restriction is mostly in the mind; options exist", "finding the way out and taking it", "challenging")
C("nine_of_swords", "Nine of Swords", "Swords", ["worry", "anxiety", "imagined fears"], "worry is magnifying the problem beyond its size", "relief as fears are named and shrink", "challenging")
C("ten_of_swords", "Ten of Swords", "Swords", ["ending", "exhaustion", "new dawn"], "a hard ending; the worst is passing and recovery can start", "recovery underway, or pain drawn out", "challenging")
C("page_of_swords", "Page of Swords", "Swords", ["curiosity", "questions", "new information"], "information and questions matter more than assumptions", "gossip, haste or misread information", "mixed")
C("knight_of_swords", "Knight of Swords", "Swords", ["direct action", "fast decision", "assertion"], "swift, direct action moves this forward", "haste causing avoidable damage", "mixed")
C("queen_of_swords", "Queen of Swords", "Swords", ["clear judgment", "honesty", "boundaries"], "clear, honest judgment and firm boundaries", "coldness or cutting words", "positive")
C("king_of_swords", "King of Swords", "Swords", ["reason", "truth", "fair decision"], "reason and fair judgment govern the outcome", "rigid thinking, or authority misused", "positive")

# --- Pentacles -----------------------------------------------------------
C("ace_of_pentacles", "Ace of Pentacles", "Pentacles", ["opportunity", "practical start", "security"], "a practical opportunity with real potential", "a missed opportunity or a slow start", "positive")
C("two_of_pentacles", "Two of Pentacles", "Pentacles", ["balance", "juggling", "priorities"], "several things are being balanced at once", "dropping a ball, or poor priorities", "mixed")
C("three_of_pentacles", "Three of Pentacles", "Pentacles", ["teamwork", "skill", "recognition"], "skill and cooperation build the result", "poor collaboration or unrecognised effort", "positive")
C("four_of_pentacles", "Four of Pentacles", "Pentacles", ["holding on", "security", "control"], "holding on tightly; security is being guarded", "loosening control, or financial pressure", "mixed")
C("five_of_pentacles", "Five of Pentacles", "Pentacles", ["hardship", "lack", "support available"], "hardship is present, but support exists nearby", "recovery from a difficult stretch", "challenging")
C("six_of_pentacles", "Six of Pentacles", "Pentacles", ["help", "generosity", "fair exchange"], "help is available and exchange becomes fair", "unequal giving, or strings attached", "positive")
C("seven_of_pentacles", "Seven of Pentacles", "Pentacles", ["patience", "assessment", "long-term view"], "results come from patience; assess before changing course", "impatience, or effort in the wrong place", "mixed")
C("eight_of_pentacles", "Eight of Pentacles", "Pentacles", ["diligence", "practice", "craft"], "steady, focused effort builds the result", "repetition without progress, or cutting corners", "positive")
C("nine_of_pentacles", "Nine of Pentacles", "Pentacles", ["independence", "enjoyment", "earned comfort"], "earned comfort and independence", "dependence, or comfort not yet earned", "positive")
C("ten_of_pentacles", "Ten of Pentacles", "Pentacles", ["lasting security", "family", "legacy"], "lasting security and something built to endure", "instability, or family expectations weighing in", "positive")
C("page_of_pentacles", "Page of Pentacles", "Pentacles", ["study", "practical start", "diligence"], "a practical beginning, best served by steady study", "daydreaming instead of starting", "mixed")
C("knight_of_pentacles", "Knight of Pentacles", "Pentacles", ["reliability", "routine", "slow progress"], "reliable, unhurried progress gets there", "stagnation or stubborn routine", "mixed")
C("queen_of_pentacles", "Queen of Pentacles", "Pentacles", ["practical care", "resourcefulness", "comfort"], "practical care and good management of resources", "overextension, or neglecting your own needs", "positive")
C("king_of_pentacles", "King of Pentacles", "Pentacles", ["stability", "provision", "authority"], "stability, provision and sound management", "rigidity about money or control", "positive")


def contextual_entry(card_id: str, subcontext: str) -> Optional[str]:
    card = CARDS.get(card_id) or {}
    return (card.get("contexts") or {}).get(subcontext)
