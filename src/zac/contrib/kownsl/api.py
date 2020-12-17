from typing import List

from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.zaken import Zaak
from zgw_consumers.client import ZGWClient

from zac.utils.decorators import optional_service

from .data import Advice, Approval, ReviewRequest
from .models import KownslConfig


def get_client() -> ZGWClient:
    config = KownslConfig.get_solo()
    assert config.service, "A service must be configured first"
    return config.service.build_client()


def create_review_request(
    zaak_url: str,
    documents: List[str],
    review_type: str = "advice",
    num_assigned_users: int = 0,
    toelichting: str = "",
    user_deadlines: dict = {},
    requester: str = "",
) -> ReviewRequest:
    client = get_client()
    data = {
        "for_zaak": zaak_url,
        "review_type": review_type,
        "num_assigned_users": num_assigned_users,
        "documents": documents,
        "toelichting": toelichting,
        "user_deadlines": user_deadlines,
        "requester": requester,
    }
    resp = client.create("reviewrequest", data=data)
    return factory(ReviewRequest, resp)


@optional_service
def retrieve_advices(review_request: ReviewRequest) -> List[Advice]:
    """
    Retrieve the advices for a single review request.

    :param review_request_uuid: uuid of review request in Kownsl API
    :return: an list of advice object
    """
    client = get_client()
    result = client.list("advice", parent_lookup_request__uuid=review_request.id)
    return factory(Advice, result)


@optional_service
def retrieve_approvals(review_request: ReviewRequest) -> List[Approval]:
    """
    Retrieve the approvals for a single review request.

    :param review_request_uuid: uuid of review request in Kownsl API
    :return: an approval-collection object
    """
    client = get_client()
    result = client.list("approval", parent_lookup_request__uuid=review_request.id)
    return factory(Approval, result)


@optional_service
def get_review_requests(zaak: Zaak) -> List[ReviewRequest]:
    client = get_client()
    result = client.list("reviewrequest", query_params={"for_zaak": zaak.url})
    review_requests = factory(ReviewRequest, result)

    # fix relation reference
    for review_request in review_requests:
        review_request.for_zaak = zaak
    return review_requests
