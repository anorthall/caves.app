from django import forms
from django.db.models import Model
from django.test import TestCase, tag

from .fields import D, DistanceField, register_aliases, register_units
from .models import DistanceFieldTestModel as TestModel
from .validators import valid_unit_type


@tag("fast", "distancefield")
class DistanceFieldTestCase(TestCase):
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

    def test_unit_registration(self):
        register_units(test_m=2)

        with self.assertRaises(Exception):
            register_units(invalid="invalid")

        register_aliases(new_test="test_m", new_test_m="m")

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
        lst = list(
            TestModel.objects.filter(mm_field__lte="20in").values_list(
                "name", flat=True
            )
        )
        lst.sort()
        self.assertEqual(lst, ["all_inches", "mixed"])

        lst = list(
            TestModel.objects.filter(mm_field="20in").values_list("name", flat=True)
        )
        lst.sort()
        self.assertEqual(lst, ["all_inches"])

        lst = list(TestModel.objects.filter(mtr_field=0).values_list("name", flat=True))
        lst.sort()
        self.assertEqual(lst, ["mixed"])

    def test_form(self):
        class TestMod(Model):
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
        """This test is considered to pass if it does not raise an ValidationError"""
        valid_unit_type("0")
