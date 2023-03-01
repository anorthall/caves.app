from django.shortcuts import render, redirect
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from .admin import UserCreationForm
from .forms import LoginForm


def login(request):
    if request.method == "POST":
        username = request.POST["email"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect("index")
        else:
            error = "The username and password provided did not match any account."
            form = LoginForm(request.POST)
            return render(request, "login.html", {"error": error, "form": form})
    else:
        form = LoginForm()
        return render(request, "login.html", {"form": form})


def logout(request):
    auth_logout(request)
    return redirect("index")


def profile(request):
    return redirect("index")


def register(request):
    form = UserCreationForm()
    rendered_form = form.render("bs5_form.html")
    return render(request, "register.html", {"form": rendered_form})
