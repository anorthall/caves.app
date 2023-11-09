from .models import Notification


def notifications(request):
    if not request.user.is_authenticated:
        return {}

    n_context = {
        "unread": 0,
        "list": [],
    }

    n_list = Notification.objects.filter(user=request.user).order_by("-updated")[:9]
    if bool(n_list):
        for notification in n_list:
            if not notification.read:
                n_context["unread"] += 1
            n_context["list"].append(notification)
    return {"notifications": n_context}
