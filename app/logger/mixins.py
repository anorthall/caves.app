from django.core.exceptions import PermissionDenied, ValidationError
from django.views.generic import DetailView
from logger.templatetags.logger_tags import distformat
from maps.services import get_lat_long_from


class TripContextMixin:
    """Mixin to add trip context to Trip views."""

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        trip = self.object

        object_owner = trip.user
        if object_owner != self.request.user:
            context["can_view_profile"] = object_owner.is_viewable_by(self.request.user)

            if self.request.user not in object_owner.friends.all():
                if object_owner.allow_friend_username:
                    context["can_add_friend"] = True

        context["trip"] = trip
        context["object_owner"] = object_owner
        return context


# noinspection PyAttributeOutsideInit
class ViewableObjectDetailView(DetailView):
    """A DetailView that considers permissions for objects like a Trip"""

    def dispatch(self, request, *args, **kwargs):
        """Get the object and test permissions before dispatching the view"""
        self.object = self.get_object()
        if self.object.is_viewable_by(request.user):
            return super().dispatch(request, *args, **kwargs)
        else:
            raise PermissionDenied

    def get(self, request, *args, **kwargs):
        """Do not fetch the object here, as it was fetched in dispatch()"""
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class DistanceUnitFormMixin:
    def __init__(self, *args, **kwargs):
        """
        Format all distance units using distformat

        There is a bug(?) in django-distance-field that causes distances
        to occasionally be rendered as scientific notation. Formatting using
        distformat fixes this.
        """

        instance = kwargs.get("instance", None)
        if not instance:
            super().__init__(*args, **kwargs)
            return

        distance_fields = [
            "horizontal_dist",
            "vert_dist_down",
            "vert_dist_up",
            "surveyed_dist",
            "resurveyed_dist",
            "aid_dist",
        ]

        units = instance.user.units
        initial = {
            field: distformat(getattr(instance, field), units)
            for field in distance_fields
        }
        kwargs["initial"] = initial
        super().__init__(*args, **kwargs)


class CleanCaveLocationMixin:
    def clean_cave_location(self):
        """Validate the cave location"""
        cave_location = self.cleaned_data.get("cave_location")
        if not cave_location:
            return cave_location

        try:
            lat, lng = get_lat_long_from(cave_location)
        except ValueError:
            raise ValidationError(
                "Please ensure that lat/long values are displayed on the page before "
                "saving, or enter your own lat/long values instead of a place name."
            )

        self.cleaned_data["latitude"] = lat
        self.cleaned_data["longitude"] = lng
        return cave_location
