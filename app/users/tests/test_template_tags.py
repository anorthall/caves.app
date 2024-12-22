from django.contrib.auth import get_user_model
from django.test import TestCase, tag

from users.templatetags.users_tags import user as user_templatetag

User = get_user_model()


@tag("unit", "fast", "users")
class TemplateTagUnitTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="enabled@user.app",
            username="enabled",
            password="testpassword",
            name="Joe",
        )
        self.user.is_active = True
        self.user.save()

    def test_user_template_tag_with_non_user_object(self):
        """Test the user template tag raises TypeError when passed a non-user object."""
        self.assertRaises(TypeError, user_templatetag, None, None)
