import boto3
from django.conf import settings
from django.core.paginator import EmptyPage, Paginator
from django.db.models import Case, Count, Exists, OuterRef, Q, Value, When
from users.models import CavingUser

from .models import Trip, TripPhoto

User = CavingUser


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
    )

    # There is a behaviour in Django where the following line:
    #        comments_count=Count("comments", distinct=True),
    # will cause the query to take a very long time when no comments exist.
    # I am not sure why this is the case, but the following line will
    # prevent this from happening and hence slowing down tests significantly,
    # at the cost of an extra query.
    if not trips.exists():
        return []

    trips = trips.annotate(
        likes_count=Count("likes", distinct=True),
        comments_count=Count("comments", distinct=True),
        user_liked=Exists(
            User.objects.filter(pk=request.user.pk, liked_trips=OuterRef("pk")).only(
                "pk"
            )
        ),
        has_photos=Exists(
            TripPhoto.objects.valid().filter(trip=OuterRef("pk")).only("pk")
        ),
        photo_count=Count(
            "photos",
            filter=Q(photos__is_valid=True, photos__deleted_at=None),
            distinct=True,
        ),
        more_than_five_photos=Case(
            When(photo_count__gt=5, then=Value(True)),
        ),
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
