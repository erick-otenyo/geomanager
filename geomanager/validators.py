import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

valid_directory_names_pattern = re.compile(r'^[a-zA-Z0-9_/-]+$')


def validate_directory_name(value):
    if value.startswith('/'):
        raise ValidationError(_("The directory name can not start with '/'. "), code='invalid', )
    if value.endswith('/'):
        raise ValidationError(_("The directory name can not end with '/'. "), code='invalid', )

    if not valid_directory_names_pattern.match(value):
        raise ValidationError(
            _("The directory name can only contain alphanumeric characters, underscores, and hyphens."),
            code='invalid', )

    return value
