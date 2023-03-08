from django.shortcuts import render, redirect
from django.http import HttpResponse


def index(request):
    """
    Index page for the entire website

    Unregistered users will be shown a static welcome page

    Registered users will be shown an interface to add/manage
    recent caving trips.
    """

    # Unregistered/unauthenticated users
    if not request.user.is_authenticated:
        return render(request, "index_unregistered.html")

    # Authenticated users
    context = {
        "user": request.user,
    }
    return render(request, "index.html", context)
