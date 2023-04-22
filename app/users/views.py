from django.conf import settings
from django.contrib import auth, messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView, View

from .emails import (
    send_email_change_notification,
    send_email_change_verification,
    send_verify_email,
)
from .forms import (
    AddFriendForm,
    PasswordChangeForm,
    PasswordResetForm,
    ProfileChangeForm,
    ResendVerifyEmailForm,
    SetPasswordForm,
    SettingsChangeForm,
    UserChangeEmailForm,
    UserChangeForm,
    UserCreationForm,
    VerifyEmailForm,
)
from .models import FriendRequest, Notification
from .verify import generate_token

User = get_user_model()


class PasswordResetView(SuccessMessageMixin, auth.views.PasswordResetView):
    template_name = "password_reset.html"
    email_template_name = "emails/email_password_reset.html"
    html_email_template_name = "emails/email_html_password_reset.html"
    subject_template_name = "emails/email_password_reset_subject.txt"
    success_url = reverse_lazy("users:login")
    success_message = (
        "If such an email is on record, then a password reset link has been sent."
    )
    form_class = PasswordResetForm
    extra_email_context = {
        "site_root": settings.SITE_ROOT,
    }


class PasswordResetConfirmView(
    SuccessMessageMixin, auth.views.PasswordResetConfirmView
):
    template_name = "password_reset_confirm.html"
    success_url = reverse_lazy("users:account")
    form_class = SetPasswordForm
    post_reset_login = True
    success_message = "Your password has been updated and you are signed in."


class PasswordChangeView(
    LoginRequiredMixin, SuccessMessageMixin, auth.views.PasswordChangeView
):
    """Presents a password change form."""

    template_name = "password_change.html"
    success_url = reverse_lazy("users:account")
    form_class = PasswordChangeForm
    success_message = "Your password has been updated."


def login(request):
    """Log in the user."""
    context = {}
    if request.method == "POST":
        username = request.POST.get("email", None)
        password = request.POST.get("password", None)
        user = auth.authenticate(request, username=username, password=password)
        if user is not None:
            auth.login(request, user)
            messages.success(request, f"Now logged in as {user.email}.")
            return redirect("log:index")
        else:
            messages.error(
                request, "The username and password provided do not match any account."
            )
            context = {
                "login_has_failed": True,  # Displays reset password link
                "no_form_error_alert": True,  # Silences default form error
            }

    if request.user.is_authenticated:
        messages.info(request, f"You are logged in as {request.user.email}.")
        return redirect("log:index")

    return render(request, "login.html", context)


def logout(request):
    """Log out the user."""
    auth.logout(request)
    messages.info(request, "You have been signed out.")
    return redirect("log:index")


class Account(LoginRequiredMixin, TemplateView):
    """View the user's account details."""

    template_name = "account.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user"] = self.request.user
        return context


class AccountUpdate(LoginRequiredMixin, TemplateView):
    """Update the user's account and settings."""

    template_name = "account_update.html"

    def get_context_data(self, **kwargs):
        u = self.request.user
        context = super().get_context_data(**kwargs)
        context["user_form"] = UserChangeForm(instance=u)
        context["settings_form"] = SettingsChangeForm(instance=u.settings)
        context["profile_form"] = ProfileChangeForm(instance=u.profile)
        return context

    def post(self, request, *args, **kwargs):
        u = request.user
        user_form = UserChangeForm(request.POST, instance=u)
        settings_form = SettingsChangeForm(request.POST, instance=u.settings)
        profile_form = ProfileChangeForm(
            request.POST, instance=u.profile, files=request.FILES
        )

        if (
            user_form.is_valid()
            and settings_form.is_valid()
            and profile_form.is_valid()
        ):
            user_form.save()
            settings_form.save()
            profile_form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect("users:account")

        context = self.get_context_data(*args, **kwargs)
        context["user_form"] = user_form
        context["settings_form"] = settings_form
        context["profile_form"] = profile_form
        return render(request, self.template_name, context)


def register(request):
    """Register a user."""
    if request.user.is_authenticated:
        return redirect("users:account")  # Already registered

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Generate verification token and send email
            verify_code = generate_token(user.pk, user.email)
            verify_url = settings.SITE_ROOT + reverse("users:verify-new-account")
            send_verify_email(user.email, user.name, verify_url, verify_code)

            # Redirect to Verify Email page.
            return redirect("users:verify-new-account")
    else:
        form = UserCreationForm()

    return render(request, "register.html", {"form": form})


def verify_new_account(request):
    """Verify a new registration."""
    if request.user.is_authenticated:
        return redirect("log:index")

    if "verify_code" in request.GET:
        form = VerifyEmailForm(request.GET)
        if form.is_valid():
            verified_user = form.user
            verified_user.email = form.email
            verified_user.is_active = True
            verified_user.save()
            auth.login(request, verified_user)
            messages.success(
                request,
                f"Welcome, {verified_user.name}. Your registration has been completed and your email address verified!",
            )
            return redirect("log:index")
    else:
        form = VerifyEmailForm()

    return render(request, "verify_new_account.html", {"form": form})


def resend_verify_email(request):
    """Resend a registration verification email."""
    if request.user.is_authenticated:
        return redirect("log:index")

    if request.method == "POST":
        form = ResendVerifyEmailForm(request.POST)
        form.is_valid()
        if form.user:
            # A valid, unverified user was found. Resend email.
            user = form.user
            verify_code = generate_token(user.pk, user.email)
            verify_url = settings.SITE_ROOT + reverse("users:verify-new-account")
            send_verify_email(user.email, user.name, verify_url, verify_code)
        messages.info(
            request,
            "If the provided email matched an account then the verification email has been resent. Please wait a few minutes and then check your email.",
        )
    else:
        form = ResendVerifyEmailForm()
    return render(request, "verify_resend_email.html", {"form": form})


def verify_email_change(request):
    """Verify an email change code."""
    if "verify_code" in request.GET:
        form = VerifyEmailForm(request.GET)
        if form.is_valid():
            verified_user = form.user
            verified_user.email = form.email  # Set the user's email
            verified_user.save()  # Save the user
            auth.login(request, verified_user)  # Log the user in
            messages.success(
                request,
                f"Your new email address, {form.email}, has been verified.",
            )
            return redirect("users:account")
    else:
        form = VerifyEmailForm()

    return render(request, "verify_email_change.html", {"form": form})


@login_required
def update_email(request):
    """Send an email change code."""
    if request.method == "POST":
        form = UserChangeEmailForm(request.user, request.POST)
        if form.is_valid():
            # Generate verification token and send email
            user = form.user
            new_email = form.cleaned_data["email"]
            verify_code = generate_token(user.pk, new_email)
            verify_url = settings.SITE_ROOT + reverse("users:verify-email-change")
            send_email_change_verification(
                new_email, user.name, verify_url, verify_code
            )

            # Send the security notification email
            send_email_change_notification(user.email, user.name, new_email)

            messages.info(
                request,
                "Please follow the instructions sent to your new email address within 24 hours to complete the change.",
            )
            return redirect("users:verify-email-change")
    else:
        form = UserChangeEmailForm(request.user)

    return render(request, "email_update.html", {"form": form})


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
        if self.request.GET.get("u", None):
            initial = {"user": self.request.GET["u"]}
            form = AddFriendForm(request, initial=initial)
        else:
            form = AddFriendForm(request)

        context = {
            "friends_list": self.request.user.profile.friends.all(),
            "friend_requests": FriendRequest.objects.filter(
                Q(user_from=request.user) | Q(user_to=request.user)
            ).order_by("user_from"),
            "add_friend_form": form,
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
                reverse("users:friends"),
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

        return redirect("users:friends")


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
        return redirect("users:friends")


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
                reverse("users:friends"),
            )
            messages.success(request, f"You are now friends with {f_req.user_from}.")
        else:
            raise Http404
        return redirect("users:friends")


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
        return redirect("users:friends")
