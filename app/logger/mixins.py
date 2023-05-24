from django.core.exceptions import PermissionDenied
from django.views.generic import DetailView

from .forms import AddCommentForm
from .models import Trip, TripReport


class TripContextMixin:
    """Mixin to add trip context to Trip and TripReport views."""

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        if isinstance(self.object, TripReport):
            report = self.object
            trip = report.trip
            context["is_report"] = True  # For includes/trip_header.html
        elif isinstance(self.object, Trip):
            trip = self.object
            report = None
            if hasattr(trip, "report"):
                report = trip.report
        elif not self.object:
            # Django will return a 404 shortly, so we can just exit
            return
        else:
            raise TypeError("Object is not a Trip or TripReport")

        object_owner = trip.user
        if not object_owner == self.request.user:
            context["can_view_profile"] = object_owner.is_viewable_by(self.request.user)

            if self.request.user not in object_owner.friends.all():
                if object_owner.allow_friend_username:
                    context["can_add_friend"] = True

            if report:
                context["can_view_report"] = report.is_viewable_by(self.request.user)

        context["trip"] = trip
        context["report"] = report
        context["object_owner"] = object_owner

        # Comment form
        initial = {
            "pk": self.object.pk,
            "type": self.object.__class__.__name__.lower(),
        }
        context["add_comment_form"] = AddCommentForm(self.request, initial=initial)
        return context


class ViewableObjectDetailView(DetailView):
    """A DetailView that considers permissions for objects like Trip and TripReport"""

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
