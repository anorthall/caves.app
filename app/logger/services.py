import csv

import boto3
from django.conf import settings
from django.core.paginator import EmptyPage, Paginator
from django.db.models import Case, Count, Exists, OuterRef, Q, Value, When
from django.http import HttpResponse
from django.utils import timezone
from django.utils.timezone import localtime as lt
from users.models import CavingUser

from .models import Trip, TripPhoto
from .templatetags.logger_tags import distformat

User = CavingUser


def trip_search(*, terms, for_user, search_user=None, limit=500):
    """Search through trips and return a list of results"""
    if not terms:
        return Trip.objects.none()

    if search_user:
        results = Trip.objects.filter(user=search_user)
    else:
        friends = for_user.friends.all()
        results = Trip.objects.filter(
            Q(user=for_user) | Q(user__in=friends) | Q(privacy=Trip.PUBLIC)
        )

    results = results.filter(
        Q(cave_name__unaccent__trigram_similar=terms)
        | Q(cave_entrance__unaccent__trigram_similar=terms)  # noqa W504
        | Q(cave_exit__unaccent__trigram_similar=terms)  # noqa W504
        | Q(cave_region__unaccent__icontains=terms)  # noqa W504
        | Q(cave_country__unaccent__iexact=terms)  # noqa W504
        | Q(cavers__unaccent__icontains=terms)  # noqa W504
    ).order_by("-start")[:limit]

    results = results.select_related("user").prefetch_related("user__friends")

    # Remove trips that the user doesn't have permission to view
    sanitised_results = [x for x in results if x.is_viewable_by(for_user)]
    return sanitised_results


def generate_s3_presigned_post(upload_path, content_type, max_bytes=10485760):
    """Generate a presigned post URL for uploading to AWS S3"""
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
            ["content-length-range", 1, max_bytes],
        ],
        ExpiresIn=expires_in,
    )

    if not aws_response:
        raise IOError("Failed to generate presigned post")

    return aws_response


def generate_csv_export(user):
    """Generate CSV export for a QuerySet of Trips"""
    qs = user.trips.all()
    if not qs:
        raise Trip.DoesNotExist("No trips to export")

    timestamp = timezone.now().strftime("%Y-%m-%d-%H%M")
    filename = f"{user.username}-trips-{timestamp}.csv"
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
    units = user.units  # Distance units
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

    return response


def get_trips_context(request, ordering, page=1):
    """
    Return a paginated list of trips that the user has permission to view
    Intended for use in the trip feed
    """
    friends = request.user.friends.all()

    trips = (
        Trip.objects.filter(Q(user__in=friends) | Q(user=request.user))
        .select_related("user")
        .prefetch_related("photos", "likes", "user__friends")
        .annotate(
            likes_count=Count("likes", distinct=True),
            user_liked=Exists(
                User.objects.filter(
                    pk=request.user.pk, liked_trips=OuterRef("pk")
                ).only("pk")
            ),
            has_photos=Exists(TripPhoto.objects.filter(trip=OuterRef("pk")).only("pk")),
            photo_count=Count("photos", distinct=True),
            more_than_five_photos=Case(
                When(photo_count__gt=5, then=Value(True)),
            ),
        )
    ).order_by(ordering)[:100]

    # Remove trips that the user does not have permission to view.
    sanitised_trips = [x for x in trips if x.is_viewable_by(request.user)]

    try:
        paginated_trips = Paginator(
            object_list=sanitised_trips, per_page=10, allow_empty_first_page=False
        ).page(page)
    except EmptyPage:
        return []

    return paginated_trips


def get_liked_str_context(request, trips):
    """Return a dictionary of liked strings for each trip
    This dictionary will be used in the includes/htmx_trip_like.html template
    """
    friends = request.user.friends.all()
    liked_str_index = {}
    for trip in trips:
        liked_str_index[trip.pk] = trip.get_liked_str(request.user, friends)

    return liked_str_index
