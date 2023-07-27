from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.generic import TemplateView, View
from django_ratelimit.decorators import ratelimit

from .services import get_lat_long_from


class UserMap(LoginRequiredMixin, TemplateView):
    template_name = "maps/map.html"


@method_decorator(cache_page(60 * 60 * 24), name="dispatch")
@method_decorator(
    ratelimit(key="user_or_ip", rate="20/m", block=False), name="dispatch"
)
class HTMXGeocoding(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        query = request.POST.get("cave_location")
        if not query or getattr(request, "limited", False):
            return self.render_results(request)

        try:
            lat, lng = get_lat_long_from(query)
            return self.render_results(request, lat, lng)
        except ValueError:
            return self.render_results(request)

    def render_results(self, request, lat=None, lng=None):
        context = {"lat": lat, "lng": lng}
        return render(request, "maps/_htmx_geocoding_results.html", context)
