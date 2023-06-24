from django.forms import fields

from . import validators


class DistanceField(fields.CharField):
    default_validators = [validators.valid_unit_type]

    def __init__(self, *args, **kwargs):
        super(DistanceField, self).__init__(*args, **kwargs)
