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
from django.views.generic import CreateView, ListView, TemplateView, UpdateView, View
from logger import statistics
from users.models import Notification

from .forms import AddCommentForm, AllUserNotificationForm, TripForm, TripReportForm
from .mixins import TripContextMixin, ViewableObjectDetailView
from .models import Comment, Trip, TripReport
from .templatetags.distformat import distformat

User = get_user_model()


class Index(TemplateView):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            context = self.get_authenticated_context(**kwargs)
            return self.render_to_response(context)
        else:
            self.template_name = "index/index_unregistered.html"
            return super().get(request, *args, **kwargs)

    def get_authenticated_context(self, **kwargs):
        context = {}
        context["news"] = self._get_news_context()
        context["trips"] = self._get_trips_context()
        context["liked_str"] = self._get_liked_str_context(context["trips"])

        if len(context["trips"]) == 0:
            self.template_name = "index/index_new_user.html"
        else:
            self.template_name = "index/index_registered.html"

        return context

    def _get_news_context(self):
        return (
            News.objects.filter(is_published=True, posted_at__lte=timezone.now())
            .prefetch_related("author")
            .order_by("-posted_at")[:3]
        )

    def _get_trips_context(self):
        friends = self.request.user.friends.all()
        trips = (
            Trip.objects.filter(Q(user__in=friends) | Q(user=self.request.user))
            .select_related("user")
            .prefetch_related("comments", "likes", "user__friends")
            .annotate(
                likes_count=Count("likes", distinct=True),
                comments_count=Count("comments", distinct=True),
                user_liked=Exists(
                    User.objects.filter(
                        pk=self.request.user.pk, liked_trips=OuterRef("pk")
                    ).only("pk")
                ),
            )
        ).order_by("-added")[
            :25
        ]  # TODO: Make this configurable

        # Remove trips that the user does not have permission to view.
        sanitised_trips = [x for x in trips if x.is_viewable_by(self.request.user)]

        return sanitised_trips

    def _get_liked_str_context(self, trips):
        friends = self.request.user.friends.all()
        liked_str_index = {}
        for trip in trips:
            liked_str_index[trip.pk] = trip.get_liked_str(self.request.user, friends)

        return liked_str_index


class UserProfile(ListView):
    """List all of a user's trips and their profile information"""

    model = Trip
    template_name = "user_profile.html"
    context_object_name = "trips"
    slug_field = "username"
    paginate_by = 50
    ordering = ("-start", "pk")

    def setup(self, *args, **kwargs):
        """Assign self.user and perform permissions checks"""
        super().setup(*args, **kwargs)
        self.user = get_object_or_404(User, username=self.kwargs["username"])
        if not self.user.is_viewable_by(self.request.user):
            raise Http404

    def get_queryset(self):
        qs = (
            Trip.objects.filter(user=self.user)
            .select_related("report")
            .order_by(*self.get_ordering())
        )

        # Sanitise trips to be privacy aware
        # TODO: This is done in other views - extract to a mixin
        if not self.user == self.request.user:
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
        if self.request.user.is_authenticated:
            context["dist_format"] = self.request.user.units
        else:
            context["dist_format"] = User.METRIC

        # GET parameters for pagination and sorting at the same time
        parameters = self.request.GET.copy()
        parameters = parameters.pop("page", True) and parameters.urlencode()
        context["get_parameters"] = parameters

        return context

    def get_page_title(self):
        if self.user.page_title:
            return self.user.page_title
        else:
            return f"{self.user.name}'s trips"


class TripUpdate(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Trip
    form_class = TripForm
    template_name_suffix = "_update_form"
    success_message = "The trip has been updated."

    def get_queryset(self):
        return Trip.objects.filter(user=self.request.user)


class TripDetail(TripContextMixin, ViewableObjectDetailView):
    model = Trip

    def get_queryset(self):
        qs = (
            Trip.objects.all()
            .select_related("user", "report")
            .prefetch_related(
                "comments",
                "comments__author",
                "likes",
                "likes__friends",
                "user__friends",
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
            friends = self.request.user.friends.all()
        else:
            friends = None

        context["liked_str"] = {
            self.object.pk: self.object.get_liked_str(self.request.user, friends)
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
        initial["cave_country"] = self.request.user.country.name
        return initial

    def get_success_url(self):
        if self.request.POST.get("addanother", False):
            return reverse("log:trip_create")
        return super().get_success_url()


class TripDelete(LoginRequiredMixin, View):
    def post(self, request, pk):
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
            raise Http404
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


class ReportDetail(TripContextMixin, ViewableObjectDetailView):
    model = TripReport

    def get_queryset(self):
        qs = (
            TripReport.objects.all()
            .select_related("user", "trip")
            .prefetch_related(
                "comments",
                "comments__author",
                "user__friends",
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
    def post(self, request, pk):
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
            form.save()
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
        if hasattr(form, "object"):
            return redirect(form.object.get_absolute_url())
        else:
            return redirect("log:index")


class HTMXTripComment(LoginRequiredMixin, TemplateView):
    template_name = "includes/comments.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        trip = self.get_trip()

        initial = {"pk": trip.pk, "type": "trip"}
        context["add_comment_form"] = AddCommentForm(self.request, initial=initial)
        context["display_hide_button"] = True
        context["object"] = trip
        return context

    def get_trip(self):
        trip = (
            Trip.objects.filter(pk=self.kwargs["pk"])
            .prefetch_related("comments", "comments__author")
            .first()
        )

        if not trip or not trip.is_viewable_by(self.request.user):
            raise Http404

        return trip


class DeleteComment(LoginRequiredMixin, View):
    def post(self, request, pk):
        comment = get_object_or_404(Comment, pk=pk)
        if (
            comment.author == request.user
            or comment.content_object.user == request.user  # noqa: W503
            or request.user.is_superuser  # noqa: W503
        ):
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

    def post(self, request, pk):
        trip = self.get_trip(request, pk)

        if trip.user_liked:
            trip.likes.remove(request.user)
            trip.user_liked = False
        else:
            trip.likes.add(request.user)
            trip.user_liked = True

        friends = request.user.friends.all()
        liked_str = {trip.pk: trip.get_liked_str(request.user, friends)}

        context = {
            "trip": trip,
            "liked_str": liked_str,
        }

        return self.render_to_response(context)

    def get_trip(self, request, pk):
        trip = (
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

        if not trip or not trip.is_viewable_by(request.user):
            raise Http404

        return trip


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
    units = request.user.units  # Distance units
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
    if request.user.units == User.IMPERIAL:
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
        "dist_format": request.user.units,
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
        "averages": statistics.trip_averages(trips, request.user.units),
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
        raise Http404  # TODO: Use UserPassesTestMixin

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

    login_user_list = User.objects.filter(is_active=True).values_list(
        "email", flat=True
    )

    context = {
        "login_user_list": login_user_list,
        "notify_form": AllUserNotificationForm(),
    }

    return render(request, "admin_tools.html", context)


@login_required
def trips_redirect(request):
    """Redirect from /trips/ to /u/username"""
    return redirect("log:user", username=request.user.username)
