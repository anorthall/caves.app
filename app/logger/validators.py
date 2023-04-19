from django.contrib.gis.measure import Distance
from django.core.exceptions import ValidationError


def above_zero_dist_validator(distance):
    """Check a distance value is above zero."""
    if distance.m < 0.0:
        raise ValidationError("Distance must be above zero.")


def horizontal_dist_validator(distance, max_dist=Distance(mi=20)):
    """Check a distance value does not exceed an upper limit, by default 20 miles."""
    if distance > max_dist:
        raise ValidationError("Distance is too large.")


def vertical_dist_validator(distance, max_dist=Distance(m=3000)):
    """Check a distance value does not exceed an upper limit, by default 3000 metres."""
    if distance > max_dist:
        raise ValidationError("Distance is too large.")
