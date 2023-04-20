from .models import Notification


def notifications(request):
    if not request.user.is_authenticated:
        return {}

    notifications = {
        "unread": 0,
        "list": [],
    }

    list = Notification.objects.filter(user=request.user).order_by("-added")[0:5]
    if bool(list):
        for notification in list:
            if not notification.read:
                notifications["unread"] += 1
            notifications["list"].append(notification)
    return {"notifications": notifications}
