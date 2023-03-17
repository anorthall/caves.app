from django.test import TestCase
from django.contrib.auth import get_user_model


class TripTestCase(TestCase):
    def setUp(self):
        # Test user to enable trip creation
        user = get_user_model().objects.create_user(
            email="user_test@test.com",
            username="usertestusername",
            password="password",
            first_name="Firstname",
            last_name="Lastname",
        )
        user.is_active = True
        user.save()

    def test_user_privacy(self):
        """Test CavingUser.is_public and CavingUser.is_private"""
        user = get_user_model().objects.get(email="user_test@test.com")

        # Test where Privacy is Private
        user.privacy = get_user_model().PRIVATE
        self.assertEqual(user.privacy, get_user_model().PRIVATE)
        self.assertTrue(user.is_private())
        self.assertFalse(user.is_public())

        # Test where Privacy is Public
        user.privacy = get_user_model().PUBLIC
        self.assertEqual(user.privacy, get_user_model().PUBLIC)
        self.assertFalse(user.is_private())
        self.assertTrue(user.is_public())
