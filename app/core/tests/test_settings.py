from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, tag

from config.django.settings.base import env

TEST_ENV_VAR = "TEST_ENV_VAR_THAT_DOES_NOT_EXIST"


@tag("settings", "fast")
class SettingsTests(SimpleTestCase):
    def test_env_method_raises_exception_when_env_var_not_set(self):
        """Test that env() raises ImproperlyConfigured when env var is not set"""
        with self.assertRaises(ImproperlyConfigured):
            env(TEST_ENV_VAR)

    def test_env_method_allows_empty_strings(self):
        """Test that env() allows empty strings"""
        self.assertEqual(env(TEST_ENV_VAR, ""), "")

    def test_env_method_allows_default_values(self):
        """Test that env() allows default values"""
        self.assertEqual(env(TEST_ENV_VAR, "default"), "default")

    def test_env_method_allows_forced_types(self):
        """Test that env() allows forced types"""
        self.assertEqual(env(TEST_ENV_VAR, "0", force_type=int), 0)
        self.assertEqual(env(TEST_ENV_VAR, "0.0", force_type=float), 0.0)
        self.assertEqual(env(TEST_ENV_VAR, 1, force_type=bool), True)

    def test_env_method_raises_exception_when_forced_type_is_invalid(self):
        """Test that env() raises ImproperlyConfigured when forced type is invalid"""
        with self.assertRaises(ImproperlyConfigured):
            env(TEST_ENV_VAR, "this is a string", force_type=int)
