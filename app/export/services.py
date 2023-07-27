from django.db.models import Model, QuerySet
from django.utils import timezone
from logger.models import Trip
from tablib import Dataset
from users.models import CavingUser as User


class Exporter:
    """Export a Django Model to a tabular format for use with tablib"""

    fields = []
    field_headers = {}
    distance_units = "m"
    model: Model = None

    def __init__(self, queryset):
        self.queryset = queryset

    def generate(self) -> Dataset:
        """Generate rows based on the QuerySet and fields passed to the constructor"""
        data = Dataset(headers=self._build_header())

        for obj in self.queryset:
            data.append(self._build_row(obj))

        return data

    def _build_row(self, obj) -> list[str]:
        """Iterate through each field in self.fields and format the value"""
        row = []
        for field_name in self.fields:
            value = getattr(obj, field_name)
            row += [self._format_field(field_name, value)]
        return row

    def _format_field(self, field_name, value) -> str:
        """
        Determine if we have a handler for the field type and call it
        Otherwise, return the value as a string
        """
        field_type = self.model._meta.get_field(field_name).__class__.__name__
        handler = getattr(self, f"_format_{field_type.lower()}", None)

        if not handler:
            handler = str

        if value is None:
            return ""
        return handler(value)

    def _build_header(self) -> list[str]:
        """Return a list of headers for the dataset"""
        return [self._get_field_header(field_name) for field_name in self.fields]

    def _get_field_header(self, field_name) -> str:
        """
        Return the header for a given field by calling the get_<field_name>_header
        method if it exists, then checking the field_headers dict, then calling
        get_<field_type>_header if it exists, then falling back to the verbose_name.
        """
        field_type = self.model._meta.get_field(field_name).__class__.__name__.lower()
        if hasattr(self, f"_get_{field_name}_header"):
            return getattr(self, f"_get_{field_name}_header")()
        elif field_name in self.field_headers:
            return self.field_headers[field_name]
        elif hasattr(self, f"_get_{field_type}_header"):
            return getattr(self, f"_get_{field_type}_header")(field_name)
        else:
            return self.model._meta.get_field(field_name).verbose_name.capitalize()

    def _get_field_verbose_name(self, field_name) -> str:
        return self.model._meta.get_field(field_name).verbose_name

    def _get_datetimefield_header(self, field_name) -> str:
        tz = timezone.get_current_timezone()
        verbose_name = self._get_field_verbose_name(field_name).capitalize()
        return f"{verbose_name} ({tz})"

    def _get_distancefield_header(self, field_name) -> str:
        verbose_name = self._get_field_verbose_name(field_name).capitalize()
        return f"{verbose_name} ({self._get_distance_units()})"

    def _get_distance_units(self) -> str:
        return self.distance_units

    def _format_datetimefield(self, value) -> str:
        return timezone.localtime(value).strftime("%Y-%m-%d %H:%M:%S")

    def _format_distancefield(self, value) -> str:
        if hasattr(value, self._get_distance_units()):
            return str(getattr(value, self._get_distance_units()))
        return str(value.m)


class TripExporter(Exporter):
    # TODO: Add Location/Lat/Long
    model = Trip
    fields = [
        "cave_name",
        "cave_entrance",
        "cave_exit",
        "cave_region",
        "cave_country",
        "start",
        "end",
        "duration_str",
        "type",
        "clubs",
        "expedition",
        "cavers",
        "custom_field_1",
        "custom_field_2",
        "custom_field_3",
        "custom_field_4",
        "custom_field_5",
        "horizontal_dist",
        "vert_dist_up",
        "vert_dist_down",
        "surveyed_dist",
        "resurveyed_dist",
        "aid_dist",
        "notes",
        "added",
        "updated",
        "privacy",
    ]
    field_headers = {
        "duration_str": "Duration",
    }

    def __init__(self, user: User, queryset: QuerySet):
        self.user = user

        # Handle custom field labels and remove any fields that don't have a label
        for field in self.fields.copy():
            if field.startswith("custom_field"):
                if hasattr(self.user, f"{field}_label"):
                    label = getattr(self.user, f"{field}_label")
                    if label:
                        self.field_headers[field] = label
                    else:
                        self.fields.remove(field)

        super().__init__(queryset)

    def _get_distance_units(self) -> str:
        if self.user.units == User.IMPERIAL:
            return "ft"
        return "m"
