from django.test import TestCase, override_settings, tag

from ..context_processors import google_analytics


@tag("fast", "context_processors")
class TestContextProcessors(TestCase):
    @override_settings(GOOGLE_ANALYTICS_ID="test-google-analytics-id")
    def test_google_analytics_context_processor_returns_id(self):
        """Test that the Google Analytics context processor returns the correct value"""
        result = google_analytics(None)
        self.assertEqual(result, {"google_analytics_id": "test-google-analytics-id"})

    @override_settings(GOOGLE_ANALYTICS_ID=None)
    def test_google_analytics_context_processor_returns_empty(self):
        """Test that the Google Analytics context processor when setting unset"""
        result = google_analytics(None)
        self.assertEqual(result, {})
