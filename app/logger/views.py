import json
from datetime import datetime

import boto3
import exifread
import logger.csv
from core.utils import get_user
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import BadRequest, PermissionDenied
from django.db.models import Count, Exists, OuterRef
from django.db.models.fields.files import ImageFieldFile
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import SafeString
from django.utils.timezone import make_aware
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
from stats import statistics as new_stats

from . import feed, services
from .forms import (
    PhotoPrivacyForm,
    TripForm,
    TripPhotoForm,
    TripReportForm,
    TripSearchForm,
)
from .mixins import ReportObjectMixin, TripContextMixin, ViewableObjectDetailView
from .models import Trip, TripPhoto, TripReport, trip_photo_upload_path

User = get_user_model()


class Index(TemplateView):
    def get(self, request, *args, **kwargs):
        """Determine if the user is logged in and render the appropriate template"""
        if request.user.is_authenticated:
            context = self.get_authenticated_context(**kwargs)
            return self.render_to_response(context)
        else:
            self.template_name = "core/index_unregistered.html"
            return super().get(request, *args, **kwargs)

    def get_authenticated_context(self, **kwargs):
        """Return the trip feed for a logged in user"""
        context = super().get_context_data(**kwargs)
        context["ordering"] = get_user(self.request).feed_ordering
        context["trips"] = feed.get_trips_context(self.request, context["ordering"])
        context["liked_str"] = feed.get_liked_str_context(
            self.request, context["trips"]
        )

        # If there are no trips, show the new user page
        if context["trips"]:
            self.template_name = "logger/social_feed.html"
        else:
            self.template_name = "core/new_user.html"

        return context


class UserProfile(ListView):
    """List all of a user's trips and their profile information"""

    model = Trip
    template_name = "logger/profile.html"
    context_object_name = "trips"
    slug_field = "username"
    paginate_by = 50
    ordering = ("-start", "pk")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.profile_user = None

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
            return ordering, "pk"

        return self.ordering

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["profile_user"] = self.profile_user
        context["page_title"] = self.get_page_title()
        context["show_cavers"] = self.profile_user.show_cavers_on_trip_list
        if self.profile_user.public_statistics:
            context["stats"] = new_stats.yearly(self.get_queryset())

        # This code provides the current GET parameters as a context variable
        # so that when a pagination link is clicked, the GET parameters are
        # preserved (for sorting).
        parameters = self.request.GET.copy()
        parameters = parameters.pop("page", True) and parameters.urlencode()
        context["get_parameters"] = parameters

        return context

    def get_page_title(self):
        if self.profile_user.page_title:
            return self.profile_user.page_title
        else:
            return f"{self.profile_user.name}'s trips"


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
        initial = super(TripCreate, self).get_initial()
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


class TripPhotos(LoginRequiredMixin, SuccessMessageMixin, FormView):
    template_name = "logger/trip_photos.html"
    form_class = PhotoPrivacyForm
    success_message = "The photo privacy setting for this trip has been updated."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.trip = None

    def dispatch(self, request, *args, **kwargs):
        self.trip = get_object_or_404(Trip, uuid=self.kwargs["uuid"])
        if not self.trip.user == request.user:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.trip
        return kwargs

    def get_success_url(self):
        return reverse("log:trip_photos", args=[self.trip.uuid])

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context["trip"] = self.trip
        context["object_owner"] = self.trip.user
        return context


class TripPhotosUpload(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        json_request = json.loads(request.body)
        filename = json_request.get("filename")
        content_type = json_request.get("contentType")
        trip_uuid = json_request.get("tripUUID")
        if not filename or not content_type or not trip_uuid:
            raise BadRequest("Missing filename, contentType or tripUUID in request")

        if not content_type.startswith("image/"):
            raise BadRequest("File is not an image")

        try:
            trip = Trip.objects.get(uuid=trip_uuid)
        except Trip.DoesNotExist:
            raise BadRequest("Trip does not exist")

        if not trip.user == request.user:
            raise PermissionDenied

        photo = TripPhoto.objects.create(
            trip=trip,
            user=request.user,
            photo=None,
        )

        upload_path = trip_photo_upload_path(photo, filename)
        photo.photo = ImageFieldFile(photo, photo.photo.field, upload_path)
        photo.save()

        session = boto3.session.Session()
        client = session.client(
            service_name="s3",
            region_name=settings.AWS_S3_REGION_NAME,
            aws_access_key_id=settings.AWS_S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_S3_SECRET_ACCESS_KEY,
        )

        acl = settings.AWS_DEFAULT_ACL
        expires_in = settings.AWS_PRESIGNED_EXPIRY

        aws_response = client.generate_presigned_post(
            settings.AWS_STORAGE_BUCKET_NAME,
            upload_path,
            Fields={
                "acl": acl,
                "Content-Type": content_type,
            },
            Conditions=[
                {"acl": acl},
                {"Content-Type": content_type},
                ["content-length-range", 1, 10485760],
            ],
            ExpiresIn=expires_in,
        )

        if not aws_response:
            raise BadRequest("Failed to generate presigned post")

        return JsonResponse(aws_response)


class TripPhotosUploadSuccess(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        json_request = json.loads(request.body)
        s3_key = json_request.get("s3Key")
        trip_uuid = json_request.get("tripUUID")

        if not s3_key or not trip_uuid:
            raise BadRequest("Missing s3Key or tripUUID in request")

        try:
            trip = Trip.objects.get(uuid=trip_uuid)
        except Trip.DoesNotExist:
            raise BadRequest("Trip does not exist")

        try:
            photo = TripPhoto.objects.get(photo__endswith=s3_key)
        except TripPhoto.DoesNotExist:
            raise BadRequest("Trip photo does not exist")

        if not trip.user == request.user or not photo.trip == trip:
            raise PermissionDenied

        with photo.photo.open("rb") as f:
            tags = exifread.process_file(f, stop_tag="EXIF DateTimeOriginal")
            if "EXIF DateTimeOriginal" in tags:
                photo.taken = make_aware(
                    datetime.strptime(
                        str(tags["EXIF DateTimeOriginal"]), "%Y:%m:%d %H:%M:%S"
                    )
                )

        photo.is_valid = True
        photo.save()
        return JsonResponse({"success": True})


class TripPhotosUpdate(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        photo = get_object_or_404(TripPhoto, uuid=request.POST["photoUUID"])
        if not photo.user == request.user:
            raise PermissionDenied

        form = TripPhotoForm(request.POST, instance=photo)
        if form.is_valid():
            photo = form.save()
            messages.success(request, "The photo has been updated.")
            return redirect(photo.trip.get_absolute_url())
        else:
            messages.error(
                request,
                "The photo could not be updated. Was the caption over 200 characters?",
            )
            return redirect(photo.trip.get_absolute_url())


class TripPhotosDelete(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        photo = get_object_or_404(TripPhoto, uuid=request.POST["photoUUID"])
        if not photo.user == request.user:
            raise PermissionDenied

        redirect_url = photo.trip.get_absolute_url()
        photo.delete()
        messages.success(request, "The photo has been deleted.")
        return redirect(redirect_url)


class TripPhotosDeleteAll(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        trip = get_object_or_404(Trip, uuid=kwargs["uuid"])
        if not trip.user == request.user:
            raise PermissionDenied

        qs = TripPhoto.objects.filter(
            trip=trip,
            user=request.user,
        )

        if qs.exists():
            qs.delete()
            messages.success(request, "All photos for the trip have been deleted.")
        else:
            messages.error(request, "There were no photos to delete.")

        return redirect(trip.get_absolute_url())


class ReportCreate(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = TripReport
    form_class = TripReportForm
    template_name = "logger/trip_report_create.html"
    success_message = "The trip report has been created."
    initial = {
        "pub_date": timezone.localdate,
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.trip = None

    def dispatch(self, request, *args, **kwargs):
        self.trip = self.get_trip()
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        candidate = form.save(commit=False)
        candidate.user = self.request.user
        candidate.trip = self.trip
        candidate.save()
        return super().form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context["trip"] = self.trip
        context["object_owner"] = self.trip.user
        return context

    def get_trip(self):
        trip = get_object_or_404(Trip, uuid=self.kwargs["uuid"])
        if not trip.user == self.request.user:
            raise PermissionDenied
        return trip

    def get(self, request, *args, **kwargs):
        if self.trip.has_report:
            return redirect(self.trip.report.get_absolute_url())

        return super().get(self, request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class ReportDetail(ReportObjectMixin, TripContextMixin, ViewableObjectDetailView):
    model = TripReport
    template_name = "logger/trip_report_detail.html"


class ReportUpdate(
    LoginRequiredMixin, ReportObjectMixin, SuccessMessageMixin, UpdateView
):
    model = TripReport
    form_class = TripReportForm
    template_name = "logger/trip_report_update.html"
    success_message = "The trip report has been updated."

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context["trip"] = self.trip
        context["object_owner"] = self.get_object().user
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_object(self, *args, **kwargs):
        obj = super().get_object(*args, **kwargs)
        if obj.user == self.request.user:
            return obj
        raise PermissionDenied


class ReportDelete(LoginRequiredMixin, View):
    def post(self, request, uuid):
        try:
            report = get_object_or_404(Trip, uuid=uuid).report
        except TripReport.DoesNotExist:
            raise Http404

        if not report.user == request.user:
            raise PermissionDenied

        trip = report.trip
        report.delete()
        messages.success(
            request,
            f"The trip report for the trip to {trip.cave_name} has been deleted.",
        )
        return redirect(trip.get_absolute_url())


class SetFeedOrdering(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        """Get the ordering from GET params and save it to the user model
        if it is valid. Return the ordering to be used in the template."""
        allowed_ordering = [User.FEED_ADDED, User.FEED_DATE]
        if self.request.POST.get("sort") in allowed_ordering:
            self.request.user.feed_ordering = self.request.POST.get("sort")
            self.request.user.save()
        return redirect(reverse("log:index"))


class Search(LoginRequiredMixin, FormView):
    template_name = "logger/search.html"
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
                messages.error(
                    request, "No trips were found with the provided search terms."
                )

            return render(request, "logger/search.html", context)
        else:
            context = {
                "form": form,
                "no_form_error_alert": True,
            }
            return render(request, "logger/search.html", context)


class HTMXTripLike(LoginRequiredMixin, TemplateView):
    """HTMX view for toggling a trip like"""

    template_name = "logger/_htmx_trip_like.html"

    def post(self, request, uuid):
        trip = self.get_trip(request, uuid)

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

    def get_trip(self, request, uuid):
        trip = (
            Trip.objects.filter(uuid=uuid)
            .annotate(
                user_liked=Exists(
                    User.objects.filter(
                        pk=request.user.pk, liked_trips=OuterRef("pk")
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


class HTMXTripFeed(LoginRequiredMixin, TemplateView):
    """Render more trips to be inserted into the trip feed via HTMX"""

    template_name = "logger/_feed.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ordering"] = get_user(self.request).feed_ordering
        context["trips"] = feed.get_trips_context(
            request=self.request,
            ordering=context["ordering"],
            page=self.request.GET.get("page", 1),
        )
        context["liked_str"] = feed.get_liked_str_context(
            self.request, context["trips"]
        )
        return context


class CSVExport(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return render(request, "logger/export.html")

    def post(self, request, *args, **kwargs):
        try:
            http_response = logger.csv.generate_csv_export(request.user)
        except Trip.DoesNotExist:
            messages.error(request, "You do not have any trips to export.")
            return redirect("log:export")
        return http_response


@login_required
def user_statistics(request):
    trips = get_user(request).trips
    chart_units = "m"
    if request.units == User.IMPERIAL:
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

    if len(trips) < 5:
        messages.warning(
            request,
            "Full featured statistics are not available as you have added "
            "less than five trips.",
        )

    context = {
        "trips": trips,
        "gte_five_trips": len(trips) >= 5,
        "show_time_charts": show_time_charts,
        "user": request.user,
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
        "averages": statistics.trip_averages(trips, get_user(request).units),
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

    new_version_msg = SafeString(
        "A new version of the statistics page is under development. You can "
        'view it by <a href="/stats/">clicking here</a>.'
    )
    messages.info(request, new_version_msg)
    return render(request, "logger/statistics.html", context)
