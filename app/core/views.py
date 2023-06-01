from django.contrib.auth import get_user_model
from django.views.generic import TemplateView

from .models import FAQ

User = get_user_model()


class Help(TemplateView):
    template_name = "help.html"
    extra_context = {"faqs": FAQ.objects.all().order_by("updated")}
