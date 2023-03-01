from django.shortcuts import render, redirect
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib import messages
from .admin import UserCreationForm
from .forms import LoginForm


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
        form = LoginForm()
        return render(request, "login.html", {"form": form})


def logout(request):
    auth_logout(request)
    messages.info(request, "You have been signed out.")
    return redirect("index")


def profile(request):
    messages.info(request, "This page is not yet implemented.")
    return redirect("index")


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
            rendered_form = form.render(form_template)
    else:
        form = UserCreationForm()
        rendered_form = form.render(form_template)

    return render(request, "register.html", {"form": rendered_form})
