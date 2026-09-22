"""Number reduction for KAVACH YES / NO.

The HOUR and the MINUTE are reduced SEPARATELY. They are never added together.
Repeated digit sum is applied until a single number 1-9 remains.

    15 -> 1 + 5 -> 6
    53 -> 5 + 3 -> 8
    59 -> 5 + 9 -> 14 -> 1 + 4 -> 5
    10 -> 1 + 0 -> 1
    20 -> 2 + 0 -> 2
    05 -> 0 + 5 -> 5

Zero handling
-------------
Digit-summing is a mod-9 process: values repeat in a 1-9 cycle, so the residue
that would be 0 belongs at 9. "00" is therefore carried to 9 rather than
returning 0, because 0 has no planet in the approved mapping and an accidental
0 would be silently wrong.

OWNER-APPROVED: `00 -> 9` is approved for this feature. It lives in the single
constant below so the rule is explicit and changeable in one place, not hidden
in the reduction loop.
"""

from __future__ import annotations

# Owner-approved zero-handling rule: 0 is not a planet number in the approved
# mapping, so a zero reduction is carried to 9 (the wrap of the 1-9 cycle).
ZERO_HANDLING = 9

SINGLE_DIGITS = (1, 2, 3, 4, 5, 6, 7, 8, 9)


def reduce_to_single_digit(value: int) -> int:
    """Repeated digit sum of a non-negative integer, forced into 1-9.

    Accepts the hour (0-23) or the minute (0-59) value. The hour and the minute
    must always be reduced with separate calls; the two results are never summed.
    """
    number = abs(int(value))
    while number > 9:
        number = sum(int(digit) for digit in str(number))
    if number == 0:
        return ZERO_HANDLING
    return number


def hour_number(hour: int) -> int:
    """Planetary number for the hour (1-9)."""
    return reduce_to_single_digit(hour)


def minute_number(minute: int) -> int:
    """Planetary number for the minute (1-9), reduced independently."""
    return reduce_to_single_digit(minute)
