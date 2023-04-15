from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Notification


@login_required
def notification_redirect(request, pk):
    """Redirect to the URL of a notification."""
    notification = get_object_or_404(Notification, pk=pk)
    if notification.user == request.user:
        notification.read = True
        notification.save()
        return redirect(notification.url)
    else:
        return redirect("log:index")
