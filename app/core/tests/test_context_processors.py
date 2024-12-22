from django.test import TestCase, override_settings, tag

from ..context_processors import api_keys


@tag("fast", "context_processors")
class TestContextProcessors(TestCase):
    @override_settings(
        GOOGLE_ANALYTICS_ID="test-google-analytics-id",
        GOOGLE_MAPS_PUBLIC_API_KEY="test-google-maps-api-key",
    )
    def test_api_keys_context_processor(self):
        """Test that the Google Analytics context processor returns the correct value."""
        result = api_keys(None)
        self.assertEqual(
            result,
            {
                "google_analytics_id": "test-google-analytics-id",
                "google_maps_api_key": "test-google-maps-api-key",
            },
        )

    @override_settings(GOOGLE_ANALYTICS_ID=None, GOOGLE_MAPS_PUBLIC_API_KEY=None)
    def test_google_analytics_context_processor_returns_empty(self):
        """Test that the Google Analytics context processor when setting unset."""
        result = api_keys(None)
        self.assertEqual(
            result,
            {
                "google_analytics_id": None,
                "google_maps_api_key": None,
            },
        )
