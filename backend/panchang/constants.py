"""Panchang name tables and traditional period rules.

All tables here are standard Panchang conventions (Lahiri / Chitrapaksha).
Nothing in this file depends on the KAVACH application.
"""

# --------------------------------------------------------------------------
# 30 Tithis (index 0 = Shukla Pratipada ... 29 = Krishna Amavasya)
# --------------------------------------------------------------------------
TITHI_NAMES = [
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima",
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Amavasya",
]

PAKSHA_NAMES = ["Shukla Paksha", "Krishna Paksha"]

# --------------------------------------------------------------------------
# 27 Nakshatras + lords (Vimshottari)
# --------------------------------------------------------------------------
NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
    "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada",
    "Revati",
]

NAKSHATRA_LORDS = [
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter",
    "Saturn", "Mercury",
] * 3  # 9 lords repeat three times across the 27 nakshatras

# --------------------------------------------------------------------------
# 27 Yogas
# --------------------------------------------------------------------------
YOGA_NAMES = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda",
    "Sukarma", "Dhriti", "Shula", "Ganda", "Vriddhi", "Dhruva", "Vyaghata",
    "Harshana", "Vajra", "Siddhi", "Vyatipata", "Variyana", "Parigha",
    "Shiva", "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma", "Indra",
    "Vaidhriti",
]

# --------------------------------------------------------------------------
# 11 Karanas
# --------------------------------------------------------------------------
KARANA_MOVABLE = [
    "Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti",
]
KARANA_FIXED_FIRST = "Kimstughna"
KARANA_FIXED_LAST = ["Shakuni", "Chatushpada", "Naga"]

# --------------------------------------------------------------------------
# Rashis
# --------------------------------------------------------------------------
RASHI_NAMES = [
    "Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya",
    "Tula", "Vrishchika", "Dhanu", "Makara", "Kumbha", "Meena",
]

RASHI_ENGLISH = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

# --------------------------------------------------------------------------
# Vara (weekday, Monday = 0 to match datetime.weekday())
# --------------------------------------------------------------------------
VARA_NAMES = [
    "Somavara", "Mangalavara", "Budhavara", "Guruvara",
    "Shukravara", "Shanivara", "Raviwara",
]
VARA_ENGLISH = [
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
]

# --------------------------------------------------------------------------
# Rahu Kalam / Yamaganda / Gulika Kalam
# Day (sunrise -> sunset) is split into 8 equal parts.
# Values are 1-indexed part numbers for each weekday (Mon=0 ... Sun=6).
# --------------------------------------------------------------------------
RAHU_KALAM_PART = {0: 2, 1: 7, 2: 5, 3: 6, 4: 4, 5: 3, 6: 8}
YAMAGANDA_PART = {0: 4, 1: 3, 2: 2, 3: 1, 4: 7, 5: 6, 6: 5}
GULIKA_PART = {0: 6, 1: 5, 2: 4, 3: 3, 4: 2, 5: 1, 6: 7}

# --------------------------------------------------------------------------
# Dur Muhurta — which day-muhurta (1..15, day split into 15 parts) is inauspicious.
# Verified against Drik Panchang for Sunday (=14). Other weekdays follow the
# classical Muhurta Chintamani table and still need reference validation.
# --------------------------------------------------------------------------
DUR_MUHURTA_PART = {6: 14, 0: 10, 1: 8, 2: 6, 3: 12, 4: 4, 5: 2}

# --------------------------------------------------------------------------
# Choghadiya
# The seven names cycle; the day starts at a weekday-specific position.
# --------------------------------------------------------------------------
CHOGHADIYA_CYCLE = ["Char", "Labh", "Amrit", "Kaal", "Shubh", "Rog", "Udveg"]

# index into CHOGHADIYA_CYCLE for the first day segment (Mon=0 ... Sun=6)
CHOGHADIYA_DAY_START = {0: 2, 1: 5, 2: 1, 3: 4, 4: 0, 5: 3, 6: 6}

CHOGHADIYA_CLASS = {
    "Char": "good",
    "Labh": "good",
    "Amrit": "best",
    "Kaal": "bad",
    "Shubh": "good",
    "Rog": "bad",
    "Udveg": "bad",
}

# --------------------------------------------------------------------------
# Ritu and Ayana
# --------------------------------------------------------------------------
RITU_NAMES = [
    "Vasanta", "Grishma", "Varsha", "Sharad", "Hemanta", "Shishira",
]

# Disha Shool (direction to avoid travelling) by weekday
DISHA_SHOOL = {
    0: "East", 1: "North", 2: "North", 3: "South", 4: "West", 5: "East", 6: "West",
}

# Amanta lunar month names, indexed by the sidereal Sun rashi at the new moon
AMANTA_MONTHS = [
    "Chaitra", "Vaishakha", "Jyeshtha", "Ashadha", "Shravana", "Bhadrapada",
    "Ashwina", "Kartika", "Margashirsha", "Pausha", "Magha", "Phalguna",
]

# --------------------------------------------------------------------------
# Extended Ashubha Muhurta (day split into 15 muhurtas).
# Sunday values are verified against the 2026-09-20 New Delhi reference.
# The remaining weekdays use the classical tables and are flagged unverified.
# --------------------------------------------------------------------------
DUSHTA_PART = {6: 14, 0: 10, 1: 8, 2: 6, 3: 12, 4: 4, 5: 2}
KULIKA_PART = {6: 14, 0: 10, 1: 8, 2: 6, 3: 12, 4: 4, 5: 2}
KANTAKA_PART = {6: 6, 0: 5, 1: 4, 2: 3, 3: 2, 4: 1, 5: 7}
KALAVELA_PART = {6: 8, 0: 7, 1: 6, 2: 5, 3: 4, 4: 3, 5: 2}
YAMAGHANTA_PART = {6: 10, 0: 9, 1: 8, 2: 7, 3: 6, 4: 5, 5: 4}

# Which extended ashubha rules the Sunday reference case validated
VERIFIED_ASHUBHA_WEEKDAY = 6

# --------------------------------------------------------------------------
# Hora — planetary hours
# The hora sequence always follows this order, and the first hora at sunrise
# belongs to the weekday lord.
# --------------------------------------------------------------------------
HORA_SEQUENCE = ["Sun", "Venus", "Mercury", "Moon", "Saturn", "Jupiter", "Mars"]

WEEKDAY_LORD = {
    0: "Moon",     # Monday
    1: "Mars",     # Tuesday
    2: "Mercury",  # Wednesday
    3: "Jupiter",  # Thursday
    4: "Venus",    # Friday
    5: "Saturn",   # Saturday
    6: "Sun",      # Sunday
}

HORA_NATURE = {
    "Sun": "Authority, government, leadership, official matters",
    "Moon": "Emotions, public interaction, nurturing, fluid matters",
    "Mars": "Action, courage, competition, physical activity",
    "Mercury": "Communication, study, business, calculation",
    "Jupiter": "Learning, guidance, important counsel, expansion",
    "Venus": "Relationships, art, comfort, beauty",
    "Saturn": "Discipline, labour, persistence, long-term work",
}

# --------------------------------------------------------------------------
# Tarabalam — the 9 taras counted from the janma nakshatra
# --------------------------------------------------------------------------
TARA_NAMES = [
    "Janma", "Sampat", "Vipat", "Kshema", "Pratyari",
    "Sadhaka", "Vadha", "Mitra", "Ati-Mitra",
]
TARA_GOOD = {1, 3, 5, 7, 8}  # Sampat, Kshema, Sadhaka, Mitra, Ati-Mitra

# Chandrabalam — Moon in these houses from the janma rashi is favourable
CHANDRA_GOOD_HOUSES = {1, 3, 6, 7, 10, 11}

# --------------------------------------------------------------------------
# Grahas for the D1 chart
# --------------------------------------------------------------------------
CLASSICAL_GRAHAS = [
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
]
OUTER_GRAHAS = ["Uranus", "Neptune", "Pluto"]

PLANET_SYMBOLS = {
    "Sun": "Su", "Moon": "Mo", "Mars": "Ma", "Mercury": "Me", "Jupiter": "Ju",
    "Venus": "Ve", "Saturn": "Sa", "Rahu": "Ra", "Ketu": "Ke",
    "Uranus": "Ur", "Neptune": "Ne", "Pluto": "Pl", "Lagna": "Asc",
}

# --------------------------------------------------------------------------
# Drik Ritu (tropical-season convention) vs Vedic Ritu (sidereal solar month)
# --------------------------------------------------------------------------
DRIK_RITU_BY_SUN_RASHI = [
    "Vasanta", "Grishma", "Grishma", "Varsha", "Varsha", "Sharad",
    "Sharad", "Hemanta", "Hemanta", "Shishira", "Shishira", "Vasanta",
]
