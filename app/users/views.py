from django.shortcuts import render, redirect
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib import messages
from .forms import LoginForm, UserCreationForm, UserChangeForm


def login(request):
    if request.method == "POST":
        username = request.POST["email"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            messages.success(request, f"Now logged in as {user.email}.")
            return redirect("index")
        else:
            form = LoginForm(request.POST)
            messages.error(
                request, "The username and password provided do not match any account."
            )
            return render(request, "login.html", {"form": form})
    else:
        if request.user.is_authenticated:
            msg = f"You are logged in as {request.user.email}."
            messages.info(request, msg)
            return redirect("index")

        form = LoginForm()
        return render(request, "login.html", {"form": form})


def logout(request):
    auth_logout(request)
    messages.info(request, "You have been signed out.")
    return redirect("index")


def profile(request):
    if not request.user.is_authenticated:
        messages.error(request, "You must be logged in to access this page.")
        return redirect("users:login")

    form_template = "bs5_form.html"
    user = request.user

    if request.method == "POST":
        form = UserChangeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(
                request, f"Your details have been updated, {user.first_name}."
            )
        else:
            messages.error(
                request, "Details not updated. Please correct the error(s) below."
            )
    else:
        form = UserChangeForm(instance=user)

    rendered_form = form.render(form_template)
    return render(request, "profile.html", {"form": rendered_form})


def register(request):
    form_template = "bs5_form.html"

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            success_msg = f"Your account has been registered, {user.first_name}. You are now signed in."
            messages.success(request, success_msg)
            return redirect("index")
        else:
            messages.error(
                request, "Registration not successful. Please fix the error(s) below."
            )
    else:
        form = UserCreationForm()

    rendered_form = form.render(form_template)
    return render(request, "register.html", {"form": rendered_form})
