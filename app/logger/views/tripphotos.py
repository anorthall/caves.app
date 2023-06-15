import json
from datetime import datetime

import exifread
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import BadRequest, PermissionDenied
from django.db.models.fields.files import ImageFieldFile
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.timezone import make_aware
from django.views.generic import FormView, View

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

        try:
            aws_response = services.generate_s3_presigned_post(
                upload_path, content_type
            )
        except IOError as e:
            raise BadRequest(e)

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