from typing import Dict, NoReturn, Optional, Tuple

from django.http import Http404

from rest_framework import status
from zds_client.client import ClientError
from zds_client.schema import get_operation_url
from zgw_consumers.api_models.base import factory

from zac.accounts.models import User
from zac.client import Client
from zac.utils.decorators import optional_service

from .data import DowcResponse
from .models import DowcConfig


def get_client(user: User) -> Client:
    config = DowcConfig.get_solo()
    assert config.service, "A service must be configured first"
    service = config.service

    # override the actual logged in user in the `user_id` claim, so that D.O.C. is
    # aware of the actual end user
    if user is not None:
        service.user_id = user.username
    return service.build_client()


@optional_service
def get_doc_info(
    user: User, drc_url: str, purpose: str
) -> Optional[Tuple[DowcResponse, int]]:
    client = get_client(user)
    try:
        response = client.create(
            "v1_documenten",
            data={
                "drc_url": drc_url,
                "purpose": purpose,
            },
        )
        return factory(DowcResponse, response), status.HTTP_201_CREATED
    except ClientError:
        response = client.list(
            "v1_documenten",
            query_params={
                "drc_url": drc_url,
                "purpose": purpose,
            },
        )
        return factory(DowcResponse, response[0]), status.HTTP_200_OK


@optional_service
def patch_and_destroy_doc(user: User, uuid: str) -> Optional[NoReturn]:
    client = get_client(user)
    operation_id = "v1_documenten_destroy"
    try:
        url = get_operation_url(client.schema, operation_id, **{"uuid": uuid})
        client.request(url, operation_id, method="DELETE", expected_status=204)

    except ClientError:
        raise Http404(f"DocumentFile with id {uuid} does not exist.")