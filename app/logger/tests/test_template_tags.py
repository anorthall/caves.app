from django.contrib.auth import get_user_model
from django.contrib.gis.measure import D
from django.test import TestCase, tag

from ..templatetags import distformat

User = get_user_model()


@tag("unit", "fast", "logger")
class TemplateTagUnitTests(TestCase):
    def test_format_metric_templatetag_with_small_value(self):
        """Test the format_metric() function with a small value"""
        self.assertEqual(distformat.format_metric(D(ft=1000)), "305m")

    def test_format_metric_templatetag_with_large_value(self):
        """Test the format_metric() function with a large value"""
        self.assertEqual(distformat.format_metric(D(mi=100)), "160.93km")

    def test_format_imperial_templatetag_with_small_value(self):
        """Test the format_imperial() function with a small value"""
        self.assertEqual(distformat.format_imperial(D(m=100)), "328ft")

    def test_format_imperial_templatetag_with_large_value(self):
        """Test the format_imperial() function with a large value"""
        self.assertEqual(distformat.format_imperial(D(km=100)), "62.14mi")

    def test_distformat_templatetag_with_metric_value(self):
        """Test the distformat() function with a metric value"""
        metric = User.METRIC
        self.assertEqual(distformat.distformat(D(ft=1000), format=metric), "305m")

    def test_distformat_templatetag_with_imperial_value(self):
        """Test the distformat() function with an imperial value"""
        imperial = User.IMPERIAL
        self.assertEqual(distformat.distformat(D(km=100), format=imperial), "62.14mi")
