from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .verify import generate_token
from .forms import (
    UserCreationForm,
    UserChangeForm,
    PasswordChangeForm,
    VerifyEmailForm,
    UserChangeEmailForm,
    ResendVerifyEmailForm,
    PasswordResetForm,
    SetPasswordForm,
)
from .emails import (
    send_verify_email,
    send_email_change_verification,
    send_email_change_notification,
)


class PasswordResetView(auth.views.PasswordResetView):
    template_name = "password_reset.html"
    email_template_name = "emails/email_password_reset.html"
    html_email_template_name = "emails/email_html_password_reset.html"
    subject_template_name = "emails/email_password_reset_subject.txt"
    success_url = reverse_lazy("users:password-reset-sent")
    form_class = PasswordResetForm


class PasswordResetConfirmView(auth.views.PasswordResetConfirmView):
    template_name = "password_reset_confirm.html"
    success_url = reverse_lazy("users:password-reset-done")
    form_class = SetPasswordForm
    post_reset_login = True


def password_reset_sent(request):
    messages.info(
        request,
        "If such an email is on record, then a password reset link has been sent.",
    )
    return redirect("users:password-reset")


@login_required
def password_reset_done(request):
    messages.success(request, "Your password has been updated and you are signed in.")
    return redirect("users:profile")


class PasswordChangeView(LoginRequiredMixin, auth.views.PasswordChangeView):
    template_name = "password_change.html"
    success_url = reverse_lazy("users:password-reset-done")
    form_class = PasswordChangeForm


def login(request):
    lhf = False  # Login has not yet failed
    if request.method == "POST":
        username = request.POST["email"]
        password = request.POST["password"]
        user = auth.authenticate(request, username=username, password=password)
        if user is not None:
            auth.login(request, user)
            messages.success(request, f"Now logged in as {user.email}.")
            return redirect("log:index")
        else:
            messages.error(
                request, "The username and password provided do not match any account."
            )
            lhf = True  # Login has failed

    if request.user.is_authenticated:
        messages.info(request, f"You are logged in as {request.user.email}.")
        return redirect("log:index")

    return render(request, "login.html", {"login_has_failed": lhf})


def logout(request):
    auth.logout(request)
    messages.info(request, "You have been signed out.")
    return redirect("log:index")


@login_required
def update(request):
    if request.method == "POST":
        form = UserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(
                request, f"Your details have been updated, {request.user.first_name}."
            )
            return redirect("users:profile")
        else:
            messages.error(
                request, "Details not updated. Please correct the error(s) below."
            )
    else:
        form = UserChangeForm(instance=request.user)

    return render(request, "profile_update.html", {"form": form})


@login_required
def profile(request):
    return render(request, "profile.html", {"user": request.user})


def register(request):
    if request.user.is_authenticated:
        return redirect("users:profile")  # Already registered

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Generate verification token and send email
            verify_code = generate_token(user.pk, user.email)
            verify_url = request.build_absolute_uri(reverse("users:verify-new-account"))
            send_verify_email(user.email, user.first_name, verify_url, verify_code)

            # Redirect to Verify Email page.
            return redirect("users:verify-new-account")
        else:
            messages.error(
                request, "Registration not successful. Please fix the error(s) below."
            )
    else:
        form = UserCreationForm()

    return render(request, "register.html", {"form": form})


def verify_new_account(request):
    if "verify_code" in request.GET:
        form = VerifyEmailForm(request.GET)
        if form.is_valid():
            verified_user = form.user
            verified_user.email = form.email  # Set the user's email
            verified_user.is_active = True  # Set the user to be active
            verified_user.save()  # Save the user
            auth.login(request, verified_user)  # Log the user in
            messages.success(
                request,
                f"Welcome, {verified_user.first_name}. Your registration has been completed and your email address verified!",
            )
            return redirect("users:profile")
    else:
        form = VerifyEmailForm()

    return render(request, "verify_new_account.html", {"form": form})


def resend_verify_email(request):
    if request.user.is_authenticated:
        return redirect("users:profile")

    if request.method == "POST":
        form = ResendVerifyEmailForm(request.POST)
        form.is_valid()
        if form.user:
            # A valid, unverified user was found. Resend email.
            user = form.user
            verify_code = generate_token(user.pk, user.email)
            verify_url = request.build_absolute_uri(reverse("users:verify-new-account"))
            send_verify_email(user.email, user.first_name, verify_url, verify_code)
        messages.info(
            request,
            "If the provided email matched an account then the verification email has been resent. Please wait a few minutes and then check your email.",
        )
    else:
        form = ResendVerifyEmailForm()
    return render(request, "verify_resend_email.html", {"form": form})


def verify_email_change(request):
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
            return redirect("users:profile")
    else:
        form = VerifyEmailForm()

    return render(request, "verify_email_change.html", {"form": form})


@login_required
def update_email(request):
    if request.method == "POST":
        form = UserChangeEmailForm(request.user, request.POST)
        if form.is_valid():
            # Generate verification token and send email
            user = form.user
            new_email = form.cleaned_data["email"]
            verify_code = generate_token(user.pk, new_email)
            verify_url = request.build_absolute_uri(
                reverse("users:verify-email-change")
            )
            send_email_change_verification(
                new_email, user.first_name, verify_url, verify_code
            )

            # Send the security notification email
            send_email_change_notification(user.email, user.first_name, new_email)

            messages.info(
                request,
                "Please follow the instructions sent to your new email address within 24 hours to complete the change.",
            )
            return redirect("users:verify-email-change")
    else:
        form = UserChangeEmailForm(request.user)

    return render(request, "email_update.html", {"form": form})
