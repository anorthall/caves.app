from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from . import statistics


class Index(LoginRequiredMixin, TemplateView):
    template_name = "stats/index.html"

    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        self.queryset = self.get_queryset()

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stats_yearly"] = statistics.yearly(self.queryset)
        context["stats_most_common"] = statistics.most_common(self.queryset)
        context["stats_biggest_trips"] = statistics.biggest_trips(self.queryset)
        context["stats_averages"] = statistics.averages(self.queryset)
        return context

    def get_queryset(self):
        return self.request.user.trips.all()
