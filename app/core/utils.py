from typing import Union

from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from users.models import CavingUser


def get_user(request: HttpRequest) -> Union[AnonymousUser, CavingUser]:
    assert isinstance(request.user, (CavingUser, AnonymousUser))
    return request.user
