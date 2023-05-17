from django.db import models


class ListField(models.CharField):
    description = "List field"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return value.split(',')

    def to_python(self, value):
        if isinstance(value, list):
            return value
        if value is None:
            return value
        return value.split(',')

    def get_prep_value(self, value):
        if isinstance(value, list):
            return ','.join([str(i) for i in value])
        return value

    def value_to_string(self, obj):
        value = self.value_from_object(obj)
        return self.get_prep_value(value)
