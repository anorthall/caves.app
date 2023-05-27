import logger.csv
from core.models import News
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Exists, OuterRef
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.generic import (
    CreateView,
    FormView,
    ListView,
    RedirectView,
    TemplateView,
    UpdateView,
    View,
)
from logger import statistics
from users.models import Notification

from . import feed, services
from .forms import AllUserNotificationForm, TripForm, TripReportForm, TripSearchForm
from .mixins import TripContextMixin, ViewableObjectDetailView
from .models import Trip, TripReport

User = get_user_model()


class Index(TemplateView):
    def get(self, request, *args, **kwargs):
        """Determine if the user is logged in and render the appropriate template"""
        if request.user.is_authenticated:
            context = self.get_authenticated_context(**kwargs)
            return self.render_to_response(context)
        else:
            self.template_name = "index/index_unregistered.html"
            return super().get(request, *args, **kwargs)

    def get_authenticated_context(self, **kwargs):
        """Return the trip feed for a logged in user"""
        context = super().get_context_data(**kwargs)
        context["news"] = self.get_news_context()
        context["ordering"] = self.request.user.feed_ordering
        context["trips"] = feed.get_trips_context(self.request, context["ordering"])
        context["liked_str"] = feed.get_liked_str_context(
            self.request, context["trips"]
        )

        # If there are no trips, show the new user page
        if context["trips"]:
            self.template_name = "index/index_registered.html"
        else:
            self.template_name = "index/index_new_user.html"

        return context

    def get_news_context(self):
        return (
            News.objects.filter(is_published=True, posted_at__lte=timezone.now())
            .prefetch_related("author")
            .order_by("-posted_at")[:3]
        )


class HTMXFeed(LoginRequiredMixin, TemplateView):
    """Paginate the trip feed by rendering more trips via HTMX"""

    template_name = "includes/feed.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ordering"] = self.request.user.feed_ordering
        context["trips"] = feed.get_trips_context(
            request=self.request,
            ordering=context["ordering"],
            page=self.request.GET.get("page", 1),
        )
        context["liked_str"] = feed.get_liked_str_context(
            self.request, context["trips"]
        )
        return context


class SetFeedOrdering(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        """Get the ordering from GET params and save it to the user model
        if it is valid. Return the ordering to be used in the template."""
        allowed_ordering = [User.FEED_ADDED, User.FEED_DATE]
        if self.request.POST.get("sort") in allowed_ordering:
            self.request.user.feed_ordering = self.request.POST.get("sort")
            self.request.user.save()
        return redirect(reverse("log:index"))


class UserProfile(ListView):
    """List all of a user's trips and their profile information"""

    model = Trip
    template_name = "user_profile.html"
    context_object_name = "trips"
    slug_field = "username"
    paginate_by = 50
    ordering = ("-start", "pk")

    def setup(self, *args, **kwargs):
        """Assign self.profile_user and perform permissions checks"""
        super().setup(*args, **kwargs)
        self.profile_user = get_object_or_404(User, username=self.kwargs["username"])
        if not self.profile_user.is_viewable_by(self.request.user):
            raise PermissionDenied

    def get_queryset(self):
        trips = (
            Trip.objects.filter(user=self.profile_user)
            .select_related("report")
            .order_by(*self.get_ordering())
        )

        # Sanitise trips to be privacy aware
        if not self.profile_user == self.request.user:
            sanitised_trips = [x for x in trips if x.is_viewable_by(self.request.user)]
            return sanitised_trips
        else:
            return trips

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
        context["profile_user"] = self.profile_user
        context["page_title"] = self.get_page_title()
        if self.request.user.is_authenticated:
            context["dist_format"] = self.request.user.units
        else:
            context["dist_format"] = User.METRIC

        # TODO: Paginate via HTMX
        # GET parameters for pagination and sorting at the same time
        parameters = self.request.GET.copy()
        parameters = parameters.pop("page", True) and parameters.urlencode()
        context["get_parameters"] = parameters

        return context

    def get_page_title(self):
        if self.profile_user.page_title:
            return self.profile_user.page_title
        else:
            return f"{self.profile_user.name}'s trips"


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
                "likes",
                "likes__friends",
                "user__friends",
            )
            .annotate(
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
            raise PermissionDenied
        trip.delete()
        messages.success(
            request,
            f"The trip to {trip.cave_name} has been deleted.",
        )
        return redirect("log:user", username=request.user.username)


class Search(LoginRequiredMixin, FormView):
    template_name = "search.html"
    form_class = TripSearchForm


class SearchResults(LoginRequiredMixin, View):
    def get(self, request):
        form = TripSearchForm(request.GET)
        if form.is_valid():
            trips = services.trip_search(
                terms=form.cleaned_data["terms"],
                for_user=request.user,
                search_user=form.cleaned_data.get("user", None),
            )
            context = {
                "trips": trips,
                "form": form,
            }
            if len(trips) == 0:
                context["no_results"] = True

            return render(request, "search.html", context)
        else:
            context = {
                "form": form,
                "no_form_error_alert": True,
            }
            return render(request, "search.html", context)


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
            raise PermissionDenied
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
            .prefetch_related("user__friends")
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
            raise PermissionDenied

        trip = report.trip
        report.delete()
        messages.success(
            request,
            f"The trip report for the trip to {trip.cave_name} has been deleted.",
        )
        return redirect("log:trip_detail", pk=trip.pk)


# TODO: Refactor comments
# class AddComment(LoginRequiredMixin, View):
#     def post(self, request):
#         form = AddCommentForm(self.request, request.POST)
#         if form.is_valid():
#             form.save()
#             if form.object.user != request.user:
#                 form.object.user.notify(
#                     f"{request.user} commented on your {form.type_str}",
#                     form.object.get_absolute_url(),
#                 )
#             messages.success(
#                 request,
#                 "Your comment has been added.",
#             )
#         else:
#             if form.errors.get("content", None):
#                 for error in form.errors["content"]:
#                     messages.error(request, error)
#             else:
#                 messages.error(
#                     request,
#                     "There was an error adding your comment. Please try again.",
#                 )
#         if hasattr(form, "object"):
#             return redirect(form.object.get_absolute_url())
#         else:
#             return redirect("log:index")


# class HTMXTripComment(LoginRequiredMixin, TemplateView):
#     template_name = "includes/comments.html"

#     def get_context_data(self, *args, **kwargs):
#         context = super().get_context_data(*args, **kwargs)
#         trip = self.get_trip()

#         initial = {"pk": trip.pk, "type": "trip"}
#         context["add_comment_form"] = AddCommentForm(self.request, initial=initial)
#         context["display_hide_button"] = True
#         context["object"] = trip
#         context["object_owner"] = trip.user
#         return context

#     def get_trip(self):
#         trip = (
#             Trip.objects.filter(pk=self.kwargs["pk"])
#             .prefetch_related("comments", "comments__author")
#             .first()
#         )

#         if not trip or not trip.is_viewable_by(self.request.user):
#             raise PermissionDenied

#         return trip


# class DeleteComment(LoginRequiredMixin, View):
#     def post(self, request, pk):
#         comment = get_object_or_404(Comment, pk=pk)
#         if (
#             comment.author == request.user
#             or comment.content_object.user == request.user  # noqa: W503
#             or request.user.is_superuser  # noqa: W503
#         ):
#             comment.delete()
#             messages.success(
#                 request,
#                 "The comment has been deleted.",
#             )
#         else:
#             raise PermissionDenied
#         return redirect(comment.content_object.get_absolute_url())


class HTMXTripLike(LoginRequiredMixin, TemplateView):
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
            raise PermissionDenied

        return trip


class CSVExport(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return render(request, "export.html")

    def post(self, request, *args, **kwargs):
        try:
            http_response = logger.csv.generate_csv_export(request.user)
        except Trip.DoesNotExist:
            messages.error(request, "You do not have any trips to export.")
            return redirect("log:export")
        return http_response


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


class AdminTools(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_superuser

    def get(self, request, *args, **kwargs):
        login_user_list = User.objects.filter(is_active=True).values_list(
            "email", flat=True
        )
        context = {
            "login_user_list": login_user_list,
            "notify_form": AllUserNotificationForm(),
        }
        return render(request, "admin_tools.html", context)

    def post(self, request, *args, **kwargs):
        if request.POST.get("login_as", False):
            self.process_login_as_form(request)
        elif request.POST.get("notify", False):
            self.process_notify_form(request)
        return self.get(request, *args, **kwargs)

    def process_login_as_form(self, request):
        try:
            user = User.objects.get(email=request.POST["login_as"])
            if user.is_superuser:
                messages.error(request, "Cannot login as a superuser via this page.")
            elif user:
                messages.success(request, f"Now logged in as {user.email}.")
                login(request, user)
                return redirect("log:index")
        except User.DoesNotExist:
            messages.error(request, "User was not found.")

    def process_notify_form(self, request):
        form = AllUserNotificationForm(request.POST)
        if form.is_valid():
            for user in User.objects.all():
                Notification.objects.create(
                    user=user,
                    message=form.cleaned_data["message"],
                    url=form.cleaned_data["url"],
                )
            messages.success(request, "Notifications sent.")


class TripsRedirect(LoginRequiredMixin, RedirectView):
    """Redirect from /trips/ to /u/username"""

    def get_redirect_url(self, *args, **kwargs):
        return reverse("log:user", kwargs={"username": self.request.user.username})
