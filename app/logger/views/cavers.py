from dal import autocomplete
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count, Max, Sum
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import DetailView, ListView

from ..forms import LinkCaverForm, MergeCaverForm, RenameCaverForm
from ..models import Caver, Trip


class CaverAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Caver.objects.filter(user=self.request.user)

        if self.q:
            qs = qs.filter(name__istartswith=self.q)

        return qs

    def create_object(self, text):
        return self.get_queryset().get_or_create(name=text, user=self.request.user)[0]

    def has_add_permission(self, request):
        return True


class CaverList(LoginRequiredMixin, ListView):
    model = Caver
    template_name = "logger/caver_list.html"
    context_object_name = "cavers"
    paginate_by = 50

    def get_queryset(self):
        return (
            Caver.objects.filter(user=self.request.user)
            .prefetch_related("trip_set")
            .order_by("name")
            .annotate(trip_count=Count("trip", distinct=True))
            .annotate(last_trip_date=Max("trip__start"))
            .annotate(annotated_total_trip_duration=Sum("trip__duration", distinct=True))
        )


class CaverDetail(LoginRequiredMixin, DetailView):
    model = Caver
    template_name = "logger/caver_detail.html"
    context_object_name = "caver"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["trips"] = Trip.objects.filter(cavers=self.object).order_by("-start")
        context["trip_count"] = context["trips"].count()
        context["link_caver_form"] = LinkCaverForm(user=self.request.user)
        context["rename_caver_form"] = RenameCaverForm()
        context["merge_caver_form"] = MergeCaverForm(user=self.request.user, caver=self.object)
        return context

    def get_queryset(self):
        return Caver.objects.filter(user=self.request.user)


class CaverDelete(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        caver = get_object_or_404(Caver, uuid=kwargs["uuid"], user=request.user)
        caver.delete()

        messages.success(request, f"The caver record for {caver.name} has been deleted.")
        return redirect("log:caver_list")


class CaverRename(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        caver = get_object_or_404(Caver, uuid=kwargs["uuid"], user=request.user)
        form = RenameCaverForm(request.POST)

        if form.is_valid():
            new_name = form.cleaned_data["name"]
            caver.name = new_name
            caver.save()
            messages.success(request, f"The caver record for {caver.name} has been updated.")
        else:
            messages.error(
                request,
                form.errors["name"][0],
            )

        return redirect(caver.get_absolute_url())


class CaverLink(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        caver = get_object_or_404(Caver, uuid=kwargs["uuid"], user=request.user)
        form = LinkCaverForm(request.POST, user=request.user)

        if form.is_valid():
            caver.linked_account = form.cleaned_data["account"]
            caver.save()
            messages.success(
                request,
                (
                    f"The caver record for {caver.name} has been linked to "
                    f"@{caver.linked_account.username}."
                ),
            )
        else:
            messages.error(
                request,
                form.errors["account"][0],
            )

        return redirect(caver.get_absolute_url())


class CaverUnlink(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        caver = get_object_or_404(Caver, uuid=kwargs["uuid"], user=request.user)
        caver.linked_account = None
        caver.save()
        messages.success(
            request,
            f"The caver record for {caver.name} has been unlinked.",
        )
        return redirect(caver.get_absolute_url())


class CaverMerge(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        caver = get_object_or_404(Caver, uuid=kwargs["uuid"], user=request.user)
        form = MergeCaverForm(request.POST, user=request.user, caver=caver)

        if form.is_valid():
            merge_caver = form.cleaned_data["caver"]
            if not merge_caver.user == request.user:
                raise PermissionDenied

            if merge_caver == caver:
                messages.error(
                    request,
                    "You cannot merge a caver with itself.",
                )
                return redirect(caver.get_absolute_url())

            with transaction.atomic():
                for trip in merge_caver.trip_set.all():
                    trip.cavers.add(caver)
                    trip.save()

                merge_caver.delete()

            messages.success(
                request,
                f"The caver record for {caver.name} has been merged with {merge_caver.name}.",
            )
        else:
            messages.error(
                request,
                form.errors["caver"][0],
            )

        return redirect(caver.get_absolute_url())
