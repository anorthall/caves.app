from core.utils import get_user
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from . import statistics


class Index(LoginRequiredMixin, TemplateView):
    template_name = "stats/index.html"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.queryset = None

    def setup(self, *args, **kwargs):
        super().setup(*args, **kwargs)
        self.queryset = self.get_queryset()

    def get_context_data(self, *args, **kwargs):
        user = get_user(self.request)
        disable_dist = user.disable_distance_statistics
        disable_survey = user.disable_survey_statistics

        context = super().get_context_data(**kwargs)
        context["stats_yearly"] = statistics.yearly(self.queryset)
        context["stats_most_common"] = statistics.most_common(self.queryset)
        context["stats_biggest_trips"] = statistics.biggest_trips(
            self.queryset,
            limit=10,
            disable_dist_stats=disable_dist,
            disable_survey_stats=disable_survey,
        )
        context["stats_averages"] = statistics.averages(
            self.queryset,
            disable_dist_stats=disable_dist,
            disable_survey_stats=disable_survey,
        )
        return context

    def get_queryset(self):
        return get_user(self.request).trips.all()
