from django.contrib.auth import get_user_model
from django.views.generic import DetailView, TemplateView

from .models import FAQ
from .models import News as NewsModel

User = get_user_model()


class Help(TemplateView):
    template_name = "core/help.html"
    extra_context = {"faqs": FAQ.objects.all().order_by("question")}


class News(TemplateView):
    template_name = "core/news.html"
    extra_context = {
        "news": NewsModel.objects.filter(is_published=True).order_by("-posted_at")
    }


class NewsDetail(DetailView):
    model = NewsModel
    template_name = "core/news_detail.html"
    context_object_name = "news"


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
