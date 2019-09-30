from django.views.generic import DetailView, ListView

from zac.core.services import get_zaken

from .models import RegieZaakConfiguratie


class IndexView(ListView):
    model = RegieZaakConfiguratie
    template_name = "regiezaken/index.html"


class RegieZaakDetailView(DetailView):
    model = RegieZaakConfiguratie
    template_name = "regiezaken/regiezaak_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        instance = self.get_object()
        context['zaken'] = get_zaken(zaaktypes=[instance.zaaktype_object.id])

        return context
