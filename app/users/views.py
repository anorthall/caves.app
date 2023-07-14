from django.conf import settings
from django.contrib import auth, messages
from django.contrib.auth import get_user_model, update_session_auth_hash
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
    EmailChangeNotificationEmail,
    EmailChangeVerificationEmail,
    FriendRequestAcceptedEmail,
    FriendRequestReceivedEmail,
    NewUserVerificationEmail,
)
from .forms import (
    AddFriendForm,
    AuthenticationForm,
    AvatarChangeForm,
    CustomFieldsForm,
    EmailChangeForm,
    PasswordChangeForm,
    PasswordResetForm,
    ProfileChangeForm,
    ResendVerifyEmailForm,
    SetPasswordForm,
    SettingsChangeForm,
    UserCreationForm,
    VerifyEmailForm,
)
from .models import FriendRequest, Notification
from .verify import generate_token

User = get_user_model()


class PasswordResetView(SuccessMessageMixin, auth_views.PasswordResetView):
    template_name = "users/password_reset.html"
    email_template_name = "emails/password_reset.txt"
    html_email_template_name = "emails/password_reset.html"
    subject_template_name = "emails/password_reset_subject.txt"
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


class Account(LoginRequiredMixin, TemplateView):
    template_name = "users/account.html"


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

            if user.email_friend_requests:
                FriendRequestReceivedEmail(
                    to=user,
                    context={
                        "name": user.name,
                        "requester_name": request.user.name,
                        "url": settings.SITE_ROOT + reverse("users:friends"),
                    },
                ).send()
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

        if f_req.user_from.email_friend_requests:
            FriendRequestAcceptedEmail(
                to=f_req.user_from,
                context={
                    "name": f_req.user_from.name,
                    "accepter_name": f_req.user_to.name,
                    "url": settings.SITE_ROOT + f_req.user_to.get_absolute_url(),
                },
            ).send()

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
    pass


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
            NewUserVerificationEmail(
                to=user,
                context={
                    "name": user.name,
                    "verify_url": verify_url,
                    "verify_code": verify_code,
                },
            ).send()

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
            NewUserVerificationEmail(
                to=user,
                context={
                    "name": user.name,
                    "verify_url": verify_url,
                    "verify_code": verify_code,
                },
            ).send()
        messages.success(
            request,
            "If the provided email matched an account then the verification email "
            "has been resent.",
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


class AccountSettings(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        context = {
            "settings_form": SettingsChangeForm(instance=request.user),
            "email_form": EmailChangeForm(user=request.user),
            "password_form": PasswordChangeForm(user=request.user),
        }
        return render(request, "users/account_settings.html", context)

    def post(self, request, *args, **kwargs):
        settings_form, email_form, password_form = None, None, None

        if request.POST.get("settings_submit"):
            settings_form = SettingsChangeForm(request.POST, instance=request.user)
            if settings_form.is_valid():
                return self.settings_form_valid(request, settings_form)
        elif request.POST.get("email_submit"):
            email_form = EmailChangeForm(request.POST, user=request.user)
            if email_form.is_valid():
                return self.email_form_valid(request, email_form)
        elif request.POST.get("password_submit"):
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                # noinspection PyTypeChecker
                return self.password_form_valid(request, password_form)

        messages.error(request, "Please correct the error(s) below.")
        if not settings_form:
            settings_form = SettingsChangeForm(instance=request.user)
        if not email_form:
            email_form = EmailChangeForm(user=request.user)
        if not password_form:
            password_form = PasswordChangeForm(user=request.user)

        context = {
            "settings_form": settings_form,
            "email_form": email_form,
            "password_form": password_form,
        }
        return render(request, "users/account_settings.html", context)

    def password_form_valid(self, request, form):
        """Save the user's new password"""
        form.save()
        update_session_auth_hash(request, request.user)
        messages.success(request, "Your password has been updated.")
        return redirect("users:account_settings")

    def email_form_valid(self, request, form):
        """Generate verification token and send the email"""
        user = request.user
        new_email = form.cleaned_data["email"]

        # Send verification email
        verify_code = generate_token(user.pk, new_email)
        verify_url = settings.SITE_ROOT + reverse("users:verify_email_change")
        EmailChangeVerificationEmail(
            to=new_email,
            context={
                "name": user.name,
                "verify_url": verify_url,
                "verify_code": verify_code,
            },
        ).send()

        # Send notification email
        EmailChangeNotificationEmail(
            to=user,
            context={
                "name": user.name,
                "new_email": new_email,
                "old_email": user.email,
            },
        ).send()

        messages.success(
            request,
            (
                "Please follow the instructions sent to your new email address "
                "to complete the change."
            ),
        )
        return redirect("users:verify_email_change")

    def settings_form_valid(self, request, form):
        """Save the user's settings"""
        form.save()
        messages.success(request, "Your settings have been updated.")
        return redirect("users:account_settings")


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
