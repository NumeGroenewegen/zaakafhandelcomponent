from itertools import groupby
from typing import List

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from ..base_views import BaseDetailView, BaseListView
from ..forms import ZakenFilterForm
from ..services import (
    find_zaak,
    get_documenten,
    get_statussen,
    get_zaakobjecten,
    get_zaken,
)
from ..zaakobjecten import GROUPS, ZaakObjectGroup


class Index(LoginRequiredMixin, BaseListView):
    """
    Display the landing screen.
    """

    template_name = "core/index.html"
    context_object_name = "zaken"
    filter_form_class = ZakenFilterForm

    def get_object_list(self):
        filter_form = self.get_filter_form()
        if filter_form.is_valid():
            filters = filter_form.as_filters()
        else:
            filters = {}
        return get_zaken(**filters)[:50]


class ZaakDetail(LoginRequiredMixin, BaseDetailView):
    template_name = "core/zaak_detail.html"
    context_object_name = "zaak"

    def get_object(self):
        return find_zaak(**self.kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "statussen": get_statussen(self.object),
                "documenten": get_documenten(self.object),
            }
        )
        return context


class FetchZaakObjecten(LoginRequiredMixin, TemplateView):
    """
    Retrieve the ZaakObjecten for a given zaak reference.

    Intended to be called via AJAX.
    """

    template_name = "core/includes/zaakobjecten.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        zaak_url = self.request.GET.get("zaak")
        if not zaak_url:
            raise ValueError("Expected zaak querystring parameter")

        context["zaakobjecten"] = self._get_zaakobjecten(zaak_url)

        return context

    def _get_zaakobjecten(self, zaak_url: str) -> List[ZaakObjectGroup]:
        # API call
        zaakobjecten = get_zaakobjecten(zaak_url)

        def group_key(zo):
            return zo.object_type

        # re-group by type
        render_groups = []
        zaakobjecten = sorted(zaakobjecten, key=group_key)
        grouped = groupby(zaakobjecten, key=group_key)
        for _group, items in grouped:
            group = GROUPS.get(_group, ZaakObjectGroup(label=_group))
            group.retrieve_items(items)
            render_groups.append(group)
        return render_groups