# KAVACH interpretation sources

## Layers

| Layer | source_type | What it covers |
| --- | --- | --- |
| Standard Jyotish foundations | `standard_jyotish` | Bhava meanings, Graha significations, Graha-in-Bhava readings, sign rulership, exaltation/debilitation, channel domains |
| KAVACH astrologer rules | `kavach_custom` (source `kavach_astrologer_rule`, status `approved`) | Five Panchang channel meanings, Panchang limb -> lord mappings, Daily Moon 6/8/12 rule, question classification, synthesis rules |

KAVACH custom methodology is **not** presented as classical text.

## Source categories researched

- **Brihat Parashara Hora Shastra / Bhava framework** ? the twelve Bhava
  significations used in `jyotish/houses.py` and the structure of the
  Graha-in-Bhava readings.
- **Standard Graha-in-Bhava interpretation** (Phaladeepika / Saravali tradition
  and widely used modern Jyotish references) ? the 108 placement readings in
  `kavach_core/knowledge/graha_bhava.py`, paraphrased from common principles as
  original semantic notes. No source prose is copied.
- **Standard dignity / rulership framework** ? sign ownership, exaltation and
  debilitation for the seven classical Grahas (`jyotish/planets.py`).
- **Standard Prashna moment-chart methodology** ? question Bhava routing,
  Lagna, Lagna lord, Moon, question house and occupants. This is the
  supplementary layer only.

## Known disagreements (recorded, not resolved by inventing rules)

- **Rahu/Ketu dignity**: traditions differ on exaltation, debilitation and sign
  ownership, so the engine assigns none (`not_assigned`). Their Graha-in-Bhava
  readings are still used.
- **Karana and Yoga lords**: the astrologer's approved tables are used as given.
  Yoga lord resolution is name-based against the classic 27-Yoga order.
- **Past-life language**: presented as part of the astrologer's tradition, never
  as established fact.
- **House 8**: transformation, vulnerability and sudden change only. Never
  death or lifespan.

## Excluded by design

No numerical scoring, no Shadbala, no friend/enemy tables, no combustion,
aspect or retrograde strength rules, no lifespan, death or medical
conclusions, no guaranteed events, no invented Rahu/Ketu dignity.
