from django.views.generic import RedirectView, TemplateView

from .mixins import StaffRequiredMixin


class Dashboard(StaffRequiredMixin, TemplateView):
    template_name = "staff/dashboard.html"


class Index(StaffRequiredMixin, RedirectView):
    pattern_name = "staff:dashboard"
