# Question Engine — Sources

## Base layer: STANDARD PRASHNA

The base engine was constructed from **common / standard Prashna and Jyotish
principles**, paraphrased — not copied. Typical reference material:

- Prashna Marga — traditional text on horary astrology (house significations,
  Lagna/Moon emphasis).
- Brihat Parashara Hora Shastra — general Bhava (house) significations.
- Common Prashna practice notes: the Lagna describes the querent and the general
  standing of the question; the Moon describes the mental/emotional climate; the
  Bhava relevant to the subject describes the matter asked about.

Rules derived from this layer are tagged `source_type: standard_prashna`.

## KAVACH custom layer

The astrologer's own rules are stored separately and are **never** labelled as
classical Jyotish. Rules from this layer are tagged:

```
source_type: kavach_custom
source: kavach_astrologer_rule
status: approved
```

Currently implemented custom rule: `KC_DAILY_MOON_001` (question-moment Moon
Nakshatra lord in house 6 / 8 / 12 → extra-care indication; otherwise supportive).

## Deliberately not implemented

No Shadbala, no numeric scores, no friendship tables, no combustion/aspect/
retrograde strength rules, no yogas. No medical, legal, financial-certainty or
safety outcomes. Lifespan/death questions are refused.


## Shared five-channel interpretation layer (`backend/jyotish/`)

KAVACH selects a planet through five Panchang channels (Vaar, Tithi, Karana,
Nakshatra, Yoga) and then reads that planet in the relevant D1 chart.

- **Selected planet + house + Rashi + dignity + channel domain -> interpretation.**
  The selected Panchang planet is NOT treated as a house lord unless it actually
  owns the relevant Rashi.
- Source categories used for this layer: the Bhava framework and general
  Graha-in-Bhava interpretation (Brihat Parashara Hora Shastra tradition),
  standard sign rulership, standard exaltation/debilitation, and standard
  Prashna moment-chart methodology. Semantic tables are paraphrased; no source
  prose is copied.
- `standard_jyotish` tables: house meanings, condition groups, planet
  significations, rulership, exaltation/debilitation, channel domains.
- `kavach_custom` tables (astrologer's approved rules, unchanged): the five
  Panchang lord mappings in `prediction/panchang_natal/mappings.py`, which now
  drive BOTH System A (birth moment) and System B (question moment) through
  `jyotish/lords.py`.
- Rahu and Ketu receive no sign ownership and no exaltation/debilitation
  scheme, because traditions differ. No friend/enemy scoring and no numerical
  scoring are implemented.
- The five channels are independent: the same planet in the same house produces
  a different reading per channel (Vaar = personality/vitality,
  Tithi = relationships/prosperity, Karana = career/decisions,
  Nakshatra = inner patterns, Yoga = challenges/support).
- House 8 is never read as death. Lifespan, death and medical conclusions are
  excluded everywhere.
