"""Deterministic dispositor-chain engine (single implementation).

Powers Rahu/Ketu operational analysis and Mala-Shree connections.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .signs import RASHIS, SIGN_LORD, sign_index


def dispositor_of(rashi: str) -> Optional[str]:
    return SIGN_LORD.get(rashi)


def previous_rashi(rashi: str) -> str:
    return RASHIS[(sign_index(rashi) - 1) % 12]


def dispositor_chain(start_planet: str, placements: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Follow planet -> occupied sign -> sign lord -> that lord's sign ... until a planet repeats."""
    chain: List[str] = []
    seen: Dict[str, int] = {}
    current: Optional[str] = start_planet
    while current and current not in seen:
        seen[current] = len(chain)
        chain.append(current)
        placement = placements.get(current)
        if not placement:
            current = None
            break
        lord = dispositor_of(str(placement.get("rashi")))
        current = lord if lord and lord in placements else None

    cycle_start: Optional[str] = None
    cycle: List[str] = []
    if current and current in seen:
        cycle_start = current
        cycle = chain[seen[current]:]

    return {
        "startingPlanet": start_planet,
        "chain": chain,
        "chainArrow": " -> ".join(chain),
        "uniquePlanets": sorted(set(chain), key=chain.index),
        "count": len(set(chain)),
        "cycleStart": cycle_start,
        "cycle": cycle,
        "cycleArrow": " -> ".join(cycle + cycle[:1]) if cycle else "",
        "isCycle": bool(cycle and len(cycle) > 1),
        "terminated": current is None,
    }


def chains_for_all(placements: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {planet: dispositor_chain(planet, placements) for planet in placements}


def mala_shree(placements: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Owner methodology: every unique planet in the connected network.

    Larger connected networks = more extensive Mala-Shree connection. No score,
    no prediction.
    """
    results = [dispositor_chain(planet, placements) for planet in placements]
    return sorted(results, key=lambda item: item["count"], reverse=True)


def network_size(placements: Dict[str, Dict[str, Any]], start_planet: str) -> int:
    return int(dispositor_chain(start_planet, placements)["count"])
