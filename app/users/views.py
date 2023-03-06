from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordChangeView
from django.contrib import messages
from .forms import (
    LoginForm,
    UserCreationForm,
    UserChangeForm,
    PasswordChangeForm,
    VerifyEmailForm,
    UserChangeEmailForm,
)
from .verify import generate_token
from .emails import send_verify_email


class PasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = "change_password.html"
    success_url = reverse_lazy("users:password-done")
    form_class = PasswordChangeForm


@login_required
def password_done(request):
    messages.success(request, "Your password has been updated.")
    return redirect("users:profile")


def login(request):
    if request.method == "POST":
        username = request.POST["email"]
        password = request.POST["password"]
        user = auth.authenticate(request, username=username, password=password)
        if user is not None:
            auth.login(request, user)
            messages.success(request, f"Now logged in as {user.email}.")
            return redirect("index")
        else:
            form = LoginForm(request.POST)
            messages.error(
                request, "The username and password provided do not match any account."
            )
            return render(request, "login.html", {"form": form})

    if request.user.is_authenticated:
        msg = f"You are logged in as {request.user.email}."
        messages.info(request, msg)
        return redirect("index")

    form = LoginForm()
    return render(request, "login.html", {"form": form})


def logout(request):
    auth.logout(request)
    messages.info(request, "You have been signed out.")
    return redirect("index")


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

    return render(request, "update_profile.html", {"form": form})


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
            verify_url = request.build_absolute_uri(reverse("users:verify"))
            send_verify_email(user.email, user.first_name, verify_url, verify_code)

            # Redirect to Verify Email page.
            return redirect("users:verify")
        else:
            messages.error(
                request, "Registration not successful. Please fix the error(s) below."
            )
    else:
        form = UserCreationForm()

    return render(request, "register.html", {"form": form})


def verify_email(request):
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
                f"Hi, {verified_user.first_name}. Your email address, {form.email}, has been verified.",
            )
            return redirect("users:profile")
    else:
        form = VerifyEmailForm()

    return render(request, "verify_email.html", {"form": form})


@login_required
def update_email(request):
    if request.method == "POST":
        form = UserChangeEmailForm(request.user, request.POST)
        if form.is_valid():
            # Generate verification token and send email
            user = form.user
            new_email = form.cleaned_data["email"]
            verify_code = generate_token(user.pk, new_email)
            verify_url = request.build_absolute_uri(reverse("users:verify"))
            send_verify_email(new_email, user.first_name, verify_url, verify_code)

            messages.info(
                request,
                "Please follow the instructions sent to your new email address in order to complete the change.",
            )
            return redirect("users:profile")
    else:
        form = UserChangeEmailForm(request.user)

    return render(request, "update_email.html", {"form": form})
