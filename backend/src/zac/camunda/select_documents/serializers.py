from dataclasses import dataclass
from typing import Dict, List, NoReturn

from django.core.validators import URLValidator
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers
from zgw_consumers.api_models.documenten import Document
from zgw_consumers.drf.serializers import APIModelSerializer

from zac.camunda.data import Task
from zac.camunda.process_instances import get_process_instance
from zac.camunda.user_tasks import Context, register, usertask_context_serializer
from zac.contrib.dowc.constants import DocFileTypes
from zac.contrib.dowc.utils import get_dowc_url
from zac.core.camunda import get_process_zaak_url
from zac.core.services import get_documenten, get_zaak


class DocumentSerializer(APIModelSerializer):
    read_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = (
            "beschrijving",
            "bestandsnaam",
            "bestandsomvang",
            "url",
            "read_url",
            "versie",
        )

    def get_read_url(self, obj) -> str:
        """
        Create the document read url to facilitate opening the document
        in a MS WebDAV client.
        """
        return get_dowc_url(obj, purpose=DocFileTypes.read)


@dataclass
class DocumentSelectContext(Context):
    documents: List[Document]


@usertask_context_serializer
class DocumentSelectContextSerializer(APIModelSerializer):
    documents = DocumentSerializer(many=True)

    class Meta:
        model = DocumentSelectContext
        fields = ("documents",)


#
# Write serializer
#


class DocumentSelectTaskSerializer(serializers.Serializer):
    """
    Serializes the selected documents for the task.

    Requires ``task`` to be in serializer ``context``.
    """

    selected_documents = serializers.MultipleChoiceField(
        choices=(),
        validators=[URLValidator],
        label=_("Selecteer de relevante documenten"),
        help_text=_(
            "Dit zijn de documenten die bij de zaak horen. Selecteer de relevante "
            "documenten."
        ),
        allow_blank=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Get zaak documents to verify valid document selection
        task = self.context["task"]
        process_instance = get_process_instance(task.process_instance_id)
        self.zaak_url = get_process_zaak_url(process_instance)
        zaak = get_zaak(zaak_url=self.zaak_url)
        documenten, rest = get_documenten(zaak)
        self.fields["selected_documents"].choices = [doc.url for doc in documenten]

    def get_process_variables(self) -> Dict:
        """
        #TODO: ?
        """
        return {}

    def on_task_submission(self) -> NoReturn:
        """
        #TODO: ?
        """
        pass
