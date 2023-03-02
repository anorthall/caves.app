from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordChangeView
from django.contrib import messages
from .forms import LoginForm, UserCreationForm, UserChangeForm, PasswordChangeForm


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
        return redirect("users:profile")

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth.login(request, user)
            success_msg = f"Your account has been registered, {user.first_name}. You are now signed in."
            messages.success(request, success_msg)
            return redirect("index")
        else:
            messages.error(
                request, "Registration not successful. Please fix the error(s) below."
            )
    else:
        form = UserCreationForm()

    return render(request, "register.html", {"form": form})
