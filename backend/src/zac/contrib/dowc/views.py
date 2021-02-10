from typing import Any, NoReturn, Optional

from django.http import HttpResponse

from rest_framework import authentication, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from zgw_consumers.api_models.documenten import Document

from zac.core.services import find_document

from .api import get_doc_info, patch_and_destroy_doc
from .permissions import CanOpenDocuments
from .serializers import DowcResponseSerializer, DowcSerializer


def _cast(value: Optional[Any], type_: type) -> Any:
    if value is None:
        return value
    return type_(value)


class OpenDowcView(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated & CanOpenDocuments,)
    document = None
    serializer_class = DowcResponseSerializer

    def get_object(self) -> Document:
        bronorganisatie = self.kwargs["bronorganisatie"]
        identificatie = self.kwargs["identificatie"]
        purpose = self.kwargs["purpose"]

        if not self.document:
            versie = _cast(self.request.GET.get("versie", None), int)
            self.document = find_document(bronorganisatie, identificatie, versie=versie)
        return self.document

    def post(self, request, bronorganisatie, identificatie, purpose):
        """
        This will create a dowc object in the dowc API and exposes the document through a URL.
        """
        document = self.get_object()
        drc_url = self.document.url
        dowc_response, status_code = get_doc_info(request.user, drc_url, purpose)
        serializer = self.serializer_class(dowc_response)
        return Response(serializer.data, status=status_code)


class DeleteDowcView(APIView):
    authentication_classes = (authentication.SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated & CanOpenDocuments,)
    serializer_class = DowcSerializer

    def delete(self, request, dowc_uuid):
        """
        This will attempt to delete the dowc object in the dowc API.
        This implies that the dowc will attempt to patch the document in the
        DRC API.
        """
        serializer = self.serializer_class(data={"uuid": dowc_uuid})
        serializer.is_valid(raise_exception=True)
        patch_and_destroy_doc(request.user, serializer.validated_data["uuid"])
        return Response(status=status.HTTP_204_NO_CONTENT)