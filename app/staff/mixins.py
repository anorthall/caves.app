from core.utils import get_user
from django.contrib.auth.mixins import UserPassesTestMixin


class ModeratorRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        user = get_user(self.request)
        return user.is_authenticated and user.is_moderator
