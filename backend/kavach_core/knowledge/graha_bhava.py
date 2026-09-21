"""GRAHA_IN_BHAVA ? standard/common Vedic Graha-in-Bhava principles.

108 placements (9 Grahas x 12 Bhavas). Each record is the placement read as a
WHOLE (not planet keywords + house keywords). Themes are tagged with the KAVACH
channel domains they can support, so the channel lens can filter them.

PROVENANCE: source_type = "standard_jyotish" (common principles paraphrased
from the classical Bhava/Graha framework and established Jyotish references).
No source prose is copied. Rahu/Ketu carry no classical sign ownership or
dignity. House 8 is never death. No lifespan or medical content.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

Theme = Tuple[str, Tuple[str, ...]]

GRAHA_BHAVA: Dict[str, Dict[int, Dict[str, object]]] = {
    "Sun": {
        1: {
            "themes": [
                ("you lead with your presence and prefer to act on your own judgment", ("personality", "career")),
                ("being seen and respected matters to you more than you usually admit", ("relationships",)),
                ("a quiet need for recognition sits under many of your choices", ("inner", "challenges")),
            ],
            "constructive": ["natural authority that people accept when you stay fair-minded"],
            "challenging": ["pride can resist good advice exactly when it would help most"],
            "guidance": ["your influence grows when confidence is worn lightly"],
        },
        2: {
            "themes": [
                ("you take personal pride in what you earn and what you provide", ("personality", "career")),
                ("family standing and clear speech matter to your sense of worth", ("relationships",)),
                ("worth and identity can become tangled, so value is often measured by resources", ("inner", "challenges")),
            ],
            "constructive": ["the ability to build steadily and to speak with natural conviction"],
            "challenging": ["self-worth can rise and fall with income if left unexamined"],
            "guidance": ["separate who you are from what you hold"],
        },
        3: {
            "themes": [
                ("you express yourself through effort, initiative and self-taught skill", ("personality", "career")),
                ("communication with siblings and peers is a lifelong arena of growth", ("relationships",)),
                ("courage is built by doing, and hesitation tends to be short-lived", ("inner", "challenges")),
            ],
            "constructive": ["bold self-expression and a willingness to try first and refine later"],
            "challenging": ["impatience with slower minds can create friction"],
            "guidance": ["steady effort serves you better than bursts of willpower"],
        },
        4: {
            "themes": [
                ("you seek a home base that reflects your identity and authority", ("personality", "career")),
                ("family and domestic life are central to your emotional standing", ("relationships",)),
                ("inner security depends on having a space that is truly your own", ("inner", "challenges")),
            ],
            "constructive": ["a stabilizing presence at home that others rely on"],
            "challenging": ["domestic pride or parental expectations can weigh on you"],
            "guidance": ["peace at home begins with how you carry yourself inside it"],
        },
        5: {
            "themes": [
                ("you express yourself creatively and want your talents recognised", ("personality", "career")),
                ("romance and children bring warmth and also lessons in humility", ("relationships",)),
                ("confidence grows when you create from genuine interest rather than approval", ("inner", "challenges")),
            ],
            "constructive": ["creative confidence and a natural pull toward leadership in learning"],
            "challenging": ["wanting to shine can overshadow patient practice"],
            "guidance": ["enjoy the making more than the showing"],
        },
        6: {
            "themes": [
                ("you take on responsibility and often carry more than your share", ("personality", "career")),
                ("service and duty shape your closest working relationships", ("relationships",)),
                ("friction and competition are familiar teachers rather than disasters", ("inner", "challenges")),
            ],
            "constructive": ["endurance in difficult conditions and skill at solving problems"],
            "challenging": ["overwork and irritability when limits are ignored"],
            "guidance": ["protect your energy as deliberately as you protect others"],
        },
        7: {
            "themes": [
                ("partnership shapes your sense of self more than solitude does", ("personality", "career")),
                ("you are drawn to partners of strength and expect mutual respect", ("relationships",)),
                ("learning to compromise is a recurring inner task", ("inner", "challenges")),
            ],
            "constructive": ["loyalty in partnership and a wish for fair dealings"],
            "challenging": ["the wish to lead in partnership can become a contest"],
            "guidance": ["meet partners as equals rather than rivals"],
        },
        8: {
            "themes": [
                ("you are drawn to what lies beneath surfaces and tolerate intensity well", ("personality", "career")),
                ("trust in closeness is built slowly and matters deeply", ("relationships",)),
                ("change and uncertainty push you to rebuild from the inside", ("inner", "challenges")),
            ],
            "constructive": ["resilience in upheaval and interest in hidden causes"],
            "challenging": ["control can tighten when vulnerability appears"],
            "guidance": ["let change finish its work before forcing a conclusion"],
        },
        9: {
            "themes": [
                ("you seek meaning and want your beliefs to guide your direction", ("personality", "career")),
                ("teachers, mentors and higher learning shape your relationships", ("relationships",)),
                ("faith is examined rather than inherited, and grows through questioning", ("inner", "challenges")),
            ],
            "constructive": ["principled outlook and natural capacity to guide others"],
            "challenging": ["certainty can close the door to further learning"],
            "guidance": ["keep your philosophy generous enough to include new facts"],
        },
        10: {
            "themes": [
                ("your identity is closely tied to reputation and public duty", ("personality", "career")),
                ("professional standing influences how you relate to authority and family", ("relationships",)),
                ("pressure to achieve can quietly overshadow private needs", ("inner", "challenges")),
            ],
            "constructive": ["capable leadership and steady responsibility in public roles"],
            "challenging": ["status anxiety when recognition lags behind effort"],
            "guidance": ["build work that still matters when nobody is watching"],
        },
        11: {
            "themes": [
                ("you direct energy toward goals shared with groups and networks", ("personality", "career")),
                ("friendships and alliances are central to what you gain", ("relationships",)),
                ("expectations of others can become a private weight", ("inner", "challenges")),
            ],
            "constructive": ["capacity to gather people around a common aim"],
            "challenging": ["over-identifying with group approval"],
            "guidance": ["choose your circles rather than being chosen by them"],
        },
        12: {
            "themes": [
                ("you need periods of withdrawal to restore your sense of self", ("personality", "challenges")),
                ("quiet and private settings matter more to your relationships than public ones", ("relationships",)),
                ("release and reflection restore you more than striving does", ("inner",)),
            ],
            "constructive": ["inner depth and comfort with solitude and reflection"],
            "challenging": ["energy can drain silently when rest is postponed"],
            "guidance": ["treat quiet time as necessary, not indulgent"],
        },
    },
    "Moon": {
        1: {
            "themes": [
                ("your mood is visible and your first response is feeling rather than analysis", ("personality", "relationships")),
                ("receptivity draws others close, and your manner sets the emotional tone", ("relationships",)),
                ("feelings arrive quickly and need time before they become decisions", ("inner", "challenges")),
            ],
            "constructive": ["warmth and read on people's feelings that puts them at ease"],
            "challenging": ["taking on the moods of others until they feel like your own"],
            "guidance": ["notice feelings without becoming them"],
        },
        2: {
            "themes": [
                ("resource matters are handled with care and emotional attachment", ("personality", "career")),
                ("family, food and shared comfort are central to your sense of wellbeing", ("relationships",)),
                ("security needs can tighten around money and speech", ("inner", "challenges")),
            ],
            "constructive": ["instinct for saving and for making people feel provided for"],
            "challenging": ["anxious spending or withholding when security feels threatened"],
            "guidance": ["let values, not fear, set the standard for enough"],
        },
        3: {
            "themes": [
                ("you think out loud and learn best in conversation", ("personality", "career")),
                ("siblings, neighbours and daily contact shape your emotional world", ("relationships",)),
                ("restlessness is often curiosity rather than anxiety", ("inner", "challenges")),
            ],
            "constructive": ["fluent communication and ease with many kinds of people"],
            "challenging": ["scattered attention when feelings are unsettled"],
            "guidance": ["write or speak your thinking out to settle it"],
        },
        4: {
            "themes": [
                ("home is where you feel most yourself and most protected", ("personality", "relationships")),
                ("family ties shape your emotional patterns for a long time", ("relationships",)),
                ("inner peace depends on the safety of your base", ("inner", "challenges")),
            ],
            "constructive": ["instinctive care for home and a settling presence for others"],
            "challenging": ["emotional weather carried from the childhood home"],
            "guidance": ["build the home you needed, in your own way"],
        },
        5: {
            "themes": [
                ("you play, create and love with real feeling", ("personality", "relationships")),
                ("romance and children bring out both delight and protectiveness", ("relationships",)),
                ("creative confidence rises and falls with mood, so rhythm matters", ("inner", "challenges")),
            ],
            "constructive": ["natural affectionate creativity that others enjoy"],
            "challenging": ["needing approval before allowing yourself to create"],
            "guidance": ["make things for the pleasure of making them"],
        },
        6: {
            "themes": [
                ("you are sensitive to the daily atmosphere of work and health", ("personality", "career")),
                ("routine and service feel personal, and you notice what is out of order", ("relationships",)),
                ("worry about details is a recurring mental habit", ("inner", "challenges")),
            ],
            "constructive": ["attentive service and care for the small things others miss"],
            "challenging": ["stress showing up in the body when it is not expressed"],
            "guidance": ["let routine carry you instead of pressing on you"],
        },
        7: {
            "themes": [
                ("you relate through feeling and need warmth in your dealings", ("personality", "relationships")),
                ("partnership is an emotional home as much as a commitment", ("relationships",)),
                ("harmony is sought quickly, sometimes before honesty", ("inner", "challenges")),
            ],
            "constructive": ["genuine sensitivity to a partner's needs and moods"],
            "challenging": ["avoiding necessary conversations to keep the peace"],
            "guidance": ["kind honesty protects closeness better than silence"],
        },
        8: {
            "themes": [
                ("your feelings run deep and you sense what others conceal", ("personality", "inner")),
                ("closeness involves trust that is earned slowly", ("relationships",)),
                ("emotional change arrives in waves rather than gradually", ("challenges",)),
            ],
            "constructive": ["emotional courage and the ability to stay present in hard times"],
            "challenging": ["moods that intensify when they are suppressed"],
            "guidance": ["let intensity be shared rather than managed alone"],
        },
        9: {
            "themes": [
                ("you feel your way toward beliefs and meaning", ("personality", "inner")),
                ("teachers and travel stir genuine emotional response", ("relationships",)),
                ("faith grows through experience rather than argument", ("challenges",)),
            ],
            "constructive": ["warm guidance of others and openness to other cultures"],
            "challenging": ["restlessness when meaning feels absent"],
            "guidance": ["let experience, not certainty, guide your principles"],
        },
        10: {
            "themes": [
                ("you work with care for people and atmosphere, not only results", ("personality", "career")),
                ("public standing matters partly because it affects how you feel valued", ("relationships",)),
                ("mood and professional confidence move together", ("inner", "challenges")),
            ],
            "constructive": ["leadership that is approachable and attentive to people"],
            "challenging": ["taking professional criticism deeply"],
            "guidance": ["measure work by consistency, not by daily feeling"],
        },
        11: {
            "themes": [
                ("you are nourished by friendship and shared hopes", ("personality", "relationships")),
                ("gains feel meaningful when shared with people you care about", ("relationships",)),
                ("the need for belonging can shape ambitions quietly", ("inner", "challenges")),
            ],
            "constructive": ["building supportive communities and long friendships"],
            "challenging": ["letting group expectations override your own aims"],
            "guidance": ["choose hopes that are genuinely yours"],
        },
        12: {
            "themes": [
                ("your inner life is active and you need privacy to restore it", ("personality", "inner")),
                ("emotional release happens best away from crowds", ("relationships",)),
                ("feelings surface slowly and benefit from quiet attention", ("challenges")),
            ],
            "constructive": ["compassion and insight that come from listening inward"],
            "challenging": ["moods collecting unnoticed until they overwhelm"],
            "guidance": ["give feelings deliberate quiet time before deciding anything"],
        },
    },
    "Mars": {
        1: {
            "themes": [
                ("you move on impulse and prefer action to deliberation", ("personality", "career")),
                ("directness defines your dealings with others, for better and worse", ("relationships",)),
                ("restlessness is your default state when nothing is being pursued", ("inner", "challenges")),
            ],
            "constructive": ["courage, drive and willingness to take the first step"],
            "challenging": ["heat rising faster than judgment"],
            "guidance": ["channel drive into one clear objective at a time"],
        },
        2: {
            "themes": [
                ("you pursue resources energetically and defend what you consider yours", ("career", "personality")),
                ("plain speech is typical, and family disagreements are handled head-on", ("relationships",)),
                ("friction appears when resources feel insecure", ("challenges",)),
            ],
            "constructive": ["initiative in earning and the courage to state terms clearly"],
            "challenging": ["sharp speech in moments of frustration"],
            "guidance": ["let clear numbers replace heated words in money matters"],
        },
        3: {
            "themes": [
                ("you are bold in self-expression and quick to act on ideas", ("personality", "career")),
                ("siblings and peers know exactly where you stand", ("relationships",)),
                ("mental energy is high and idles poorly", ("inner", "challenges")),
            ],
            "constructive": ["decisive communication and competitive effort"],
            "challenging": ["argument for its own sake when energy has no outlet"],
            "guidance": ["turn restlessness into practice, not into disputes"],
        },
        4: {
            "themes": [
                ("you defend your home and those in it with force if needed", ("personality", "relationships")),
                ("domestic life can be lively, competitive or occasionally combative", ("relationships",)),
                ("inner security is tied to control over your immediate environment", ("inner", "challenges")),
            ],
            "constructive": ["protective energy that makes home feel safe"],
            "challenging": ["tension at home when energy has nowhere to go"],
            "guidance": ["channel combativeness into maintaining the household, not into it"],
        },
        5: {
            "themes": [
                ("you pursue interests, games and romance with competitive energy", ("personality", "relationships")),
                ("romance runs warm and can move quickly", ("relationships",)),
                ("creative drive wants a challenge, not a hobby", ("inner", "challenges")),
            ],
            "constructive": ["bold creativity and enthusiasm that carries others along"],
            "challenging": ["impatience when results do not come quickly"],
            "guidance": ["let effort, not winning, define your enjoyment"],
        },
        6: {
            "themes": [
                ("you attack problems directly and work hard under pressure", ("personality", "career")),
                ("competition at work is familiar ground for you", ("relationships",)),
                ("frustration builds when obstacles persist despite effort", ("inner", "challenges")),
            ],
            "constructive": ["excellent crisis energy and capacity to outlast difficulties"],
            "challenging": ["irritability, overexertion and arguing with what cannot be changed"],
            "guidance": ["fight the problem, never the people around it"],
        },
        7: {
            "themes": [
                ("you engage others energetically and take positions in discussions", ("personality", "career")),
                ("partnership requires negotiation because your instinct is to push", ("relationships",)),
                ("patience in close dealings is a deliberate practice", ("inner", "challenges")),
            ],
            "constructive": ["decisive handling of joint matters and readiness to act for both parties"],
            "challenging": ["conflict when compromise feels like losing"],
            "guidance": ["in negotiation, aim for agreement rather than victory"],
        },
        8: {
            "themes": [
                ("you meet intensity and change with a willingness to fight through", ("personality", "challenges")),
                ("trust and shared resources are handled with caution and forcefulness", ("relationships",)),
                ("stress arrives suddenly and you prefer to confront it directly", ("inner", "challenges")),
            ],
            "constructive": ["bravery in crisis and stamina for difficult passages"],
            "challenging": ["reacting before the full picture is clear"],
            "guidance": ["pause before acting when the situation is still unfolding"],
        },
        9: {
            "themes": [
                ("you pursue beliefs actively and argue for your convictions", ("personality", "career")),
                ("teachers and travel are met with enthusiasm and challenge", ("relationships",)),
                ("philosophy is lived rather than merely studied", ("inner", "challenges")),
            ],
            "constructive": ["energetic pursuit of learning and journeys"],
            "challenging": ["treating disagreement as a contest"],
            "guidance": ["let enquiry stay open even when you argue strongly"],
        },
        10: {
            "themes": [
                ("you pursue professional goals with competitive drive", ("career", "personality")),
                ("authority is met directly, sometimes head-on", ("relationships",)),
                ("you would rather act than wait for permission", ("inner", "challenges")),
            ],
            "constructive": ["executive energy and ability to push projects to completion"],
            "challenging": ["workplace friction when ambition outruns diplomacy"],
            "guidance": ["choose the battles that move your work forward"],
        },
        11: {
            "themes": [
                ("you work hard for shared goals and expect effort from others", ("career", "personality")),
                ("friendships include energy, competition and occasional arguments", ("relationships",)),
                ("frustration appears when gains arrive slowly", ("inner", "challenges")),
            ],
            "constructive": ["drive that rallies groups toward a result"],
            "challenging": ["strained friendships when ambition hardens"],
            "guidance": ["keep alliances warm, not merely useful"],
        },
        12: {
            "themes": [
                ("energy turns inward and needs a private outlet", ("inner", "challenges")),
                ("quiet or distant settings suit your relationships better than constant contact", ("relationships",)),
                ("unexpressed frustration shows up as fatigue or restlessness", ("challenges",)),
            ],
            "constructive": ["capacity for sustained solitary work and self-discipline"],
            "challenging": ["energy draining silently into resentment"],
            "guidance": ["give the drive a private practice to consume it"],
        },
    },
    "Mercury": {
        1: {
            "themes": [
                ("you come across as articulate, curious and quick to reason", ("personality", "career")),
                ("conversation is how you connect, and words carry real weight for you", ("relationships",)),
                ("your mind rarely stops, which is both your gift and your restlessness", ("inner", "challenges")),
            ],
            "constructive": ["clear thinking and a talent for explaining things simply"],
            "challenging": ["overthinking choices that do not need this much analysis"],
            "guidance": ["think it through once, then act"],
        },
        2: {
            "themes": [
                ("you handle resources with calculation and careful words", ("personality", "career")),
                ("speech and family communication are central to your sense of value", ("relationships",)),
                ("you are skilled at making limited means go further", ("challenges")),
            ],
            "constructive": ["practical intelligence about money, trade and negotiation"],
            "challenging": ["worrying about security until it becomes mental noise"],
            "guidance": ["keep written accounts so your mind can relax"],
        },
        3: {
            "themes": [
                ("communication, writing and learning are your natural instruments", ("personality", "career")),
                ("siblings, peers and daily contacts keep your mind active", ("relationships",)),
                ("you learn by speaking, teaching and exchanging ideas", ("inner", "challenges")),
            ],
            "constructive": ["versatile skill, quick learning and persuasive expression"],
            "challenging": ["scattering attention across too many interests"],
            "guidance": ["finish more than you begin"],
        },
        4: {
            "themes": [
                ("you think about home, roots and belonging in practical terms", ("personality", "relationships")),
                ("family conversation and domestic learning shape your outlook", ("relationships",)),
                ("inner security comes from understanding where you come from", ("inner", "challenges")),
            ],
            "constructive": ["careful planning for home and property matters"],
            "challenging": ["mental restlessness even when you are settled"],
            "guidance": ["make your home a place where the mind can slow down"],
        },
        5: {
            "themes": [
                ("you are intelligent, inventive and playful with ideas", ("personality", "career")),
                ("romance is approached with curiosity and conversation", ("relationships",)),
                ("learning and creating are how you express yourself", ("inner", "challenges")),
            ],
            "constructive": ["original thinking and strong capacity for study"],
            "challenging": ["turning play into performance and losing the pleasure"],
            "guidance": ["keep learning playful rather than proving something"],
        },
        6: {
            "themes": [
                ("you analyse problems at work and prefer method to improvisation", ("career", "personality")),
                ("service and routine run better when you can negotiate the terms", ("relationships",)),
                ("an active mind can magnify small worries", ("inner", "challenges")),
            ],
            "constructive": ["problem-solving skill and attention to detail"],
            "challenging": ["anxiety fed by analysing what cannot be controlled"],
            "guidance": ["solve what is solvable and put the rest down"],
        },
        7: {
            "themes": [
                ("you relate through conversation and need intellectual company", ("personality", "relationships")),
                ("partnership works best as an equal exchange of views", ("relationships",)),
                ("you think your way through relationship questions", ("inner", "challenges")),
            ],
            "constructive": ["skilled negotiation and fair, reasoned dealing"],
            "challenging": ["debating when your partner wants understanding"],
            "guidance": ["listen to understand before answering"],
        },
        8: {
            "themes": [
                ("you are drawn to research, hidden causes and close analysis", ("personality", "career")),
                ("trust is discussed and reasoned about before it is felt", ("relationships",)),
                ("your mind works well in complex or uncertain conditions", ("inner", "challenges")),
            ],
            "constructive": ["investigative intelligence and comfort with complexity"],
            "challenging": ["mental overactivity when feelings are involved"],
            "guidance": ["let understanding come gradually in emotional matters"],
        },
        9: {
            "themes": [
                ("you pursue knowledge widely and enjoy comparing viewpoints", ("personality", "career")),
                ("teachers, study and travel expand how you communicate", ("relationships",)),
                ("beliefs are assembled by reasoning rather than inherited", ("inner", "challenges")),
            ],
            "constructive": ["broad learning and ability to teach what you know"],
            "challenging": ["collecting ideas without settling on principles"],
            "guidance": ["let study deepen conviction, not just information"],
        },
        10: {
            "themes": [
                ("your professional value lies in analysis, communication and organisation", ("career", "personality")),
                ("you deal with authority through discussion and clever positioning", ("relationships",)),
                ("you think carefully about reputation and how work is perceived", ("inner", "challenges")),
            ],
            "constructive": ["excellent professional judgment and adaptability"],
            "challenging": ["spreading effort across too many directions at work"],
            "guidance": ["choose the work where your thinking is most needed"],
        },
        11: {
            "themes": [
                ("you gain through networks, information and clever collaboration", ("career", "personality")),
                ("friendships are based on shared interests and lively exchange", ("relationships",)),
                ("you calculate how to reach goals efficiently", ("inner", "challenges")),
            ],
            "constructive": ["talent for connecting people and opportunities"],
            "challenging": ["treating relationships as transactions"],
            "guidance": ["let some gains come from goodwill, not strategy"],
        },
        12: {
            "themes": [
                ("your mind turns inward and finds meaning in reflection", ("inner", "personality")),
                ("you communicate best in quieter or written settings", ("relationships",)),
                ("imagination is strong but can turn into private worry", ("challenges")),
            ],
            "constructive": ["imaginative, contemplative intelligence"],
            "challenging": ["overanalysis when alone with a problem"],
            "guidance": ["write it down and let privacy do its work"],
        },
    },
    "Jupiter": {
        1: {
            "themes": [
                ("you carry natural optimism and are looked to for guidance", ("personality", "career")),
                ("your presence encourages others, and generosity defines your dealings", ("relationships",)),
                ("growth comes from widening your view of yourself", ("inner", "challenges")),
            ],
            "constructive": ["confidence, goodwill and a broadening influence on others"],
            "challenging": ["overpromising out of optimism"],
            "guidance": ["give others advice they can actually use"],
        },
        2: {
            "themes": [
                ("you tend to build confidence through what you know and value", ("personality", "career")),
                ("family, speech and shared resources grow through generosity and wisdom", ("relationships",)),
                ("prosperity is connected with learning, advising and responsible values", ("inner", "challenges")),
            ],
            "constructive": ["capacity to grow resources and to speak with wise encouragement"],
            "challenging": ["comfort and abundance can drift into complacency"],
            "guidance": ["let what you value, not what you possess, set your standard"],
        },
        3: {
            "themes": [
                ("you expand through communication, teaching and self-directed learning", ("personality", "career")),
                ("siblings and neighbours benefit from your encouragement", ("relationships",)),
                ("optimism fuels sustained effort and skill-building", ("inner", "challenges")),
            ],
            "constructive": ["inspiring communication and a broad, generous mind"],
            "challenging": ["talking expansively without following through"],
            "guidance": ["say less and complete more"],
        },
        4: {
            "themes": [
                ("you bring warmth and a sense of abundance to home life", ("personality", "relationships")),
                ("family and roots are sources of support and meaning", ("relationships",)),
                ("inner peace grows from a generous and settled home base", ("inner", "challenges")),
            ],
            "constructive": ["creating a welcoming home that nourishes others"],
            "challenging": ["domestic comfort can soften necessary discipline"],
            "guidance": ["let home restore you, not shelter you"],
        },
        5: {
            "themes": [
                ("you teach, create and encourage with warmth and confidence", ("personality", "career")),
                ("romance and children bring growth and generous affection", ("relationships",)),
                ("creative expression and learning become sources of inner expansion", ("inner", "challenges")),
            ],
            "constructive": ["fertile creativity and natural mentorship"],
            "challenging": ["extravagance or over-optimism in pleasures"],
            "guidance": ["keep your creative promises to yourself"],
        },
        6: {
            "themes": [
                ("you work steadily and often help others carry their load", ("career", "personality")),
                ("colleagues and clients appreciate your fair-minded support", ("relationships",)),
                ("difficulties are met with perspective and patience", ("inner", "challenges")),
            ],
            "constructive": ["dedication to service and calm, experienced problem-solving"],
            "challenging": ["taking on too much in the name of being helpful"],
            "guidance": ["help where it is wanted, not only where it is needed"],
        },
        7: {
            "themes": [
                ("you approach partnership with generosity and high expectations", ("personality", "relationships")),
                ("marriage and close alliances are important spheres of growth", ("relationships",)),
                ("you learn about yourself through committed relationship", ("inner", "challenges")),
            ],
            "constructive": ["fairness, warmth and growth through partnership"],
            "challenging": ["expecting more of a partner than any person can carry"],
            "guidance": ["let partnership be equal, not idealised"],
        },
        8: {
            "themes": [
                ("you seek deeper understanding of change, risk and shared resources", ("personality", "career")),
                ("trust and intimacy are treated as serious, meaningful subjects", ("relationships",)),
                ("perspective helps you move through upheaval", ("inner", "challenges")),
            ],
            "constructive": ["wisdom about risk and generosity in shared matters"],
            "challenging": ["overconfidence when facing the unknown"],
            "guidance": ["respect the limits of what you can control"],
        },
        9: {
            "themes": [
                ("beliefs, learning and meaning guide your direction strongly", ("personality", "career")),
                ("teachers, mentors and journeys play an important role in your life", ("relationships",)),
                ("faith grows through study and experience and shapes your resilience", ("inner", "challenges")),
            ],
            "constructive": ["a guiding philosophy and genuine talent for teaching"],
            "challenging": ["certainty that stops listening to new experience"],
            "guidance": ["keep learning even where you already feel expert"],
        },
        10: {
            "themes": [
                ("you are entrusted with responsibility and expected to guide others", ("career", "personality")),
                ("professional relationships rest on integrity and fair advice", ("relationships",)),
                ("your reputation grows through knowledge and reliability", ("inner", "challenges")),
            ],
            "constructive": ["respected professional judgment and leadership through knowledge"],
            "challenging": ["taking on responsibility for outcomes beyond your control"],
            "guidance": ["let your word remain reliable under pressure"],
        },
        11: {
            "themes": [
                ("you gain through networks, communities and long-term goodwill", ("career", "personality")),
                ("friendships and shared aims bring prosperity and support", ("relationships",)),
                ("your hopes tend to be large and generously shared", ("inner", "challenges")),
            ],
            "constructive": ["capacity to build wide, supportive networks"],
            "challenging": ["promising more than can be delivered"],
            "guidance": ["invest in people, not only in opportunities"],
        },
        12: {
            "themes": [
                ("you find meaning in solitude, study and inner reflection", ("inner", "personality")),
                ("quiet and distance suit your relationships better than constant activity", ("relationships",)),
                ("perspective and forgiveness help you release difficulties", ("challenges")),
            ],
            "constructive": ["compassion, depth and philosophical acceptance"],
            "challenging": ["avoiding practical tasks in favour of reflection"],
            "guidance": ["let reflection return you to life, not away from it"],
        },
    },
    "Venus": {
        1: {
            "themes": [
                ("you come across with warmth, grace and an instinct for pleasing", ("personality", "relationships")),
                ("your personal manner strongly influences how relationships develop", ("relationships",)),
                ("harmony is a real need, and conflict costs you energy", ("inner", "challenges")),
            ],
            "constructive": ["charm, diplomacy and a calming presence"],
            "challenging": ["keeping peace at the cost of your own position"],
            "guidance": ["be kind without disappearing"],
        },
        2: {
            "themes": [
                ("you value comfort, beauty and stability in resources", ("personality", "career")),
                ("family harmony and pleasant speech matter to you a great deal", ("relationships",)),
                ("material and relational wellbeing are closely linked for you", ("inner", "challenges")),
            ],
            "constructive": ["talent for making resources go toward comfort and enjoyment"],
            "challenging": ["indulgence when comfort becomes the goal itself"],
            "guidance": ["value what sustains you, not only what is pleasant"],
        },
        3: {
            "themes": [
                ("you communicate with grace and prefer agreement to friction", ("personality", "relationships")),
                ("siblings and peers experience you as pleasant and cooperative", ("relationships",)),
                ("art, music and language are comfortable forms of expression", ("inner", "challenges")),
            ],
            "constructive": ["tactful communication and artistic sensitivity"],
            "challenging": ["avoiding difficult conversations to preserve calm"],
            "guidance": ["say the necessary thing kindly but say it"],
        },
        4: {
            "themes": [
                ("you want a comfortable, harmonious home above all", ("personality", "relationships")),
                ("family life and domestic beauty matter deeply to you", ("relationships",)),
                ("emotional balance depends on the atmosphere at home", ("inner", "challenges")),
            ],
            "constructive": ["making home a genuinely pleasant place for others"],
            "challenging": ["discomfort avoiding necessary domestic realities"],
            "guidance": ["let home be honest as well as beautiful"],
        },
        5: {
            "themes": [
                ("you enjoy romance, pleasure and creative expression openly", ("personality", "relationships")),
                ("romance is a central and happy area of your life", ("relationships",)),
                ("creative and affectionate expression restores your inner balance", ("inner", "challenges")),
            ],
            "constructive": ["warmth, artistry and enjoyment of life"],
            "challenging": ["chasing pleasure when deeper satisfaction is missing"],
            "guidance": ["put feeling into what you make, not only into what you enjoy"],
        },
        6: {
            "themes": [
                ("you work well where atmosphere and relationships are decent", ("career", "personality")),
                ("cooperation at work matters more to you than competition", ("relationships",)),
                ("discord and disorder affect your wellbeing noticeably", ("inner", "challenges")),
            ],
            "constructive": ["harmonious teamwork and care for working relationships"],
            "challenging": ["overindulgence or avoidance when routines get trying"],
            "guidance": ["make peace with routine; it supports your balance"],
        },
        7: {
            "themes": [
                ("you relate through affection, fairness and shared pleasure", ("personality", "relationships")),
                ("marriage and partnership are central to your happiness", ("relationships",)),
                ("you seek harmony and may soften disagreements quickly", ("inner", "challenges")),
            ],
            "constructive": ["deep capacity for partnership and loyal affection"],
            "challenging": ["losing your own opinion inside a relationship"],
            "guidance": ["bring your whole self into partnership"],
        },
        8: {
            "themes": [
                ("you are drawn to depth, intensity and meaningful sharing", ("personality", "relationships")),
                ("intimacy and trust are taken seriously and sought sincerely", ("relationships",)),
                ("strong feelings can arise around dependence and resources", ("inner", "challenges")),
            ],
            "constructive": ["capacity for profound closeness and loyalty"],
            "challenging": ["intensity that unsettles balance when trust is uncertain"],
            "guidance": ["let trust grow rather than demanding reassurance"],
        },
        9: {
            "themes": [
                ("you value refined beliefs, beauty and higher culture", ("personality", "career")),
                ("teachers, travel and philosophy bring you genuine pleasure", ("relationships",)),
                ("your faith is gentle and inclusive rather than rigid", ("inner", "challenges")),
            ],
            "constructive": ["appreciation for learning, art and other cultures"],
            "challenging": ["avoiding hard truths in favour of pleasant ones"],
            "guidance": ["let your philosophy include what is uncomfortable"],
        },
        10: {
            "themes": [
                ("you do well in work involving people, beauty and relationship", ("career", "personality")),
                ("professional reputation depends on how fairly you deal with others", ("relationships",)),
                ("recognition matters to you and is best earned through cooperation", ("inner", "challenges")),
            ],
            "constructive": ["diplomatic professionalism and attractive presentation"],
            "challenging": ["needing to be liked professionally"],
            "guidance": ["let quality, not popularity, be your measure"],
        },
        11: {
            "themes": [
                ("you gain through relationships, goodwill and shared pleasures", ("career", "relationships")),
                ("friendships are warm, aesthetic and long-lasting", ("relationships",)),
                ("your hopes centre on comfort, company and harmony", ("inner", "challenges")),
            ],
            "constructive": ["talent for building pleasant, productive alliances"],
            "challenging": ["overvaluing social comfort over honest aims"],
            "guidance": ["choose friends who bring out your better judgment"],
        },
        12: {
            "themes": [
                ("you appreciate quiet beauty and private affection", ("inner", "relationships")),
                ("solitude does not trouble you and restores your balance", ("relationships",)),
                ("feelings are often kept private until they settle", ("challenges")),
            ],
            "constructive": ["compassionate acceptance and quiet, steady warmth"],
            "challenging": ["withdrawing instead of saying what is needed"],
            "guidance": ["let privacy be a resource, not a hiding place"],
        },
    },
    "Saturn": {
        1: {
            "themes": [
                ("you take yourself seriously and build identity slowly but solidly", ("personality", "career")),
                ("you are seen as dependable, reserved or older than your years", ("relationships",)),
                ("self-confidence is earned through experience rather than given", ("inner", "challenges")),
            ],
            "constructive": ["endurance, realism and quiet self-reliance"],
            "challenging": ["harsh self-judgment that slows natural growth"],
            "guidance": ["give yourself the patience you give everyone else"],
        },
        2: {
            "themes": [
                ("you manage resources carefully and plan for the long term", ("career", "personality")),
                ("family duty and measured speech define much of your exchange", ("relationships",)),
                ("security is built by discipline rather than by opportunity", ("inner", "challenges")),
            ],
            "constructive": ["prudent stewardship and reliability with resources"],
            "challenging": ["scarcity thinking even when means are adequate"],
            "guidance": ["allow yourself to enjoy what you have built"],
        },
        3: {
            "themes": [
                ("you communicate carefully and value effort over talk", ("personality", "career")),
                ("relationships with siblings and peers carry responsibility", ("relationships",)),
                ("persistence rather than quickness is your mental strength", ("inner", "challenges")),
            ],
            "constructive": ["thorough learning and dependable communication"],
            "challenging": ["hesitancy or over-caution when speaking"],
            "guidance": ["say it plainly; your care already protects the rest"],
        },
        4: {
            "themes": [
                ("you take responsibility for home and family early on", ("personality", "relationships")),
                ("emotional foundations are serious and built through duty", ("relationships",)),
                ("inner security comes from structure and steady routine", ("inner", "challenges")),
            ],
            "constructive": ["loyal care for family and a stable, dutiful presence"],
            "challenging": ["emotional restraint that feels like distance to others"],
            "guidance": ["let those close to you see the feeling, not only the duty"],
        },
        5: {
            "themes": [
                ("you approach creativity and learning with discipline and patience", ("personality", "career")),
                ("children and romance bring responsibility along with affection", ("relationships",)),
                ("pleasure is enjoyed more when it feels earned", ("inner", "challenges")),
            ],
            "constructive": ["serious craft and sustained creative commitment"],
            "challenging": ["self-criticism that blocks playful expression"],
            "guidance": ["allow yourself to create without judging the result"],
        },
        6: {
            "themes": [
                ("you are strong in service, method and sustained effort", ("career", "personality")),
                ("you accept duty toward colleagues and those who depend on you", ("relationships",)),
                ("obstacles are outlasted rather than overcome in a rush", ("inner", "challenges")),
            ],
            "constructive": ["exceptional stamina and discipline in difficulty"],
            "challenging": ["overwork and worry affecting health and mood"],
            "guidance": ["rest is part of the discipline, not a failure of it"],
        },
        7: {
            "themes": [
                ("you treat partnership as a serious commitment with clear duties", ("personality", "relationships")),
                ("marriage asks for patience and maturity from you", ("relationships",)),
                ("you grow through learning to share control and trust", ("inner", "challenges")),
            ],
            "constructive": ["loyalty, reliability and long-lasting commitment"],
            "challenging": ["caution or control crowding out warmth"],
            "guidance": ["let trust be given gradually but genuinely"],
        },
        8: {
            "themes": [
                ("you meet crisis with endurance and a realistic mind", ("personality", "challenges")),
                ("trust, shared resources and change bring serious lessons", ("relationships",)),
                ("you are capable of deep, slow transformation", ("inner", "challenges")),
            ],
            "constructive": ["resilience through upheaval and steady handling of risk"],
            "challenging": ["fear or control tightening around uncertainty"],
            "guidance": ["let change take time rather than forcing certainty"],
        },
        9: {
            "themes": [
                ("you test beliefs carefully and value principles that hold up", ("personality", "career")),
                ("teachers and traditions are respected but questioned", ("relationships",)),
                ("your worldview forms slowly through experience and reflection", ("inner", "challenges")),
            ],
            "constructive": ["considered wisdom and integrity in belief"],
            "challenging": ["scepticism that delays genuine faith"],
            "guidance": ["let experience refine your principles without hardening them"],
        },
        10: {
            "themes": [
                ("you build a career through sustained effort and responsibility", ("career", "personality")),
                ("authority is earned slowly and carried seriously", ("relationships",)),
                ("professional recognition usually comes later and lasts longer", ("inner", "challenges")),
            ],
            "constructive": ["reliable authority and respect earned over time"],
            "challenging": ["discouragement when advancement is slow"],
            "guidance": ["keep the long view; your work compounds"],
        },
        11: {
            "themes": [
                ("you gain through persistence, patience and a few lasting alliances", ("career", "relationships")),
                ("you prefer a small circle of dependable friends", ("relationships",)),
                ("ambitions are realistic and pursued over years", ("inner", "challenges")),
            ],
            "constructive": ["steady, dependable gains and deep friendships"],
            "challenging": ["impatience when rewards lag behind effort"],
            "guidance": ["value the few and invest in them"],
        },
        12: {
            "themes": [
                ("you need solitude and are comfortable with discipline in private", ("inner", "personality")),
                ("you give quietly to others without needing it noticed", ("relationships",)),
                ("release and acceptance arrive through patient reflection", ("challenges")),
            ],
            "constructive": ["inner discipline, compassion and quiet service"],
            "challenging": ["isolation or unspoken heaviness when burdens stay private"],
            "guidance": ["share the weight occasionally rather than carrying it all quietly"],
        },
    },
    "Rahu": {
        1: {
            "themes": [
                ("you present yourself unconventionally and are restless about identity", ("personality", "career")),
                ("you attract attention and unusual connections without trying", ("relationships",)),
                ("you are driven to define yourself beyond family expectations", ("inner", "challenges")),
            ],
            "constructive": ["magnetic presence and appetite for reinvention"],
            "challenging": ["restlessness that scatters identity and direction"],
            "guidance": ["aim the ambition at something genuinely yours"],
        },
        2: {
            "themes": [
                ("you have an intense drive for resources and unusual ways of gaining", ("career", "personality")),
                ("family background and values are places of ambition or departure", ("relationships",)),
                ("appetite for more can overshadow what is already sufficient", ("inner", "challenges")),
            ],
            "constructive": ["ambition that can build substantial means"],
            "challenging": ["insatiability that keeps satisfaction out of reach"],
            "guidance": ["decide in advance what enough looks like"],
        },
        3: {
            "themes": [
                ("you communicate boldly and take unconventional paths of effort", ("personality", "career")),
                ("competition with peers or siblings fuels your drive", ("relationships",)),
                ("your mind seeks novelty and dislikes routine", ("inner", "challenges")),
            ],
            "constructive": ["inventive skill and fearlessness in self-expression"],
            "challenging": ["impatience and scattered effort"],
            "guidance": ["give your originality a structure to work within"],
        },
        4: {
            "themes": [
                ("your sense of home and belonging takes an unusual route", ("personality", "relationships")),
                ("family circumstances may feel unsettled or unconventional", ("relationships",)),
                ("you seek inner security by redefining what home means", ("inner", "challenges")),
            ],
            "constructive": ["capacity to build a home on your own terms"],
            "challenging": ["restlessness that makes it hard to settle"],
            "guidance": ["create roots deliberately rather than waiting to feel rooted"],
        },
        5: {
            "themes": [
                ("you are drawn to intense interests and unconventional creativity", ("personality", "career")),
                ("romance can be magnetic, sudden and occasionally complicated", ("relationships",)),
                ("you take creative risks that others avoid", ("inner", "challenges")),
            ],
            "constructive": ["original talent and willingness to experiment"],
            "challenging": ["craving intensity so much that steady pleasures pale"],
            "guidance": ["let intensity serve the work, not the other way around"],
        },
        6: {
            "themes": [
                ("you fight obstacles with unusual persistence and cleverness", ("career", "challenges")),
                ("workplace politics and competition are familiar territory", ("relationships",)),
                ("you are driven to overcome whatever restricts you", ("inner", "challenges")),
            ],
            "constructive": ["formidable drive to overcome disadvantage"],
            "challenging": ["overextension and escalating conflict"],
            "guidance": ["choose the battles that actually change your conditions"],
        },
        7: {
            "themes": [
                ("you are drawn to partners who are unusual, strong or foreign to your world", ("personality", "relationships")),
                ("partnership brings intense lessons about power and desire", ("relationships",)),
                ("you are learning to relate without being consumed by the other", ("inner", "challenges")),
            ],
            "constructive": ["wide horizons in relationship and genuine openness to difference"],
            "challenging": ["repeating intense or imbalanced attachments"],
            "guidance": ["choose partnership for the person rather than the intensity"],
        },
        8: {
            "themes": [
                ("you are drawn to secrets, research and hidden mechanisms", ("personality", "career")),
                ("trust and shared resources are areas of complexity", ("relationships",)),
                ("your inner life is intense and private by nature", ("inner", "challenges")),
            ],
            "constructive": ["depth of inquiry and aptitude for sensitive work"],
            "challenging": ["anxiety around control and dependence"],
            "guidance": ["bring hidden worries into the open before they grow"],
        },
        9: {
            "themes": [
                ("you are attracted to unconventional philosophies and foreign influences", ("personality", "career")),
                ("teachers or travels open doors that surprise your family", ("relationships",)),
                ("beliefs are built from experience rather than tradition", ("inner", "challenges")),
            ],
            "constructive": ["broad, adventurous perspective and courage in exploration"],
            "challenging": ["certainty in ideas that change again later"],
            "guidance": ["hold your conclusions loosely while you are still exploring"],
        },
        10: {
            "themes": [
                ("you have strong worldly ambition and unconventional professional paths", ("career", "personality")),
                ("professional relationships may involve foreign or unusual circles", ("relationships",)),
                ("the drive for status is powerful and best aimed deliberately", ("inner", "challenges")),
            ],
            "constructive": ["ambition that reaches beyond conventional ceilings"],
            "challenging": ["pursuing recognition for its own sake"],
            "guidance": ["choose work you respect, not merely work that shines"],
        },
        11: {
            "themes": [
                ("you pursue large gains and unusually wide networks", ("career", "personality")),
                ("friendships bring opportunity, ambition and occasional turbulence", ("relationships",)),
                ("your hopes are expansive and can outrun your patience", ("inner", "challenges")),
            ],
            "constructive": ["reach across groups and access to wide opportunity"],
            "challenging": ["scattered effort chasing too many possibilities"],
            "guidance": ["choose a few ambitions and honour them"],
        },
        12: {
            "themes": [
                ("your imagination is strong and draws you toward hidden or distant matters", ("inner", "personality")),
                ("you need solitude and may be drawn to foreign places", ("relationships",)),
                ("releasing control is a recurring inner challenge", ("challenges")),
            ],
            "constructive": ["imagination, compassion and comfort with the unknown"],
            "challenging": ["escapism or unclear boundaries when pressure builds"],
            "guidance": ["give imagination a direction so it does not become an escape"],
        },
    },
    "Ketu": {
        1: {
            "themes": [
                ("you are not very concerned with how you appear to others", ("personality", "inner")),
                ("you can seem distant or gently detached in relationships", ("relationships",)),
                ("identity is built inward rather than through visibility", ("challenges")),
            ],
            "constructive": ["quiet self-containment and freedom from image"],
            "challenging": ["uncertain sense of self when asked to assert it"],
            "guidance": ["let others see some of what you keep private"],
        },
        2: {
            "themes": [
                ("you are detached from accumulating and care little for display", ("inner", "personality")),
                ("family and speech may feel like areas to move beyond", ("relationships",)),
                ("values are unconventional and simplifying resources has appeal", ("challenges")),
            ],
            "constructive": ["freedom from greed and clarity about real needs"],
            "challenging": ["neglecting practical provision because it matters little to you"],
            "guidance": ["let maintenance be simple, not neglected"],
        },
        3: {
            "themes": [
                ("your communication is intuitive and economical", ("inner", "personality")),
                ("you may feel detached from competitive conversation with peers", ("relationships",)),
                ("effort is applied selectively rather than energetically", ("challenges")),
            ],
            "constructive": ["insightful, unfussy communication and focused skill"],
            "challenging": ["withdrawing effort from areas that need persistence"],
            "guidance": ["keep going after interest fades"],
        },
        4: {
            "themes": [
                ("your sense of home is inward and less tied to place", ("inner", "personality")),
                ("you may feel like an observer within your own family", ("relationships",)),
                ("inner security comes from release rather than accumulation", ("challenges")),
            ],
            "constructive": ["inner stability independent of circumstances"],
            "challenging": ["rootlessness or distance from family warmth"],
            "guidance": ["build belonging deliberately, even without needing it"],
        },
        5: {
            "themes": [
                ("creativity and learning follow intuitive lines rather than formal ones", ("inner", "career")),
                ("romance may be approached with detachment or restraint", ("relationships",)),
                ("you can find insight where others see nothing remarkable", ("challenges")),
            ],
            "constructive": ["intuitive originality and a subtle, discerning intelligence"],
            "challenging": ["difficulty sustaining enthusiasm for consistent effort"],
            "guidance": ["finish the things your intuition starts"],
        },
        6: {
            "themes": [
                ("service and routines are handled without fuss or pride", ("career", "inner")),
                ("you take a philosophical view of conflicts and competition", ("relationships",)),
                ("obstacles are weathered by stepping back from them", ("challenges")),
            ],
            "constructive": ["unobtrusive discipline and resilience in difficulty"],
            "challenging": ["avoiding confrontation that would actually resolve matters"],
            "guidance": ["address the practical problem before taking the higher view"],
        },
        7: {
            "themes": [
                ("you are not seeking to be defined by partnership", ("personality", "inner")),
                ("relationships carry a sense of destiny or unusual distance", ("relationships",)),
                ("you learn about yourself through detachment from others' expectations", ("challenges")),
            ],
            "constructive": ["clear-sighted, unpossessive attitude toward relationship"],
            "challenging": ["distance or disengagement when closeness is required"],
            "guidance": ["stay present in relationships rather than mentally leaving"],
        },
        8: {
            "themes": [
                ("you have inherent comfort with the hidden and the profound", ("inner", "personality")),
                ("shared resources and intimacy may carry a sense of release", ("relationships",)),
                ("change is met with insight more than resistance", ("challenges")),
            ],
            "constructive": ["deep insight into change and human complexity"],
            "challenging": ["withdrawing into the hidden when life asks for participation"],
            "guidance": ["share what you understand; it helps others"],
        },
        9: {
            "themes": [
                ("beliefs are personal and arrived at intuitively", ("inner", "personality")),
                ("you may hold teachers and traditions at a certain distance", ("relationships",)),
                ("meaning is sought inwardly rather than through formal authority", ("challenges")),
            ],
            "constructive": ["independent, inward faith and genuine openness"],
            "challenging": ["disengaging from useful learning because of its packaging"],
            "guidance": ["take what is useful from tradition without accepting it wholesale"],
        },
        10: {
            "themes": [
                ("you are less motivated by status than by the meaning of the work", ("inner", "career")),
                ("professionally you may move between roles without attachment", ("relationships",)),
                ("you would rather work with purpose than with ambition", ("challenges")),
            ],
            "constructive": ["integrity, skill and freedom from career vanity"],
            "challenging": ["drifting professionally when purpose is unclear"],
            "guidance": ["choose work by what it develops in you"],
        },
        11: {
            "themes": [
                ("you have a small, meaningful circle rather than a large network", ("inner", "relationships")),
                ("gains matter less to you than shared purpose", ("relationships",)),
                ("you may let go of ambitions once they are achieved", ("challenges")),
            ],
            "constructive": ["sincere friendships and detachment from status"],
            "challenging": ["withdrawing from groups that could genuinely support you"],
            "guidance": ["stay connected even when solitude feels easier"],
        },
        12: {
            "themes": [
                ("you are naturally drawn to inner life, solitude and release", ("inner", "personality")),
                ("comfort with the unseen shapes how you relate to the world", ("relationships",)),
                ("your insight deepens when you allow quiet and reflection", ("challenges")),
            ],
            "constructive": ["rare capacity for contemplation and letting go"],
            "challenging": ["losing contact with practical affairs"],
            "guidance": ["keep one foot in the everyday while the other explores"],
        },
    },
}
