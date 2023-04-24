import csv

from core.models import News
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Exists, OuterRef, Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import localtime as lt
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
    View,
)
from logger import statistics
from users.models import Notification, UserSettings

from .forms import AddCommentForm, AllUserNotificationForm, TripForm, TripReportForm
from .models import Comment, Trip, TripReport
from .templatetags.distformat import distformat

User = get_user_model()


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
            if hasattr(trip, "report"):
                report = trip.report
            else:
                report = None
        elif not self.object:
            # Django will return Http404 shortly, so we can just
            return
        else:
            raise TypeError("Object is not a Trip or TripReport")

        user = trip.user

        if not user == self.request.user:
            context["can_view_profile"] = user.profile.is_viewable_by(self.request.user)

            if self.request.user not in user.profile.friends.all():
                if user.settings.friend_allow_username:
                    context["can_add_friend"] = True

            if report:
                context["can_view_report"] = report.is_viewable_by(self.request.user)

        context["trip"] = trip
        context["report"] = report
        # This is the author of the trip/report, not the request user
        context["user"] = user

        # Comment form
        initial = {
            "pk": self.object.pk,
            "type": self.object.__class__.__name__.lower(),
        }
        context["add_comment_form"] = AddCommentForm(self.request, initial=initial)
        return context

    def get_object(self, *args, **kwargs):
        self.object = super().get_object(*args, **kwargs)
        return self.object


def index(request):
    """
    Index page for the website.

    Unregistered users will be shown a static welcome page.

    Registered users will be shown an interface to add/manage
    recent caving trips.

    Newly registered users will be shown a help page.
    """
    if not request.user.is_authenticated:
        return render(request, "index/index_unregistered.html")

    context = {}

    news = (
        News.objects.filter(is_published=True, posted_at__lte=timezone.now())
        .prefetch_related("author__profile")
        .order_by("-posted_at")[:3]
    )
    context["news"] = news

    friends = request.user.profile.friends.all()
    trips = (
        Trip.objects.filter(Q(user__in=friends) | Q(user=request.user))
        .select_related("user__settings")
        .prefetch_related("comments", "likes")
        .prefetch_related("user__profile__friends")
        .annotate(
            likes_count=Count("likes", distinct=True),
            comments_count=Count("comments", distinct=True),
            user_liked=Exists(
                User.objects.filter(
                    pk=request.user.pk, liked_trips=OuterRef("pk")
                ).only("pk")
            ),
        )
    ).order_by("-added")[
        :25
    ]  # TODO: Make this configurable

    # Remove trips that the user does not have permission to view.
    context["trips"] = [x for x in trips if x.is_viewable_by(request.user)]

    if len(context["trips"]) == 0:
        return render(request, "index/index_new_user.html", context)

    # Build the 'liked_str' dictionary
    liked_str_index = {}
    for trip in context["trips"]:
        liked_str_index[trip.pk] = trip.get_liked_str(request.user)
    context["liked_str"] = liked_str_index

    return render(request, "index/index_registered.html", context)


@login_required
def export(request):
    """Export a user's trips to CSV file"""
    if not request.POST:  # Display information page
        return render(request, "export.html")

    # Generate HTTP response and the CSV file
    qs = Trip.objects.filter(user=request.user).order_by("start", "pk")
    if not qs:
        messages.error(request, "You do not have any trips to export.")
        return redirect("log:export")

    timestamp = timezone.now().strftime("%Y-%m-%d-%H%M")
    filename = f"{request.user.username}-trips-{timestamp}.csv"
    response = HttpResponse(
        content_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

    writer = csv.writer(response)

    # Headers
    tz = timezone.get_current_timezone()
    writer.writerow(
        [
            "Number",
            "Cave name",
            "Cave region",
            "Cave country",
            "Cave URL",
            f"Trip start ({tz})",
            f"Trip end ({tz})",
            "Duration",
            "Trip type",
            "Cavers",
            "Clubs",
            "Expedition",
            "Horizontal distance",
            "Vertical distance down",
            "Vertical distance up",
            "Surveyed distance",
            "Resurveyed distance",
            "Aid climbing distance",
            "Notes",
            "URL",
            "Trip report",
            f"Added on ({tz})",
            f"Last updated ({tz})",
        ]
    )

    # Content
    units = request.user.settings.units  # Distance units
    tf = "%Y-%m-%d %H:%M"  # Time format to use
    x = 1
    for t in qs:
        row = [  # Break row into two to process end time
            x,
            t.cave_name,
            t.cave_region,
            t.cave_country,
            t.cave_url,
            lt(t.start).strftime(tf),
        ]

        # End time may not exist, so check first
        try:
            row = row + [lt(t.end).strftime(tf)]
        except AttributeError:
            row = row + [t.end]

        trip_report = ""
        if t.has_report:
            trip_report = f"{settings.SITE_ROOT}{t.report.get_absolute_url()}"

        row = row + [  # Second half of row
            t.duration_str,
            t.type,
            t.cavers,
            t.clubs,
            t.expedition,
            distformat(t.horizontal_dist, units, simplify=False),
            distformat(t.vert_dist_down, units, simplify=False),
            distformat(t.vert_dist_up, units, simplify=False),
            distformat(t.surveyed_dist, units, simplify=False),
            distformat(t.resurveyed_dist, units, simplify=False),
            distformat(t.aid_dist, units, simplify=False),
            t.notes,
            f"{settings.SITE_ROOT}{t.get_absolute_url()}",
            trip_report,
            lt(t.added).strftime(tf),
            lt(t.updated).strftime(tf),
        ]

        writer.writerow(row)  # Finally write the complete row
        x += 1

    return response  # Return the CSV file as a HttpResponse


@login_required
def user_statistics(request):
    trips = request.user.trips
    chart_units = "m"
    if request.user.settings.units == UserSettings.IMPERIAL:
        chart_units = "ft"

    # Generate stats for trips/distances by year
    this_year = timezone.now().year
    prev_year = (timezone.now() - timezone.timedelta(days=365)).year
    prev_year_2 = (timezone.now() - timezone.timedelta(days=730)).year
    trip_stats = statistics.stats_for_user(trips)
    trip_stats_year0 = statistics.stats_for_user(trips, year=prev_year_2)
    trip_stats_year1 = statistics.stats_for_user(trips, year=prev_year)
    trip_stats_year2 = statistics.stats_for_user(trips, year=this_year)

    # Check if we should show time charts
    show_time_charts = False
    if len(trips) >= 2:
        ordered = trips.order_by("-start")
        if (ordered.first().start.date() - ordered.last().start.date()).days > 40:
            if trips.filter(end__isnull=False):
                show_time_charts = True

    context = {
        "trips": trips,
        "gte_five_trips": len(trips) >= 5,
        "show_time_charts": show_time_charts,
        "user": request.user,
        "dist_format": request.user.settings.units,
        "chart_units": chart_units,
        "year0": prev_year_2,
        "year1": prev_year,
        "year2": this_year,
        "trip_stats": trip_stats,
        "trip_stats_year0": trip_stats_year0,
        "trip_stats_year1": trip_stats_year1,
        "trip_stats_year2": trip_stats_year2,
        "common_caves": statistics.common_caves(trips),
        "common_cavers": statistics.common_cavers(trips),
        "common_cavers_by_time": statistics.common_cavers_by_time(trips),
        "common_clubs": statistics.common_clubs(trips),
        "most_duration": trips.exclude(duration=None).order_by("-duration")[0:10],
        "averages": statistics.trip_averages(trips, request.user.settings.units),
        "most_vert_up": trips.filter(vert_dist_up__gt=0).order_by("-vert_dist_up")[
            0:10
        ],
        "most_vert_down": trips.filter(vert_dist_down__gt=0).order_by(
            "-vert_dist_down"
        )[0:10],
        "most_surveyed": trips.filter(surveyed_dist__gt=0).order_by("-surveyed_dist")[
            0:10
        ],
        "most_resurveyed": trips.filter(resurveyed_dist__gt=0).order_by(
            "-resurveyed_dist"
        )[0:10],
        "most_aid": trips.filter(aid_dist__gt=0).order_by("-aid_dist")[0:10],
        "most_horizontal": trips.filter(horizontal_dist__gt=0).order_by(
            "-horizontal_dist"
        )[0:10],
    }
    return render(request, "statistics.html", context)


def admin_tools(request):  # noqa: C901
    """Tools for website administrators."""
    if not request.user.is_superuser:
        raise Http404

    if request.POST:
        if request.POST.get("login_as", False):
            try:
                user = User.objects.get(email=request.POST["login_as"])
                if user.is_superuser:
                    messages.error(
                        request, "Cannot login as a superuser via this page."
                    )
                elif user:
                    messages.success(request, f"Now logged in as {user.email}.")
                    login(request, user)
                    return redirect("log:index")

            except ObjectDoesNotExist:
                messages.error(request, "User was not found.")
        elif request.POST.get("notify", False):
            form = AllUserNotificationForm(request.POST)
            if form.is_valid():
                for user in User.objects.all():
                    Notification.objects.create(
                        user=user,
                        message=form.cleaned_data["message"],
                        url=form.cleaned_data["url"],
                    )
                messages.success(request, "Notifications sent.")

    users = User.objects.all()
    active_users = users.filter(is_active=True)
    disabled_users = users.filter(is_active=False)
    prune_users = disabled_users.filter(
        date_joined__lt=timezone.now() - timezone.timedelta(days=1)
    )
    joined_year = users.filter(
        date_joined__gt=timezone.now() - timezone.timedelta(days=365)
    )
    joined_month = joined_year.filter(
        date_joined__gt=timezone.now() - timezone.timedelta(days=31)
    )
    joined_week = joined_month.filter(
        date_joined__gt=timezone.now() - timezone.timedelta(days=7)
    )
    joined_day = joined_week.filter(
        date_joined__gt=timezone.now() - timezone.timedelta(days=1)
    )

    trips = Trip.objects.all()
    trips_year = trips.filter(added__gt=timezone.now() - timezone.timedelta(days=365))
    trips_month = trips_year.filter(
        added__gt=timezone.now() - timezone.timedelta(days=31)
    )
    trips_week = trips_month.filter(
        added__gt=timezone.now() - timezone.timedelta(days=7)
    )
    trips_day = trips_week.filter(added__gt=timezone.now() - timezone.timedelta(days=1))

    login_user_list = active_users.values_list("email", flat=True)

    context = {
        "users": users,
        "active_users": active_users.order_by("-last_seen"),
        "disabled_users": disabled_users,
        "prune_users": prune_users.order_by("date_joined"),
        "joined_day": joined_day,
        "joined_week": joined_week,
        "joined_month": joined_month,
        "joined_year": joined_year,
        "trips": trips,
        "trips_day": trips_day,
        "trips_week": trips_week,
        "trips_month": trips_month,
        "trips_year": trips_year,
        "login_user_list": login_user_list,
        "notify_form": AllUserNotificationForm(),
    }

    return render(request, "admin_tools.html", context)


@login_required
def trips_redirect(request):
    """Redirect from /trips/ to /u/username"""
    return redirect("log:user", username=request.user.username)


class UserProfile(ListView):
    """List all of a user's trips and their profile information"""

    model = Trip
    template_name = "user_profile.html"
    context_object_name = "trips"
    slug_field = "username"
    paginate_by = 50
    ordering = ("-start", "pk")

    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        self.user = get_object_or_404(User, username=self.kwargs["username"])

        if not self.user.profile.is_viewable_by(self.request.user):
            raise Http404

    def get_queryset(self):
        qs = Trip.objects.filter(user=self.user).select_related("report")
        qs = qs.order_by(*self.get_ordering())

        if not self.user == self.request.user:
            qs = qs.select_related("user__settings", "user__profile")
            privacy_aware_trips = []
            for trip in qs:
                if trip.is_viewable_by(self.request.user):
                    privacy_aware_trips.append(trip)
            return privacy_aware_trips
        else:
            return qs

    def get_ordering(self):
        allowed_ordering = [
            "start",
            "cave_name",
            "duration",
            "type",
            "vert_dist_up",
            "vert_dist_down",
        ]

        ordering = self.request.GET.get("sort", "")
        if ordering.replace("-", "") in allowed_ordering:
            return (ordering, "pk")

        return self.ordering

    def get_context_data(self):
        context = super().get_context_data()
        context["user"] = self.user
        context["page_title"] = self.get_page_title()

        # GET parameters for pagination and sorting at the same time
        parameters = self.request.GET.copy()
        parameters = parameters.pop("page", True) and parameters.urlencode()
        context["get_parameters"] = parameters

        return context

    def get_page_title(self):
        if self.user.profile.page_title:
            return self.user.profile.page_title
        else:
            return f"{self.user.name}'s trips"


class TripUpdate(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Trip
    form_class = TripForm
    template_name_suffix = "_update_form"
    success_message = "The trip has been updated."

    def get_queryset(self):
        return Trip.objects.filter(user=self.request.user)


class TripDetail(TripContextMixin, DetailView):
    model = Trip

    def get_queryset(self):
        qs = (
            Trip.objects.all()
            .select_related(
                "user",
                "user__profile",
                "user__settings",
            )
            .prefetch_related(
                "comments",
                "likes",
                "user__profile__friends",
                "comments__author__profile",
                "comments__author__settings",
            )
            .annotate(
                comments_count=Count("comments", distinct=True),
                likes_count=Count("likes", distinct=True),
                user_liked=Exists(
                    User.objects.filter(
                        pk=self.request.user.pk, liked_trips=OuterRef("pk")
                    ).only("pk")
                ),
            )
        )
        return qs

    def get_object(self, *args, **kwargs):
        super().get_object(*args, **kwargs)
        if self.object.user == self.request.user:
            return self.object
        else:
            return self.object.sanitise(self.request.user)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["liked_str"] = {
            self.object.pk: self.object.get_liked_str(self.request.user)
        }
        return context


class TripCreate(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Trip
    form_class = TripForm
    template_name_suffix = "_create_form"
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

    def get_initial(self):
        initial = super(TripCreate, self).get_initial()
        initial = initial.copy()
        initial["cave_country"] = self.request.user.profile.country.name
        return initial

    def get_success_url(self):
        if self.request.POST.get("addanother", False):
            return reverse("log:trip_create")
        return super().get_success_url()


class TripDelete(LoginRequiredMixin, View):
    def get(self, request, pk):
        trip = get_object_or_404(Trip, pk=pk)
        if not trip.user == request.user:
            raise Http404
        trip.delete()
        messages.success(
            request,
            f"The trip to {trip.cave_name} has been deleted.",
        )
        return redirect("log:user", username=request.user.username)


class ReportCreate(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = TripReport
    form_class = TripReportForm
    template_name_suffix = "_create_form"
    success_message = "The trip report has been created."
    initial = {
        "pub_date": timezone.localdate,
    }

    def form_valid(self, form):
        candidate = form.save(commit=False)
        candidate.user = self.request.user
        candidate.trip = self.get_trip()
        candidate.save()
        return super().form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["trip"] = self.get_trip()
        return context

    def get_trip(self):
        trip = get_object_or_404(Trip, pk=self.kwargs["pk"])
        if not trip.user == self.request.user:
            raise Http404  # Users can only create reports for their own trips
        return trip

    def get(self, request, *args, **kwargs):
        trip = self.get_trip()
        if trip.has_report:
            return redirect(trip.report.get_absolute_url())

        return super().get(self, request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class ReportDetail(TripContextMixin, DetailView):
    model = TripReport

    def get_queryset(self):
        qs = (
            TripReport.objects.all()
            .select_related(
                "user",
                "user__profile",
                "user__settings",
            )
            .prefetch_related(
                "comments",
                "likes",
                "user__profile__friends",
                "comments__author__profile",
                "comments__author__settings",
            )
            .annotate(
                likes_count=Count("likes", distinct=True),
            )
        )
        return qs


class ReportUpdate(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = TripReport
    form_class = TripReportForm
    template_name_suffix = "_update_form"
    success_message = "The trip report has been updated."

    def get_queryset(self):
        return TripReport.objects.filter(user=self.request.user)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["trip"] = self.get_object().trip
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class ReportDelete(LoginRequiredMixin, View):
    def get(self, request, pk):
        report = get_object_or_404(TripReport, pk=pk)
        if not report.user == request.user:
            raise Http404

        trip = report.trip
        report.delete()
        messages.success(
            request,
            f"The trip report for the trip to {trip.cave_name} has been deleted.",
        )
        return redirect("log:trip_detail", pk=trip.pk)


class AddComment(LoginRequiredMixin, View):
    def post(self, request):
        form = AddCommentForm(self.request, request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.save()
            if form.object.user != request.user:
                form.object.user.notify(
                    f"{request.user} commented on your {form.type_str}",
                    form.object.get_absolute_url(),
                )
            messages.success(
                request,
                "Your comment has been added.",
            )
        else:
            if form.errors.get("content", None):
                for error in form.errors["content"]:
                    messages.error(request, error)
            else:
                messages.error(
                    request,
                    "There was an error adding your comment. Please try again.",
                )
        return redirect(form.object.get_absolute_url())


class HTMXTripComment(LoginRequiredMixin, TemplateView):
    template_name = "includes/comments.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        trip = self.get_object()
        if not trip.is_viewable_by(self.request.user):
            raise Http404

        initial = {"pk": trip.pk, "type": "trip"}
        context["add_comment_form"] = AddCommentForm(self.request, initial=initial)
        context["display_hide_button"] = True
        context["object"] = trip
        return context

    def get_object(self):
        trip = Trip.objects.filter(pk=self.kwargs["pk"]).prefetch_related(
            "comments",
            "comments__author",
            "comments__author__settings",
            "comments__author__profile",
        )
        return trip.first()


class DeleteComment(LoginRequiredMixin, View):
    def get(self, request, pk):
        comment = get_object_or_404(Comment, pk=pk)
        if comment.author == request.user or request.user.is_superuser:
            comment.delete()
            messages.success(
                request,
                "The comment has been deleted.",
            )
        else:
            raise Http404
        return redirect(comment.content_object.get_absolute_url())


class TripLikeToggle(LoginRequiredMixin, TemplateView):
    """HTMX view for toggling a trip like"""

    template_name = "includes/htmx_trip_like.html"

    def get(self, request, pk):
        trip = self.get_object(request, pk)
        if not trip or not trip.is_viewable_by(request.user):
            raise Http404

        if trip.user_liked:
            trip.likes.remove(request.user)
            trip.user_liked = False
        else:
            trip.likes.add(request.user)
            trip.user_liked = True

        liked_str = {trip.pk: trip.get_liked_str(request.user)}

        context = {
            "trip": trip,
            "liked_str": liked_str,
        }

        return self.render_to_response(context)

    def get_object(self, request, pk):
        return (
            Trip.objects.filter(pk=pk)
            .annotate(
                user_liked=Exists(
                    User.objects.filter(
                        pk=request.user.pk, liked_trips=OuterRef("pk")
                    ).only("pk")
                )
            )
            .first()
        )
