from django.db import models

from .fields import DistanceField, DistanceUnitField


class DistanceFieldTestModel(models.Model):
    name = models.CharField(unique=True, max_length=20)

    mm_field = DistanceField(unit="mm", unit_field="mm_field_units")
    inch_field = DistanceField(unit="inch", unit_field="inch_field_units")
    mtr_field = DistanceField(unit_field="mtr_field_units")
    no_unit_field = DistanceField(unit="inch", default="10in")

    mm_field_units = DistanceUnitField()
    inch_field_units = DistanceUnitField()
    mtr_field_units = DistanceUnitField()

    def __str__(self):
        return "{}, {}, {}".format(self.mm_field, self.inch_field, self.mtr_field)
