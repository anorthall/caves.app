import logging

from django import forms
from django.db.models import Model
from django.test import TestCase, tag

from .fields import D, DistanceField, register_aliases, register_units
from .models import DistanceFieldTestModel as TestModel
from .validators import valid_unit_type


@tag("fast", "distancefield")
class DistanceFieldTests(TestCase):
    FORM_TEST_VALUES = [
        ("100mm", "100mm"),
        ("100 mm", "100mm"),
        ("10 in", "10in"),
        ("10m", "10m"),
        ("-10.5m", "-10.5m"),
    ]

    INVALID_FORM_TEST_VALUES = [
        "100monkeys",
        "10 unit does not exist",
        "-10 asdas__",
        "10",
    ]

    def setUp(self):
        TestModel.objects.create(
            mm_field="10m", inch_field="10m", mtr_field="10m", name="all_metres"
        )
        TestModel.objects.create(
            mm_field="20in", inch_field="19in", mtr_field="18in", name="all_inches"
        )
        TestModel.objects.create(
            mm_field=D(mm=200), inch_field="-20mm", mtr_field="0 inch", name="mixed"
        )
        TestModel.objects.create(
            mm_field="20000000.123mm",
            inch_field="-20000000.123mm",
            mtr_field="0.00002 inch",
            name="large",
        )

    def test_setting(self):
        tm = TestModel.objects.first()
        tm.mm_field = ""
        self.assertEqual(tm.mm_field, None)

        tm.mm_field = ("10m", "200m")
        self.assertEqual(tm.mm_field, D(m=10))

        tm.mm_field = "20m"
        self.assertEqual(tm.mm_field, D(m=20))

        tm.mm_field = D(m=30)
        self.assertEqual(tm.mm_field, D(m=30))

        tm.mm_field = 40
        self.assertEqual(tm.mm_field, D(mm=40))

    def test_unit_registration(self):
        register_units(test_m=2)

        with self.assertRaises(Exception):
            register_units(invalid="invalid")

        register_aliases(new_test="test_m", new_test_m="m")

        logging.disable(logging.CRITICAL)
        register_aliases(this_should_fail="with_a_warning")
        logging.disable(logging.NOTSET)

        self.assertEqual(D(test_m=1), D(mm=2000))
        self.assertEqual(D(new_test=1), D(test_m=1))
        self.assertEqual(D(new_test_m=100000), D(m=100000))

    def test_basic(self):
        self.assertNotEqual(D(mm=1000.123), D(mm=1000.124))
        self.assertEqual(D(inch=10), D(mm=254))
        self.assertEqual(D(m=5), 5)
        self.assertNotEqual(D(m=5), 6)
        self.assertNotEqual(D(m=5), "6inch")
        self.assertNotEqual(D(m=5), "noteq")
        self.assertEqual(D(inch=10.5), D(mm=10.5 * 25.4))
        self.assertEqual(D(inch=10.123), -D(inch=-10.123))
        self.assertEqual(D(inch=10.123), abs(-D(inch=-10.123)))
        self.assertEqual(D(inch=10.123), +D(inch=-10.123))
        self.assertEqual(D(inch=-10.123), ~D(inch=10.123))
        self.assertNotEqual(D(m=5), {})

    def test_unit_conversion(self):
        tm = TestModel.objects.get(name="all_metres")
        self.assertEqual(tm.no_unit_field, D(inch=10))
        self.assertEqual(tm.mm_field, D(m=10))
        self.assertEqual(tm.mm_field, D(mm=10 * 1000))
        self.assertEqual(tm.mm_field, tm.inch_field)
        self.assertEqual(tm.mm_field, tm.mtr_field)

        tm = TestModel.objects.get(name="all_inches")
        self.assertEqual(tm.mm_field, D(inch=20))
        self.assertEqual(tm.inch_field, D(inch=19))
        self.assertEqual(tm.mtr_field, D(inch=18))

        tm = TestModel.objects.get(name="mixed")
        self.assertEqual(tm.mm_field, D(mm=200))
        self.assertEqual(tm.inch_field, "-20mm")
        self.assertEqual(tm.mtr_field, 0)

    def test_large_units(self):
        tm = TestModel.objects.get(name="large")
        self.assertEqual(tm.mm_field, D(mm=20000000.123))
        self.assertEqual(tm.inch_field, -tm.mm_field)
        self.assertEqual(tm.mtr_field, D(mm=5.08e-4))

    def test_queryset_filtering(self):
        lst = list(TestModel.objects.filter(mm_field__lte="20in").values_list("name", flat=True))
        lst.sort()
        self.assertEqual(lst, ["all_inches", "mixed"])

        lst = list(TestModel.objects.filter(mm_field="20in").values_list("name", flat=True))
        lst.sort()
        self.assertEqual(lst, ["all_inches"])

        lst = list(TestModel.objects.filter(mtr_field=0).values_list("name", flat=True))
        lst.sort()
        self.assertEqual(lst, ["mixed"])

    def test_form(self):
        class TestMod(Model):  # noqa: DJ008
            dist = DistanceField()

        class TestForm(forms.ModelForm):
            class Meta:
                model = TestMod
                fields = ("dist",)

        for value, eq in self.FORM_TEST_VALUES:
            df = TestForm({"dist": value})
            self.assertEqual(df.is_valid(), True)
            self.assertEqual(df.cleaned_data["dist"], D(eq))

        for value in self.INVALID_FORM_TEST_VALUES:
            df = TestForm({"dist": value})
            self.assertEqual(df.is_valid(), False)

    def test_validation_with_a_zero(self):
        """This test is considered to pass if it does not raise an ValidationError."""
        valid_unit_type("0")

    def test_distance_field_test_model_str(self):
        """Test the distance field test model __str__ method."""
        tm = TestModel.objects.first()
        self.assertEqual(str(tm), f"{tm.mm_field}, {tm.inch_field}, {tm.mtr_field}")

    def test_string_parsing(self):
        self.assertEqual(DistanceField.parse_string("abcdefghijk"), (None, False))
        self.assertEqual(DistanceField.parse_string("345defghijk"), (None, False))

    def test_distance_to_parts_method(self):
        """Test the distance_to_parts method."""
        self.assertEqual(DistanceField.distance_to_parts(None), (None, None, None))

        self.assertEqual(DistanceField.distance_to_parts(D(mm=10)), (10.0, "mm", 0.01))
