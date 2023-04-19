from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import TemplateView, View

from .forms import AddFriendForm
from .models import FriendRequest, Notification

User = get_user_model()


@login_required
def notification_redirect(request, pk):
    """Redirect to the URL of a notification."""
    notification = get_object_or_404(Notification, pk=pk)
    if notification.user == request.user:
        notification.read = True
        notification.save()
        return redirect(notification.url)
    else:
        return redirect("log:index")


class FriendListView(LoginRequiredMixin, TemplateView):
    """A view for viewing, adding, and removing friends."""

    template_name = "friends.html"

    def get(self, request):
        """Display the friend list, friend requests, and add friend form"""
        context = {
            "friends_list": self.request.user.profile.friends.all(),
            "friend_requests": FriendRequest.objects.filter(
                Q(user_from=request.user) | Q(user_to=request.user)
            ).order_by("user_from"),
            "add_friend_form": AddFriendForm(self.request),
        }

        return self.render_to_response(context)


class FriendAddView(LoginRequiredMixin, View):
    """A view to send friend requests"""

    def post(self, request):
        """Handle requests to send friend requests"""
        form = AddFriendForm(request, request.POST)
        if form.is_valid():
            user = form.cleaned_data["user"]
            FriendRequest.objects.create(
                user_from=request.user,
                user_to=user,
            )
            user.notify(
                f"{request.user.username} sent you a friend request",
                reverse("social:friends"),
            )
            messages.success(request, f"Friend request sent to {user}.")
        else:
            if form.errors["user"]:
                for error in form.errors["user"]:
                    messages.error(request, error)
            elif form.non_field_errors():
                for error in form.non_field_errors():
                    messages.error(request, error)
            else:
                messages.error(
                    request, "Unable to add friend. Are the details correct?"
                )

        return redirect("social:friends")


class FriendRequestDeleteView(LoginRequiredMixin, View):
    """A view for deleting a friend request"""

    def get(self, request, pk):
        """Handle requests to delete friend requests"""
        f_req = get_object_or_404(FriendRequest, pk=pk)
        if f_req.user_to == request.user or f_req.user_from == request.user:
            f_req.delete()
            messages.success(
                request,
                f"Friend request between {f_req.user_to} and {f_req.user_from} deleted.",
            )
        else:
            raise Http404
        return redirect("social:friends")


class FriendRequestAcceptView(LoginRequiredMixin, View):
    """A view for accepting a friend request"""

    def get(self, request, pk):
        """Handle requests to accept friend requests"""
        f_req = get_object_or_404(FriendRequest, pk=pk)
        if f_req.user_to == request.user:
            f_req.user_from.profile.friends.add(f_req.user_to)
            f_req.user_to.profile.friends.add(f_req.user_from)
            f_req.delete()

            f_req.user_from.notify(
                f"{f_req.user_to.username} accepted your friend request",
                reverse("social:friends"),
            )
            messages.success(request, f"You are now friends with {f_req.user_from}.")
        else:
            raise Http404
        return redirect("social:friends")


class FriendRemoveView(LoginRequiredMixin, View):
    """A view for removing a friend"""

    def get(self, request, username):
        """Handle requests to remove friends"""
        user = get_object_or_404(User, username=username)
        if user in request.user.profile.friends.all():
            request.user.profile.friends.remove(user)
            user.profile.friends.remove(request.user)
            messages.success(request, f"You are no longer friends with {user}.")
        else:
            raise Http404
        return redirect("social:friends")
