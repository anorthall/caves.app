import json
from datetime import datetime
from io import BytesIO

import exifread
from core.logging import log_trip_action, log_tripphoto_action
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import BadRequest, PermissionDenied
from django.core.files import File
from django.db.models.fields.files import ImageFieldFile
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.timezone import make_aware
from django.views.generic import FormView, View
from django_ratelimit.decorators import ratelimit
from PIL import Image

from .. import services
from ..forms import PhotoPrivacyForm, TripPhotoForm
from ..models import Trip, TripPhoto, trip_photo_upload_path


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


@method_decorator(
    ratelimit(key="user", rate="500/d", method=ratelimit.UNSAFE), name="dispatch"
)
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

        uppy_upload_path = settings.PHOTOS_STORAGE_LOCATION + "/" + upload_path

        try:
            aws_response = services.generate_s3_presigned_post(
                uppy_upload_path, content_type
            )
        except IOError as e:
            raise BadRequest(e)

        return JsonResponse(aws_response)


class TripPhotosUploadSuccess(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        json_request = json.loads(request.body)
        s3_key = json_request.get("s3Key")
        s3_key = s3_key.replace(settings.PHOTOS_STORAGE_LOCATION + "/", "")
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

        photo.filesize = photo.photo.size
        photo.is_valid = True
        photo.save()
        log_tripphoto_action(request.user, photo, "uploaded", f"{photo.filesize} bytes")
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
            log_tripphoto_action(
                request.user, photo, "updated the caption for", photo.caption
            )
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

        photo.deleted_at = timezone.now()
        photo.save()
        log_tripphoto_action(request.user, photo, "deleted")
        messages.success(request, "The photo has been deleted.")
        return redirect(photo.trip.get_absolute_url())


class TripPhotosDeleteAll(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        trip = get_object_or_404(Trip, uuid=kwargs["uuid"])
        if not trip.user == request.user:
            raise PermissionDenied

        qs = TripPhoto.objects.valid().filter(trip=trip, user=request.user)
        if qs.exists():
            deleted_count = qs.count()
            qs.update(deleted_at=timezone.now())
            messages.success(request, "All photos for the trip have been deleted.")
            log_trip_action(
                request.user,
                trip,
                "deleted all photos for",
                f"{deleted_count} photos deleted",
            )
        else:
            messages.error(request, "There were no photos to delete.")

        return redirect(trip.get_absolute_url())


class TripPhotoFeature(LoginRequiredMixin, View):
    def post(self, request, uuid):
        trip = get_object_or_404(Trip, uuid=uuid)
        if trip.user != request.user:
            raise PermissionDenied

        photo = get_object_or_404(TripPhoto, uuid=request.POST.get("photoUUID"))

        crop = {
            "x": float(request.POST.get("cropX", None)),
            "y": float(request.POST.get("cropY", None)),
            "width": float(request.POST.get("cropWidth", None)),
            "height": float(request.POST.get("cropHeight", None)),
            "rotate": float(request.POST.get("cropRotate", None)),
            "scaleX": float(request.POST.get("cropScaleX", None)),
            "scaleY": float(request.POST.get("cropScaleY", None)),
        }

        if None in crop.values():
            raise BadRequest("Missing crop data")

        img = Image.open(photo.photo.file)
        img = img.rotate(crop["rotate"]).crop(
            (
                int(crop["x"]),
                int(crop["y"]),
                int(crop["x"] + crop["width"]),
                int(crop["y"] + crop["height"]),
            )
        )

        if img.width > 1800 or img.height > 800:
            # We want a max of 1800x800 to display at 900x400 on retina screens
            img = img.resize((1800, 800))

        blob = BytesIO()
        img.save(blob, "JPEG", quality=70)
        featured_photo = TripPhoto.objects.create(
            trip=trip,
            user=request.user,
            photo=File(blob, "featured.jpg"),
            is_valid=True,
            photo_type=TripPhoto.PhotoTypes.FEATURED,
            filesize=blob.getbuffer().nbytes,
        )
        trip.featured_photo = featured_photo
        trip.save()

        log_trip_action(request.user, trip, "featured", featured_photo)
        messages.success(request, "The featured photo has been updated.")
        return redirect(trip.get_absolute_url())


class TripPhotoUnsetFeature(LoginRequiredMixin, View):
    def post(self, request, uuid):
        trip = get_object_or_404(Trip, uuid=uuid)
        if not trip.user == request.user:
            raise PermissionDenied

        trip.featured_photo.deleted_at = timezone.now()
        trip.featured_photo.save()

        trip.featured_photo = None
        trip.save()

        log_trip_action(request.user, trip, "deleted featured photo")
        messages.success(
            request,
            "The featured photo has been unset.",
        )
        return redirect(trip.get_absolute_url())
