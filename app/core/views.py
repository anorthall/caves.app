from django.contrib.auth import get_user_model
from django.views.generic import TemplateView

from .models import FAQ

User = get_user_model()


class Help(TemplateView):
    template_name = "core/help.html"
    extra_context = {"faqs": FAQ.objects.all().order_by("updated")}


class HTTP400(TemplateView):
    template_name = "400.html"


class HTTP403(TemplateView):
    template_name = "403.html"


class HTTP403CSRF(TemplateView):
    template_name = "403_csrf.html"


class HTTP404(TemplateView):
    template_name = "404.html"


class HTTP500(TemplateView):
    template_name = "500.html"
