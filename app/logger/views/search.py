from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import FormView
from django_ratelimit.decorators import ratelimit

from .. import search
from ..forms import TripSearchForm


@method_decorator(ratelimit(key="user", rate="60/h", method=ratelimit.UNSAFE), name="dispatch")
class Search(LoginRequiredMixin, FormView):
    form_class = TripSearchForm
    template_name = "logger/search.html"

    def get(self, request, *args, **kwargs):
        if "page" in self.request.GET:
            form = TripSearchForm(self.request.session["search_params"])
            if form.is_valid():
                return self.form_valid(form, store_params=False)

        return super().get(request, *args, **kwargs)

    def form_valid(self, form, store_params=True):
        search_fields = [f for f in form.cleaned_data if form.cleaned_data[f] is True]

        search_user = form.cleaned_data.get("user")
        trips = search.trip_search(
            terms=form.cleaned_data["terms"],
            for_user=self.request.user,
            search_user=search_user,
            type=form.cleaned_data.get("trip_type"),
            fields=search_fields,
        )

        paginator = Paginator(trips, 10, allow_empty_first_page=True)
        page = self.request.GET.get("page", 1)
        trips = paginator.get_page(page)

        context = {
            "trips": trips,
            "form": form,
        }

        if len(trips) == 0:
            messages.error(self.request, "No trips were found with the provided search terms.")

        # Store the POST parameters in the session so that the user can paginate
        # through the results without losing the search.
        if store_params:
            self.request.session["search_params"] = self.request.POST

        return render(self.request, "logger/search.html", context)
