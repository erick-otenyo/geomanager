import json
import math
from uuid import UUID

from django.utils.translation import gettext_lazy as _


class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            # if the obj is uuid, we simply return the value of uuid
            return str(obj)
        return json.JSONEncoder.default(self, obj)


DATE_FORMAT_CHOICES = (
    ("yyyy-MM-dd HH:mm", _("Hour minute:second - (E.g 2023-01-01 00:00)")),
    ("yyyy-MM-dd", _("Day - (E.g 2023-01-01)")),
    ("pentadal", _("Pentadal - (E.g Jan 2023 - P1 1-5th)")),
    ("dekadal", _("Dekadal - (E.g Jan 2023 - D1 1-10th)")),
    ("yyyy-MM", _("Month number - (E.g 2023-01)")),
    ("MMMM yyyy", _("Month name - (E.g January 2023)")),
    ("yyyy", _("Year - (E.g 2023)")),
)


def significant_digits(step, number):
    """
    This function calculates the number of significant digits to keep after the decimal
    point based on a given step value.

    Args:
        step: The minimum absolute difference between two values considered significant.
        number: The number to analyze.


    Returns:
        The number of significant digits to keep.
    """
    if number == 0:
        return 1  # Handle zero case

    # Convert the number to absolute value and handle negatives
    abs_number = abs(number)
    # Get the integer part (number of leading zeros not considered significant)
    exponent = int(math.floor(math.log10(abs_number)))

    # If the number is less than 1 (between 0 and 1), consider the leading zero
    if abs_number < 1:
        exponent -= 1

    # Calculate significant digits based on exponent and step
    sign_digits = max(0, exponent + 1)  # At least 1 significant digit
    if step > 0:
        sign_digits = max(sign_digits, int(math.ceil(math.log10(abs_number) / math.log10(step))))

    return sign_digits


def round_to_precision(precision=None):
    """
    This function creates and returns another function that rounds numbers to a specified precision.

    Args:
        precision: The desired number of decimal places for rounding (optional).

    Returns:
        A function that rounds numbers to the specified precision.
    """
    if precision is None:
        def inner(n):
            return n  # No rounding if precision is not specified

        return inner

    multiplier = 10 ** precision

    def inner(n):
        """
        Inner function that performs rounding based on the multiplier.
        """
        return round(n * multiplier) / multiplier

    return inner
