from comments.forms import CommentForm
from core.logging import log_trip_action
from core.utils import get_user
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.gis.geos import Point
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Exists, OuterRef
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import CreateView, RedirectView, UpdateView
from django_ratelimit.decorators import ratelimit
from users.models import CavingUser as User

from ..forms import TripForm
from ..mixins import TripContextMixin, ViewableObjectDetailView
from ..models import Trip, TripPhoto


class TripsRedirect(LoginRequiredMixin, RedirectView):
    """Redirect from /trips/ to /u/username"""

    def get_redirect_url(self, *args, **kwargs):
        return reverse("log:user", kwargs={"username": self.request.user.username})


class TripUpdate(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Trip
    form_class = TripForm
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    extra_context = {"title": "Edit trip"}
    template_name = "logger/crispy_form.html"
    success_message = "The trip has been updated."

    def get_queryset(self):
        return Trip.objects.filter(user=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object_owner"] = self.object.user
        return context

    def form_valid(self, form):
        trip = form.save(commit=False)

        lat = form.cleaned_data.get("latitude")
        lng = form.cleaned_data.get("longitude")
        if lat and lng:
            trip.cave_coordinates = Point(lng, lat)

        trip.save()

        log_trip_action(self.request.user, self.object, "updated")
        return redirect(trip.get_absolute_url())


class TripDetail(TripContextMixin, ViewableObjectDetailView):
    model = Trip
    template_name = "logger/trip_detail.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_queryset(self):
        qs = (
            Trip.objects.all()
            .select_related("user")
            .prefetch_related(
                "photos",
                "likes",
                "comments",
                "comments__author",
                "likes__friends",
                "user__friends",
            )
            .annotate(
                likes_count=Count("likes", distinct=True),
                comments_count=Count("comments", distinct=True),
                user_liked=Exists(
                    User.objects.filter(
                        pk=self.request.user.pk, liked_trips=OuterRef("pk")
                    ).only("pk")
                ),
            )
        )
        return qs

    def get_object(self, *args, **kwargs):
        """Sanitise the Trip for the current user"""
        obj = super().get_object(*args, **kwargs)
        if obj.user == self.request.user:
            return obj
        else:
            return obj.sanitise(self.request.user)

    def get_context_data(self, *args, **kwargs):
        """Add the string of users that liked the trip to the context"""
        context = super().get_context_data(*args, **kwargs)

        if self.request.user.is_authenticated:
            friends = get_user(self.request).friends.all()
        else:
            friends = None

        context["liked_str"] = {
            self.object.pk: self.object.get_liked_str(self.request.user, friends)
        }

        valid_photos = self.object.valid_photos
        if valid_photos:
            if not self.object.private_photos or self.object.user == self.request.user:
                context["show_photos"] = True
                context["valid_photos"] = valid_photos

        if self.object.user.allow_comments:
            context["comment_form"] = CommentForm(self.request, self.object)

        return context


@method_decorator(
    ratelimit(key="user", rate="30/h", method=ratelimit.UNSAFE), name="dispatch"
)
class TripCreate(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Trip
    form_class = TripForm
    template_name = "logger/crispy_form.html"
    extra_context = {"title": "Add a trip"}
    success_message = "The trip has been created."
    initial = {
        "start": timezone.localdate(),
        "end": timezone.localdate(),
    }

    def form_valid(self, form):
        trip = form.save(commit=False)
        trip.user = self.request.user

        lat = form.cleaned_data.get("latitude")
        lng = form.cleaned_data.get("longitude")
        if lat and lng:
            trip.cave_coordinates = Point(lng, lat)

        trip.save()

        log_trip_action(self.request.user, trip, "added")

        if self.request.POST.get("addanother", False):
            return redirect(reverse("log:trip_create"))
        return redirect(trip.get_absolute_url())

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        initial = initial.copy()
        initial["cave_country"] = get_user(self.request).country.name
        return initial


class TripDelete(LoginRequiredMixin, View):
    def post(self, request, uuid):
        trip = get_object_or_404(Trip, uuid=uuid)
        if not trip.user == request.user:
            raise PermissionDenied

        # Delete all photos associated with the trip
        photos = TripPhoto.objects.all().filter(trip=trip)
        if photos.exists():
            photos.update(deleted_at=timezone.now())

        trip.delete()
        log_trip_action(request.user, trip, "deleted")
        messages.success(
            request,
            f"The trip to {trip.cave_name} has been deleted.",
        )
        return redirect("log:user", username=request.user.username)


class TripReportDetail(TripContextMixin, ViewableObjectDetailView):
    model = Trip
    template_name = "logger/trip_report_detail.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_object(self, *args, **kwargs):
        """Check that the trip has a report, otherwise raise 404"""
        obj = super().get_object(*args, **kwargs)
        if obj.trip_report.strip():
            return obj
        else:
            raise Http404

    def get_queryset(self):
        qs = (
            Trip.objects.all()
            .select_related("user")
            .prefetch_related(
                "photos",
            )
        )
        return qs
