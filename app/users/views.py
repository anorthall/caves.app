from django.conf import settings
from django.contrib import auth, messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordResetConfirmView,
    PasswordResetView,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import FormView, TemplateView, View

from .emails import (
    send_email_change_notification,
    send_email_change_verification,
    send_verify_email,
)
from .forms import (
    AddFriendForm,
    AuthenticationForm,
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


class PasswordResetView(SuccessMessageMixin, PasswordResetView):
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


class PasswordResetConfirmView(SuccessMessageMixin, PasswordResetConfirmView):
    template_name = "password_reset_confirm.html"
    success_url = reverse_lazy("users:account_detail")
    form_class = SetPasswordForm
    post_reset_login = True
    success_message = "Your password has been updated and you are signed in."


class PasswordChangeView(LoginRequiredMixin, SuccessMessageMixin, PasswordChangeView):
    template_name = "password_change.html"
    success_url = reverse_lazy("users:account_detail")
    form_class = PasswordChangeForm
    success_message = "Your password has been updated."


class Account(LoginRequiredMixin, TemplateView):
    """View the user's account details."""

    template_name = "account.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class AccountUpdate(LoginRequiredMixin, TemplateView):
    """Update the user's account and settings."""

    template_name = "account_update.html"

    def get_context_data(self, **kwargs):
        u = self.request.user
        context = super().get_context_data(**kwargs)
        context["user_form"] = UserChangeForm(instance=u)
        context["settings_form"] = SettingsChangeForm(instance=u)
        context["profile_form"] = ProfileChangeForm(instance=u)
        return context

    def post(self, request, *args, **kwargs):
        u = request.user
        u_form = UserChangeForm(request.POST, instance=u)
        s_form = SettingsChangeForm(request.POST, instance=u)
        p_form = ProfileChangeForm(request.POST, instance=u, files=request.FILES)

        if u_form.is_valid() and s_form.is_valid() and p_form.is_valid():
            u_form.save()
            s_form.save()
            p_form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect("users:account_update")

        context = self.get_context_data(*args, **kwargs)
        context["user_form"] = u_form
        context["settings_form"] = s_form
        context["profile_form"] = p_form
        return render(request, self.template_name, context)


class FriendListView(LoginRequiredMixin, TemplateView):
    template_name = "friends.html"

    def get(self, request):
        if self.request.GET.get("u", None):
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
            if form.errors.get("user", None):
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


class Login(SuccessMessageMixin, LoginView):
    template_name = "login.html"
    success_message = "You are now logged in."
    form_class = AuthenticationForm
    redirect_authenticated_user = True

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["no_form_error_alert"] = True  # Silences messages.html
        return context


class Logout(LoginRequiredMixin, LogoutView):
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

    return render(request, "register.html", {"form": form})


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

    return render(request, "verify_new_account.html", {"form": form})


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
    return render(request, "verify_resend_email.html", {"form": form})


class VerifyEmailChange(SuccessMessageMixin, LoginRequiredMixin, FormView):
    form_class = VerifyEmailForm
    template_name = "verify_email_change.html"
    success_message = "Your email address has been verified and updated."
    success_url = reverse_lazy("users:account_detail")

    def form_valid(self, form, *args, **kwargs):
        """Set the user's new email address and log them in"""
        verified_user = form.user
        verified_user.email = form.email
        verified_user.save()
        auth.login(self.request, verified_user)
        return super().form_valid(form, *args, **kwargs)

    def get_initial(self, *args, **kwargs):
        """Add the verify_code from the URL params to the form's initial data"""
        initial = super().get_initial(*args, **kwargs)
        initial["verify_code"] = self.request.GET.get("verify_code", "")
        return initial.copy()


class UpdateEmail(SuccessMessageMixin, LoginRequiredMixin, FormView):
    form_class = UserChangeEmailForm
    template_name = "email_update.html"
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
        return super().form_valid(form, *args, **kwargs)

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
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
