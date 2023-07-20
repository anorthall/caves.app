from comments.forms import CommentForm
from comments.models import Comment
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


class AddComment(LoginRequiredMixin, View):
    @method_decorator(ratelimit(key="user", rate="20/h"))
    def post(self, request, uuid):
        trip = get_object_or_404(Trip, uuid=uuid)
        form = CommentForm(self.request, trip, request.POST)

        if not trip.is_viewable_by(self.request.user):
            raise PermissionDenied

        if form.is_valid():
            form.save()
            if form.trip.user != request.user:
                form.trip.user.notify(
                    f"{request.user} commented on your trip.",
                    form.trip.get_absolute_url(),
                )

                if form.trip.user.email_comments:
                    NewCommentEmail(
                        to=form.trip.user.email,
                        context={
                            "name": form.trip.user.name,
                            "commenter_name": request.user.name,
                            "trip": form.trip,
                            "comment_content": form.cleaned_data["content"],
                        },
                    ).send()
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
        return redirect(form.trip.get_absolute_url())


class HTMXTripComment(LoginRequiredMixin, TemplateView):
    template_name = "comments/_comments_card.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
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
        else:
            raise PermissionDenied
        return redirect(comment.trip.get_absolute_url())
