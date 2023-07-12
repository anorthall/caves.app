from comments.forms import CommentForm
from core.utils import get_user
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Exists, OuterRef
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, RedirectView, UpdateView
from users.models import CavingUser as User

from ..forms import TripForm
from ..mixins import TripContextMixin, ViewableObjectDetailView
from ..models import Trip


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


class TripDetail(TripContextMixin, ViewableObjectDetailView):
    model = Trip
    template_name = "logger/trip_detail.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_queryset(self):
        qs = (
            Trip.objects.all()
            .select_related("user", "report")
            .prefetch_related(
                "photos",
                "likes",
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
        candidate = form.save(commit=False)
        candidate.user = self.request.user
        candidate.save()
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        initial = initial.copy()
        initial["cave_country"] = get_user(self.request).country.name
        return initial

    def get_success_url(self):
        if self.request.POST.get("addanother", False):
            return reverse("log:trip_create")
        return super().get_success_url()


class TripDelete(LoginRequiredMixin, View):
    def post(self, request, uuid):
        trip = get_object_or_404(Trip, uuid=uuid)
        if not trip.user == request.user:
            raise PermissionDenied
        trip.delete()
        messages.success(
            request,
            f"The trip to {trip.cave_name} has been deleted.",
        )
        return redirect("log:user", username=request.user.username)
