"""KAVACH MARRIAGE COMPATIBILITY (V1) - isolated methodology package.

Built ONLY from the owner-supplied decks ("MARRIAGE COMAPABILITY.pptx" and
"MARRIAGE COMAPABILITY - class 2.pptx"). It deliberately does NOT reuse the
proprietary KAVACH BNN friendship registry: this methodology uses a separate
natural planetary friendship table, which lives here.

V1 factors (source-supported only):
    tara          Dina / Tara Kuta
    gana          Gana
    nadi          Nadi
    rashi         Rashi Kuta (directional, with mitigation)
    graha_maitri  Rashiadhipathi / Graha Maitri
    vasya         Vasya Kuta

Not implemented (missing or ambiguous source data): Yoni, and the deeper
Class-2 chart checks (7th/8th house, Ascendant, Dasha/Bhukti, Mercury-Mercury,
Mars-Mars, Kuja Dosha).

Results are qualitative. No 36-point total is produced, and no prohibited
output (death, lifespan, fertility, pregnancy, child health, hereditary or
medical claims) is ever generated.
"""

from .engine import FACTOR_ORDER, STATUSES, evaluate_compatibility, overall_summary
from .models import FactorResult, PersonFacts

__all__ = [
    "FACTOR_ORDER",
    "STATUSES",
    "evaluate_compatibility",
    "overall_summary",
    "FactorResult",
    "PersonFacts",
]
