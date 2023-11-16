from comments.forms import NewsCommentForm
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView

from .models import FAQ
from .models import News
from .models import News as NewsModel

User = get_user_model()


class Help(TemplateView):
    template_name = "core/help.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["faqs"] = FAQ.objects.all().order_by("question")
        return context


class NewsList(ListView):
    template_name = "core/news.html"
    model = News
    context_object_name = "news"
    paginate_by = 4

    def get_queryset(self):
        return News.objects.all().order_by("-posted_at")


class NewsDetail(DetailView):
    model = NewsModel
    template_name = "core/news_detail.html"
    context_object_name = "news"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comment_form"] = NewsCommentForm(self.request, self.object)
        return context


class Healthcheck(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse("OK")


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
