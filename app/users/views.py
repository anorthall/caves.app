from django.conf import settings
from django.contrib import auth, messages
from django.contrib.auth import get_user_model
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import FormView, ListView, TemplateView, View

from .emails import (
    send_email_change_notification,
    send_email_change_verification,
    send_verify_email,
)
from .forms import (
    AddFriendForm,
    AuthenticationForm,
    AvatarChangeForm,
    CustomFieldsForm,
    PasswordChangeForm,
    PasswordResetForm,
    ProfileChangeForm,
    ResendVerifyEmailForm,
    SetPasswordForm,
    SettingsChangeForm,
    UserChangeEmailForm,
    UserCreationForm,
    VerifyEmailForm,
)
from .models import FriendRequest, Notification
from .verify import generate_token

User = get_user_model()


class PasswordResetView(SuccessMessageMixin, auth_views.PasswordResetView):
    template_name = "users/crispy_form_center.html"
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
    extra_context = {
        "title": "Reset your password",
    }


class PasswordResetConfirmView(
    SuccessMessageMixin, auth_views.PasswordResetConfirmView
):
    template_name = "users/password_reset_confirm.html"
    success_url = reverse_lazy("users:account_detail")
    form_class = SetPasswordForm
    post_reset_login = True
    success_message = "Your password has been updated and you are signed in."
    extra_context = {
        "title": "Set your password",
    }


class PasswordChangeView(
    LoginRequiredMixin, SuccessMessageMixin, auth_views.PasswordChangeView
):
    template_name = "users/crispy_form.html"
    extra_context = {"title": "Change your password"}
    success_url = reverse_lazy("users:account_detail")
    form_class = PasswordChangeForm
    success_message = "Your password has been updated."


class Account(LoginRequiredMixin, TemplateView):
    template_name = "users/account.html"


class SettingsUpdate(LoginRequiredMixin, SuccessMessageMixin, FormView):
    template_name = "users/crispy_form.html"
    extra_context = {"title": "Update your account"}
    form_class = SettingsChangeForm
    success_url = reverse_lazy("users:settings_update")
    success_message = "Your settings have been updated."

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


class ProfileUpdate(LoginRequiredMixin, SuccessMessageMixin, FormView):
    template_name = "users/crispy_form.html"
    extra_context = {"title": "Update your profile"}
    form_class = ProfileChangeForm
    success_url = reverse_lazy("users:profile_update")
    success_message = "Your profile has been updated."

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


class AvatarUpdate(LoginRequiredMixin, SuccessMessageMixin, FormView):
    template_name = "users/profile_photo.html"
    form_class = AvatarChangeForm
    success_url = reverse_lazy("users:account_detail")
    success_message = "Your profile picture has been updated."

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.request.user
        return kwargs

    def form_valid(self, form):  # pragma: no cover
        form.save()
        return super().form_valid(form)


class FriendListView(LoginRequiredMixin, TemplateView):
    template_name = "users/friends.html"

    def get(self, request, **kwargs):
        if self.request.GET.get("u"):
            initial = {"user": self.request.GET["u"]}
            form = AddFriendForm(request, initial=initial)
        else:
            form = AddFriendForm(request)

        friend_requests = (
            FriendRequest.objects.filter(
                Q(user_from=request.user) | Q(user_to=request.user)
            )
            .order_by("user_from")
            .select_related(
                "user_from",
                "user_to",
            )
            .prefetch_related(
                "user_from__friends",
                "user_to__friends",
            )
        )

        friends = request.user.friends.all().prefetch_related("friends")
        context = {
            "friends_list": friends,
            "friend_requests": friend_requests,
            "add_friend_form": form,
        }

        return self.render_to_response(context)


class FriendAddView(LoginRequiredMixin, View):
    def post(self, request):
        form = AddFriendForm(request, request.POST)

        if form.is_valid():
            user = form.cleaned_data["user"]
            FriendRequest.objects.create(
                user_from=request.user,
                user_to=user,
            )
            user.notify(
                f"{request.user.name} sent you a friend request",
                reverse("users:friends"),
            )
            messages.success(request, f"Friend request sent to {user}.")
        else:
            if form.errors.get("user"):
                for error in form.errors["user"]:
                    messages.error(request, error)
            else:  # pragma: no cover
                messages.error(
                    request, "Unable to add friend. Are the details correct?"
                )

        return redirect("users:friends")


class FriendRequestDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        f_req = get_object_or_404(FriendRequest, pk=pk)
        if f_req.user_to == request.user or f_req.user_from == request.user:
            f_req.delete()
            messages.success(
                request,
                f"Friend request between {f_req.user_to} and {f_req.user_from} "
                "deleted.",
            )
        else:
            raise PermissionDenied
        return redirect("users:friends")


class FriendRequestAcceptView(LoginRequiredMixin, View):
    def post(self, request, pk):
        f_req = get_object_or_404(FriendRequest, pk=pk)
        if not f_req.user_to == request.user:
            raise PermissionDenied

        f_req.user_from.friends.add(f_req.user_to)
        f_req.user_to.friends.add(f_req.user_from)
        f_req.delete()
        f_req.user_from.notify(
            f"{f_req.user_to.name} accepted your friend request",
            reverse("users:friends"),
        )
        messages.success(request, f"You are now friends with {f_req.user_from}.")
        return redirect("users:friends")


class FriendRemoveView(LoginRequiredMixin, View):
    def post(self, request, username):
        user = get_object_or_404(User, username=username)
        if user not in request.user.friends.all():
            raise Http404

        request.user.friends.remove(user)
        user.friends.remove(request.user)
        messages.success(request, f"You are no longer friends with {user}.")
        return redirect("users:friends")


class Login(SuccessMessageMixin, auth_views.LoginView):
    template_name = "users/login.html"
    success_message = "You are now logged in."
    form_class = AuthenticationForm
    redirect_authenticated_user = True

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context["no_form_error_alert"] = True  # Silences messages.html
        return context


class Logout(LoginRequiredMixin, auth_views.LogoutView):
    def dispatch(self, *args, **kwargs):
        result = super().dispatch(*args, **kwargs)
        messages.success(self.request, "You have been logged out.")
        return result


def register(request):
    if request.user.is_authenticated:
        return redirect("users:account_detail")

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Generate verification token and send email
            verify_code = generate_token(user.pk, user.email)
            verify_url = settings.SITE_ROOT + reverse("users:verify_new_account")
            send_verify_email(user.email, user.name, verify_url, verify_code)

            # Redirect to Verify Email page.
            return redirect("users:verify_new_account")
    else:
        form = UserCreationForm()

    return render(request, "users/register.html", {"form": form})


def verify_new_account(request):
    """Verify the email address of a new account"""
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
                f"Welcome, {verified_user.name}. Your registration has been completed "
                "and your email address verified!",
            )
            return redirect("log:index")
    else:
        form = VerifyEmailForm()

    return render(request, "users/verify_new_account.html", {"form": form})


def resend_verify_email(request):
    """Resend a verification email for a new account"""
    if request.user.is_authenticated:
        return redirect("log:index")

    if request.method == "POST":
        form = ResendVerifyEmailForm(request.POST)
        form.is_valid()
        if form.user:
            # A valid, unverified user was found. Resend email.
            user = form.user
            verify_code = generate_token(user.pk, user.email)
            verify_url = settings.SITE_ROOT + reverse("users:verify_new_account")
            send_verify_email(user.email, user.name, verify_url, verify_code)
        messages.info(
            request,
            "If the provided email matched an account then the verification email "
            "has been resent. Please wait a few minutes and then check your email.",
        )
    else:
        form = ResendVerifyEmailForm()
    return render(request, "users/verify_resend_email.html", {"form": form})


class VerifyEmailChange(SuccessMessageMixin, LoginRequiredMixin, FormView):
    form_class = VerifyEmailForm
    template_name = "users/verify_email_change.html"
    success_message = "Your email address has been verified and updated."
    success_url = reverse_lazy("users:account_detail")

    def form_valid(self, form):
        """Set the user's new email address and log them in"""
        verified_user = form.user
        verified_user.email = form.email
        verified_user.save()
        auth.login(self.request, verified_user)
        return super().form_valid(form)

    def get_initial(self, *args, **kwargs):
        """Add the verify_code from the URL params to the form's initial data"""
        initial = super().get_initial().copy()
        initial["verify_code"] = self.request.GET.get("verify_code")
        return initial


class UpdateEmail(SuccessMessageMixin, LoginRequiredMixin, FormView):
    template_name = "users/crispy_form.html"
    extra_context = {"title": "Change your email address"}
    form_class = UserChangeEmailForm
    success_url = reverse_lazy("users:verify_email_change")
    success_message = (
        "Please follow the instructions sent to your new email address within "
        "24 hours to complete the change."
    )

    def form_valid(self, form, *args, **kwargs):
        """Generate verification token and send the email"""
        user = form.user
        new_email = form.cleaned_data["email"]
        verify_code = generate_token(user.pk, new_email)
        verify_url = settings.SITE_ROOT + reverse("users:verify_email_change")
        send_email_change_verification(new_email, user.name, verify_url, verify_code)
        send_email_change_notification(user.email, user.name, new_email)
        return super().form_valid(form)

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class NotificationRedirect(LoginRequiredMixin, View):
    def get(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk)
        if not notification.user == request.user:
            raise PermissionDenied

        notification.read = True
        notification.save()
        return redirect(notification.url)


class CustomFieldsUpdate(LoginRequiredMixin, SuccessMessageMixin, FormView):
    template_name = "users/custom_fields.html"
    form_class = CustomFieldsForm
    success_message = "Your custom fields have been updated."
    success_url = reverse_lazy("users:custom_fields_update")

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


class NotificationsList(LoginRequiredMixin, ListView):
    model = Notification
    template_name = "users/notifications.html"
    context_object_name = "all_notifications"
    paginate_by = 10

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by("-added")


class NotificationMarkAllRead(LoginRequiredMixin, View):
    def get(self, request):
        Notification.objects.filter(user=request.user, read=False).update(read=True)
        messages.success(request, "All notifications marked as read.")
        return redirect("users:notifications")
