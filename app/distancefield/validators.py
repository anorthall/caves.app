from django.core.exceptions import ValidationError


def valid_unit_type(value):
    from .fields import D, DistanceField  # prevent circular import

    if not value:
        return

    if isinstance(value, str):
        if value == "0":
            value = "0m"

        r, f = DistanceField.parse_string(value)
        if r is None or f is False:
            units = ", ".join([g for g in set(D.ALIAS.values()) if "_" not in g])

            raise ValidationError(f"Please choose a valid unit from {units}.")
