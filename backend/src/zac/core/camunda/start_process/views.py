from django.utils.translation import gettext_lazy as _

from drf_spectacular.utils import extend_schema
from rest_framework import exceptions, permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView
from zgw_consumers.api_models.constants import RolOmschrijving

from zac.accounts.api.permissions import HasTokenAuth
from zac.accounts.authentication import ApplicationTokenAuthentication
from zac.camunda.api.utils import start_process
from zac.camunda.constants import AssigneeTypeChoices
from zac.contrib.objects.services import fetch_start_camunda_process_form
from zac.core.api.views import GetZaakMixin
from zac.core.services import get_rollen

from .permissions import CanStartCamundaProcess
from .serializers import CreatedProcessInstanceSerializer


class StartCamundaProcessView(GetZaakMixin, APIView):
    authentication_classes = [
        ApplicationTokenAuthentication
    ] + api_settings.DEFAULT_AUTHENTICATION_CLASSES
    permission_classes = (
        HasTokenAuth | (permissions.IsAuthenticated & CanStartCamundaProcess),
    )

    def get_serializer(self, *args, **kwargs):
        return CreatedProcessInstanceSerializer(*args, **kwargs)

    @extend_schema(summary=_("Start camunda process for ZAAK."))
    def post(
        self, request: Request, bronorganisatie: str, identificatie: str
    ) -> Response:
        zaak = self.get_object()

        # See if there is a configured camunda_start_process object
        form = fetch_start_camunda_process_form(zaak.zaaktype)
        if not form:
            raise exceptions.NotFound(
                "No start camunda process form found for zaaktype with `identificatie`: `%s`."
                % zaak.zaaktype.identificatie
            )

        variables = {
            "zaakUrl": zaak.url,
            "zaakIdentificatie": zaak.identificatie,
            "zaakDetails": {
                "omschrijving": zaak.omschrijving,
                "zaaktypeOmschrijving": zaak.zaaktype.omschrijving,
            },
        }

        initiator = [
            rol
            for rol in get_rollen(zaak)
            if rol.omschrijving_generiek.lower() == RolOmschrijving.initiator.lower()
        ]
        if initiator:
            variables["initiator"] = initiator[0].betrokkene_identificatie[
                "identificatie"
            ]
        elif request.user:
            variables["initiator"] = f"{AssigneeTypeChoices.user}:{request.user}"

        results = start_process(
            process_key=form.camunda_process_definition_key,
            variables=variables,
        )
        serializer = self.get_serializer(results)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
