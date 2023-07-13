from django.contrib.auth.mixins import UserPassesTestMixin


class ModeratorRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_moderator
