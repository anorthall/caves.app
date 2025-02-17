"""A "compound" field that represents a distance measurement.

Stores the field internally using two (or, optionally, three) fields:

    a) Measurement value - a float field representing the actual value of
       the measurement. This is the data stored by the main field.
       Internally we convert to whatever is stored in the default_units
       kwarg.
    b) Measurement unit - a String field representing the default unit name,
       e.g. 'mi'. This is the units that were used to create the distance.
       If the field name is not supplied through the "unit_field_"
       kwarg, then it will be retrieved in the "default_unit" format.
"""

import logging
import re
from decimal import Decimal

from django.contrib.gis.measure import D as _D
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.db.models import fields, signals

from . import forms, validators

LOGGER = logging.getLogger(__name__)


class D(_D):
    MAX_DECIMAL_PRECISION = 6
    EXTRA_ALIASES: dict[str, str] = {}
    EXTRA_UNITS = {"px": 0.001}

    ADDITIONAL_ALIASES = {
        "in": "inch",
        '"': "inch",
        "'": "ft",
        "centimeter": "cm",
        "ru": "u",
    }
    UNITS = _D.UNITS
    UNITS.update({"u": 0.04445})
    ALIAS = _D.ALIAS
    ALIAS.update(ADDITIONAL_ALIASES)
    LALIAS = _D.LALIAS
    LALIAS.update(ADDITIONAL_ALIASES)

    UNITS.update(EXTRA_UNITS)
    ALIAS.update(EXTRA_ALIASES)

    def __init__(self, *args, **kwargs):
        prec = kwargs.pop("max_decimal_precision", None)
        self.prec = prec or self.MAX_DECIMAL_PRECISION

        if len(args) == 1:
            parsed = DistanceField.parse_string(args[0])
            if parsed and parsed[0]:
                self._default_unit = parsed[0]._default_unit or "m"
                self.standard = parsed[0].standard
        else:
            super().__init__(*args, **kwargs)

    def __eq__(self, other):
        if isinstance(other, str):
            other, units = DistanceField.parse_string(other)
            if other is None:
                return False

        if isinstance(other, self.__class__):
            return round(other.standard, self.prec) == round(self.standard, self.prec)
        if isinstance(other, int | float | Decimal):
            return other == self.standard

        return False

    def __ne__(self, other):
        if isinstance(other, str):
            other, units = DistanceField.parse_string(other)
            if other is None:
                return True

        if isinstance(other, self.__class__):
            return round(self.standard, self.prec) != round(other.standard, self.prec)
        if isinstance(other, int | float | Decimal):
            return other != self.standard

        return True

    def copy(self):
        dn = self.__class__()
        dn._default_unit = self._default_unit
        dn.standard = self.standard
        dn.prec = self.prec
        return dn

    def __neg__(self):
        dn = self.copy()
        dn.standard *= -1
        return dn

    def __pos__(self):
        dn = self.copy()
        if dn.standard <= 0:
            dn.standard *= -1
        return dn

    def __abs__(self):
        dn = self.copy()
        dn.standard = abs(dn.standard)
        return dn

    def __invert__(self):
        dn = self.copy()
        dn.standard *= -1
        return dn

    @classmethod
    def remove_exponent(cls, num: float) -> Decimal:
        d = Decimal(num)
        quant = "".zfill(cls.MAX_DECIMAL_PRECISION - 1)
        if d == d.to_integral():
            return d.quantize(Decimal(1))

        return d.quantize(Decimal(f".{quant}1")).normalize()

    def __str__(self):
        norm = self.remove_exponent(getattr(self, self._default_unit))
        return f"{norm.to_eng_string()}{self._default_unit}"


def register_units(**kwargs):
    """Register a unit type.

    Keyword arguments should be in the form alias=distance in metres.

    Example: ft=0.3048.
    """
    for k, v in kwargs.items():
        try:
            v = float(v)
        except ValueError:
            raise ImproperlyConfigured(
                f"Invalid distance unit {k}={v}m. Please ensure the value can be cast to a float."
            )

        D.UNITS[k] = v
        LOGGER.debug(f"Registered custom distance unit {k}={v}m")


def register_aliases(**kwargs):
    """Register an alias for a unit type.

    Keyword arguments should be in the form alias=unit, where unit is an existing unit alias.

    Example: in=inch, '"'=inch.
    """
    for k, v in kwargs.items():
        if v not in D.UNITS:
            LOGGER.warning(
                f"Unit alias {v} does not exist when adding "
                f"alias {k}. Please ensure you have already added "
                f"the unit type {v} using register_units if required."
            )
            continue

        D.ALIAS[k] = v
        LOGGER.debug(f"Registered '{k}' as an alias of unit type '{v}'")


class DistanceFieldDescriptor:
    def __init__(self, field):
        self.field = field

    def __get__(self, instance=None, owner=None):
        if instance is None:  # pragma: no cover
            return None

        return instance.__dict__[self.field.name]

    def __set__(self, instance, value):
        if value is None or value == "":
            instance.__dict__[self.field.name] = None

        if isinstance(value, tuple | list):
            value = value[0]

        if isinstance(value, str):
            dist, has_units = DistanceField.parse_string(value, self.field.default_unit)
            instance.__dict__[self.field.name] = dist
            self.field._has_no_units = not has_units
        elif isinstance(value, D):
            instance.__dict__[self.field.name] = value
        else:
            self.field._has_no_units = True
            kw = {
                self.field.default_unit: float(value or 0),
                "max_decimal_precision": self.field.decimal_places,
            }
            instance.__dict__[self.field.name] = D(**kw)

        self.field.update_unit_fields(instance)


class DistanceField(models.Field):
    ALPHA_REGEX = re.compile(r"([\s\-_a-z\"\']+)$", re.I)

    descriptor_class = DistanceFieldDescriptor
    default_validators = [validators.valid_unit_type]

    DEFAULT_UNIT = "m"

    def __init__(
        self,
        decimal_places=6,
        max_digits=14,
        unit_field=None,
        unit=DEFAULT_UNIT,
        *args,
        **kwargs,
    ):
        self.decimal_places = decimal_places
        self.max_digits = max_digits
        self.unit_field = unit_field
        self.default_unit = unit
        super().__init__(*args, **kwargs)

    def formfield(self, form_class=None, choices_form_class=None, **kwargs):
        return super().formfield(
            form_class=forms.DistanceField,
            choices_form_class=choices_form_class,
            **kwargs,
        )

    def get_internal_type(self):
        return "DecimalField"

    def contribute_to_class(self, cls, name, **kwargs):
        super().contribute_to_class(cls, name, **kwargs)
        setattr(cls, self.name, self.descriptor_class(self))
        signals.post_init.connect(self.update_after_init, sender=cls)

    @staticmethod
    def parse_string(value, default_units="m", max_digits=6) -> tuple[None | D, bool]:
        if not value:
            return None, False

        units = DistanceField.ALPHA_REGEX.findall(value)
        has_units = False
        if not units:
            units = default_units
            try:
                value = float(value)
            except ValueError:  # pragma: no cover
                return None, False
        else:
            has_units = True
            units = units[0].strip()
            try:
                value = float(value.replace(units, ""))
            except ValueError:
                return None, False

        # noinspection PyBroadException
        try:
            assert isinstance(units, str)
            kw = {D.unit_attname(units): value, "max_decimal_precision": max_digits}
            return D(**kw), has_units
        except Exception:
            return None, False

    # noinspection PyProtectedMember
    @staticmethod
    def distance_to_parts(distance):
        if distance is None:
            return None, None, None
        u = distance._default_unit
        return getattr(distance, u), u, distance.m

    # noinspection PyUnusedLocal
    def update_after_init(self, instance, **kwargs):
        if getattr(self, "_has_no_units", False) and self.unit_field:
            try:
                dist = getattr(instance, self.name)
                units = getattr(instance, self.unit_field)
            except KeyError:  # pragma: no cover
                return
            if not units:
                return
            parts = DistanceField.distance_to_parts(dist)
            if parts[1] != units:
                conv = getattr(dist, units)
                kw = {units: conv, "max_decimal_precision": self.decimal_places}
                instance.__dict__[self.name] = D(**kw)

    def update_unit_fields(self, instance):
        if not self.unit_field:
            return

        distance = DistanceField.distance_to_parts(getattr(instance, self.attname))
        try:
            if distance[0] is None:
                setattr(instance, self.unit_field, None)
            else:
                setattr(instance, self.unit_field, distance[1])
        except AttributeError:  # pragma: no cover
            raise ImproperlyConfigured(
                f"DistanceField {self.name} has unit field property {self.unit_field} "
                f"specified, but field cannot be found on instance."
            )

    def pre_save(self, model_instance, add=False):
        self.update_unit_fields(model_instance)
        return getattr(model_instance, self.name)

    def get_db_prep_value(self, value, connection, prepared=False):
        # Convert it to the "default_unit" format.
        value = super().get_db_prep_value(value, connection, prepared)
        return connection.ops.adapt_decimalfield_value(value, self.max_digits, self.decimal_places)

    def get_prep_value(self, value):
        if value is None or value == "":
            return None
        if isinstance(value, str):
            dist, has_units = DistanceField.parse_string(value, self.default_unit, self.max_digits)
        elif isinstance(value, D):
            dist = value
        else:
            try:
                return float(value)
            except ValueError:  # pragma: no cover
                return super().get_prep_value(value)

        return getattr(dist, self.default_unit)

    def get_prep_lookup(self, lookup_type, value):  # pragma: no cover
        if lookup_type in ("exact", "iexact", "gt", "gte", "lt", "lte"):
            return self.get_prep_value(value)
        if lookup_type == "in":
            return [self.get_prep_value(v) for v in value]
        raise TypeError(f"Lookup type {lookup_type} not supported.")

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self.max_digits is not None:
            kwargs["max_digits"] = self.max_digits
        if self.decimal_places is not None:
            kwargs["decimal_places"] = self.decimal_places
        if self.unit_field is not None:
            kwargs["unit_field"] = self.unit_field
        if self.default_unit is not None:
            kwargs["unit"] = self.default_unit
        return name, path, args, kwargs


class DistanceUnitField(fields.CharField):
    def __init__(self, *args, **kwargs):
        if kwargs.get("max_length") is None:
            kwargs["max_length"] = max([len(unit_len) for unit_len in D.UNITS])
        kwargs.update({"blank": True, "null": True, "editable": False})
        super().__init__(*args, **kwargs)
