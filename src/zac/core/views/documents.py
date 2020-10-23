import mimetypes
from typing import Any, Optional

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.views import View

from rules.contrib.views import PermissionRequiredMixin
from zgw_consumers.api_models.documenten import Document

from ..services import download_document, find_document, get_informatieobjecttype


def _cast(value: Optional[Any], type_: type) -> Any:
    if value is None:
        return value
    return type_(value)


class DownloadDocumentView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "core:download_document"

    document = None

    def get_object(self) -> Document:
        versie = _cast(self.request.GET.get("versie", None), int)
        self.document = find_document(versie=versie, **self.kwargs)

        informatieobjecttype = get_informatieobjecttype(
            self.document.informatieobjecttype
        )
        self.document.informatieobjecttype = informatieobjecttype
        return self.document

    def get(self, request, *args, **kwargs):
        if self.document is None:
            self.get_object()

        content_type = (
            self.document.formaat or mimetypes.guess_type(self.document.bestandsnaam)[0]
        )

        document, content = download_document(self.document)
        response = HttpResponse(content, content_type=content_type)
        response[
            "Content-Disposition"
        ] = f'attachment; filename="{document.bestandsnaam}"'
        return response
