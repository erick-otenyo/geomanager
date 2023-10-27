import json
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
    ("yyyy-MM", _("Month number - (E.g 2023-01)")),
    ("MMMM yyyy", _("Month name - (E.g January 2023)")),
    ("pentadal", _("Pentadal - (E.g Jan 2023 - P1 1-5th)"))
)
