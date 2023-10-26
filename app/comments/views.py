from comments.forms import CommentForm
from comments.models import Comment
from core.logging import log_trip_action
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import TemplateView
from django_ratelimit.decorators import ratelimit
from logger.models import Trip
from users.emails import NewCommentEmail
from users.models import Notification


class AddComment(LoginRequiredMixin, View):
    @method_decorator(ratelimit(key="user", rate="20/h"))
    def post(self, request, uuid):
        trip = get_object_or_404(Trip, uuid=uuid)
        form = CommentForm(self.request, trip, request.POST)

        if not trip.is_viewable_by(self.request.user):
            raise PermissionDenied

        if form.is_valid():
            form.save()

            # Send emails and notifications to followers of the trip
            for user in trip.followers.all():
                # Send the email
                if user.email_comments and user != request.user:
                    NewCommentEmail(
                        to=user.email,
                        context={
                            "name": user.name,
                            "commenter_name": request.user.name,
                            "trip": trip,
                            "comment_content": form.cleaned_data["content"],
                        },
                    ).send()

                # Send the notification
                if user != request.user:
                    try:
                        notification = Notification.objects.get(
                            trip=trip, user=user, type=Notification.TRIP_COMMENT
                        )
                        notification.read = False
                        notification.save()
                    except Notification.DoesNotExist:
                        Notification.objects.create(
                            trip=trip, user=user, type=Notification.TRIP_COMMENT
                        )
            messages.success(
                request,
                "Your comment has been added.",
            )
            log_trip_action(request.user, form.trip, "commented on")
        else:
            if form.errors.get("content", None):
                for error in form.errors["content"]:
                    messages.error(request, error)
            else:
                messages.error(
                    request,
                    "There was an error adding your comment. Please try again.",
                )
        return redirect(form.trip.get_absolute_url())


class HTMXTripComment(LoginRequiredMixin, TemplateView):
    template_name = "comments/_comments_card.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trip = self.get_trip()

        context["comment_form"] = CommentForm(self.request, trip)
        context["trip"] = trip
        return context

    def get_trip(self):
        trip = (
            Trip.objects.filter(uuid=self.kwargs.get("uuid"))
            .prefetch_related("comments", "comments__author")
            .first()
        )

        if not trip or not trip.is_viewable_by(self.request.user):
            raise PermissionDenied

        return trip


class DeleteComment(LoginRequiredMixin, View):
    def post(self, request, uuid):
        comment = get_object_or_404(Comment, uuid=uuid)
        if (
            comment.author == request.user
            or comment.trip.user == request.user  # noqa: W503
            or request.user.is_superuser  # noqa: W503
        ):
            comment.delete()
            messages.success(
                request,
                "The comment has been deleted.",
            )
            log_trip_action(request.user, comment.trip, "deleted a comment on")
        else:
            raise PermissionDenied
        return redirect(comment.trip.get_absolute_url())
