from django.http import HttpRequest
from users.models import CavingUser


def get_user(request: HttpRequest) -> CavingUser:
    assert request.user.is_authenticated
    assert isinstance(request.user, CavingUser)
    return request.user
