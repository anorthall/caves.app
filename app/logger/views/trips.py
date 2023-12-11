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
from django.views.generic import CreateView, RedirectView, TemplateView, UpdateView
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
        form.save_m2m()

        log_trip_action(self.request.user, self.object, "updated")
        return redirect(trip.get_absolute_url())


class TripDetail(TripContextMixin, ViewableObjectDetailView):
    model = Trip
    template_name = "logger/trip_detail.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_queryset(self):
        return (
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

        if not self.object.private_photos or self.object.user == self.request.user:
            if valid_photos := self.object.valid_photos:
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
        form.save_m2m()
        trip.followers.add(self.request.user)

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


class TripPhotoFeature(LoginRequiredMixin, View):
    def post(self, request, uuid, photo_uuid):
        trip = get_object_or_404(Trip, uuid=uuid)
        if trip.user != request.user:
            raise PermissionDenied

        photo = get_object_or_404(TripPhoto, uuid=photo_uuid)
        trip.featured_photo = photo
        trip.save()
        log_trip_action(request.user, trip, "set featured photo", photo.uuid)
        messages.success(
            request,
            "The featured photo has been updated.",
        )
        return redirect(trip.get_absolute_url())


class TripPhotoUnsetFeature(LoginRequiredMixin, View):
    def post(self, request, uuid):
        trip = get_object_or_404(Trip, uuid=uuid)
        if trip.user != request.user:
            raise PermissionDenied

        trip.featured_photo = None
        trip.save()
        log_trip_action(request.user, trip, "unset featured photo")
        messages.success(
            request,
            "The featured photo has been unset.",
        )
        return redirect(trip.get_absolute_url())


class TripDelete(LoginRequiredMixin, View):
    def post(self, request, uuid):
        trip = get_object_or_404(Trip, uuid=uuid)
        if trip.user != request.user:
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


class TripReportRedirect(RedirectView):
    """Redirect to support old TripReport Model URLs which are now Trip URLs"""

    def get_redirect_url(self, *args, **kwargs):
        trip = get_object_or_404(Trip, uuid=kwargs.get("uuid"))
        return trip.get_absolute_url()


class HTMXTripFollow(LoginRequiredMixin, TemplateView):
    """HTMX view for toggling following a trip"""

    template_name = "logger/_htmx_trip_follow.html"

    @method_decorator(ratelimit(key="user", rate="20/h"))
    def post(self, request, uuid):
        trip = self._get_trip(request, uuid)
        context = {"trip": trip, "user": request.user}

        if trip.user_followed:  # User already follows, so unfollow the trip
            trip.followers.remove(request.user)
            log_trip_action(request.user, trip, "unfollowed")
        else:  # User doesn't follow, so follow the trip
            trip.followers.add(request.user)
            log_trip_action(request.user, trip, "followed")

        return self.render_to_response(context)

    def _get_trip(self, request, uuid):
        trip = (
            Trip.objects.filter(uuid=uuid)
            .annotate(
                user_followed=Exists(
                    User.objects.filter(
                        pk=request.user.pk, followed_trips=OuterRef("pk")
                    ).only("pk")
                )
            )
            .first()
        )

        if not trip:
            raise Http404

        if trip.is_viewable_by(request.user):
            return trip

        raise PermissionDenied
