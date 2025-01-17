from typing import List, Optional

from django.http import Http404
from django.utils.translation import gettext_lazy as _

from zds_client.client import ClientError
from zgw_consumers.api_models.base import factory
from zgw_consumers.client import ZGWClient

from zac.accounts.models import User
from zac.utils.decorators import optional_service
from zgw.models.zrc import Zaak

from .data import Advice, Approval, ReviewRequest
from .models import KownslConfig


def get_client(user: Optional[User] = None) -> ZGWClient:
    config = KownslConfig.get_solo()
    assert config.service, "A service must be configured first"
    service = config.service

    # override the actual logged in user in the `user_id` claim, so that Kownsl is
    # aware of the actual end user
    if user is not None:
        service.user_id = user.username
    client = service.build_client()
    client.operation_suffix_mapping = {
        **client.operation_suffix_mapping,
        "retrieve": "_retrieve",
    }
    return client


def create_review_request(
    zaak_url: str,
    requester: User,
    documents: List[str],
    review_type: str = "advice",
    num_assigned_users: int = 0,
    toelichting: str = "",
    user_deadlines: Optional[dict] = None,
) -> ReviewRequest:
    client = get_client(user=requester)
    data = {
        "for_zaak": zaak_url,
        "review_type": review_type,
        "num_assigned_users": num_assigned_users,
        "documents": documents,
        "toelichting": toelichting,
        "user_deadlines": user_deadlines,
    }
    resp = client.create("review_requests", data=data)
    rr = factory(ReviewRequest, resp)

    # underscoreize in zgw_consumers.api_models.base.factory is messing
    # with the format of the keys in the user_deadlines dictionary
    rr.user_deadlines = user_deadlines
    return rr


@optional_service
def retrieve_advices(review_request: ReviewRequest) -> List[Advice]:
    """
    Retrieve the advices for a single review request.

    :param review_request_uuid: uuid of review request in Kownsl API
    :return: an list of advice object
    """
    client = get_client()
    result = client.list("review_requests_advices", request__uuid=review_request.id)
    return factory(Advice, result)


@optional_service
def retrieve_approvals(review_request: ReviewRequest) -> List[Approval]:
    """
    Retrieve the approvals for a single review request.

    :param review_request_uuid: uuid of review request in Kownsl API
    :return: an approval-collection object
    """
    client = get_client()
    result = client.list("review_requests_approvals", request__uuid=review_request.id)
    return factory(Approval, result)


@optional_service
def get_review_request(uuid: str) -> Optional[ReviewRequest]:
    client = get_client()
    # Reviewrequest_retrieve translates to reviewrequest_read which isn't a valid
    # operation_id in the schema (yet?). Building the url and doing the request
    # manually for now.
    try:
        result = client.retrieve("review_requests", uuid=uuid)
    except ClientError:
        raise Http404(f"Review request with id {uuid} does not exist.")

    review_request = factory(ReviewRequest, result)

    # underscoreize in zgw_consumers.api_models.base.factory is messing
    # with the format of the keys in the user_deadlines dictionary
    review_request.user_deadlines = result["userDeadlines"]
    return review_request


@optional_service
def get_review_requests(zaak: Zaak) -> List[ReviewRequest]:
    client = get_client()
    results = client.list("review_requests", query_params={"for_zaak": zaak.url})
    review_requests = factory(ReviewRequest, results)

    # fix relation reference
    for result, review_request in zip(results, review_requests):
        review_request.for_zaak = zaak
        review_request.user_deadlines = result["userDeadlines"]
    return review_requests


@optional_service
def lock_review_request(uuid: str, lock_reason: str) -> Optional[ReviewRequest]:
    client = get_client()
    try:
        result = client.partial_update(
            "review_requests",
            uuid=uuid,
            data={"locked": True, "lock_reason": lock_reason},
        )
    except ClientError:
        raise Http404(
            _("Review request with id {uuid} does not exist.").format(uuid=uuid)
        )

    review_request = factory(ReviewRequest, result)
    review_request.user_deadlines = result["userDeadlines"]
    return review_request
