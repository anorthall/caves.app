from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View
from django.views.generic import FormView

from .. import services
from ..forms import TripSearchForm


class Search(LoginRequiredMixin, FormView):
    template_name = "logger/search.html"
    form_class = TripSearchForm


class SearchResults(LoginRequiredMixin, View):
    def get(self, request):
        form = TripSearchForm(request.GET)
        if form.is_valid():
            trips = services.trip_search(
                terms=form.cleaned_data["terms"],
                for_user=request.user,
                search_user=form.cleaned_data.get("user", None),
            )
            context = {
                "trips": trips,
                "form": form,
            }
            if len(trips) == 0:
                messages.error(
                    request, "No trips were found with the provided search terms."
                )

            return render(request, "logger/search.html", context)
        else:
            context = {
                "form": form,
                "no_form_error_alert": True,
            }
            return render(request, "logger/search.html", context)
