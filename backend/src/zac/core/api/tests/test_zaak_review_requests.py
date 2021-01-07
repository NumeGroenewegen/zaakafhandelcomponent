import uuid
from unittest.mock import patch

from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse

import requests_mock
from rest_framework import status
from rest_framework.test import APITestCase
from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.catalogi import InformatieObjectType, ZaakType
from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen
from zgw_consumers.api_models.documenten import Document
from zgw_consumers.constants import APITypes
from zgw_consumers.models import Service
from zgw_consumers.test import generate_oas_component

from zac.accounts.tests.factories import SuperUserFactory, UserFactory
from zac.contrib.kownsl.data import Advice, KownslTypes, ReviewRequest
from zac.core.tests.utils import ClearCachesMixin
from zgw.models.zrc import Zaak

CATALOGI_ROOT = "http://catalogus.nl/api/v1/"
ZAKEN_ROOT = "http://zaken.nl/api/v1/"
DOCUMENTS_ROOT = "http://documents.nl/api/v1/"


@requests_mock.Mocker()
class ZaakReviewRequestsResponseTests(APITestCase):
    """
    Test the API response body for zaak-review-requests endpoint.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user = SuperUserFactory.create()

        Service.objects.create(api_type=APITypes.ztc, api_root=CATALOGI_ROOT)
        Service.objects.create(api_type=APITypes.zrc, api_root=ZAKEN_ROOT)
        Service.objects.create(api_type=APITypes.drc, api_root=DOCUMENTS_ROOT)

        catalogus_url = (
            f"{CATALOGI_ROOT}/catalogussen/e13e72de-56ba-42b6-be36-5c280e9b30cd"
        )
        cls.zaaktype = generate_oas_component(
            "ztc",
            "schemas/ZaakType",
            url=f"{CATALOGI_ROOT}zaaktypen/3e2a1218-e598-4bbe-b520-cb56b0584d60",
            identificatie="ZT1",
            catalogus=catalogus_url,
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        cls.documenttype = generate_oas_component(
            "ztc",
            "schemas/InformatieObjectType",
            url=f"{CATALOGI_ROOT}informatieobjecttypen/d5d7285d-ce95-4f9e-a36f-181f1c642aa6",
            omschrijving="bijlage",
            catalogus=catalogus_url,
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        cls.zaak = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=f"{ZAKEN_ROOT}zaken/e3f5c6d2-0e49-4293-8428-26139f630950",
            identificatie="ZAAK-2020-0010",
            bronorganisatie="123456782",
            zaaktype=cls.zaaktype["url"],
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
            startdatum="2020-12-25",
            uiterlijkeEinddatumAfdoening="2021-01-04",
        )
        cls.document = generate_oas_component(
            "drc",
            "schemas/EnkelvoudigInformatieObject",
            url=f"{DOCUMENTS_ROOT}enkelvoudiginformatieobjecten/0c47fe5e-4fe1-4781-8583-168e0730c9b6",
            identificatie="DOC-2020-007",
            bronorganisatie="123456782",
            informatieobjecttype=cls.documenttype["url"],
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
            bestandsomvang=10,
        )

        zaak = factory(Zaak, cls.zaak)
        zaak.zaaktype = factory(ZaakType, cls.zaaktype)

        document = factory(Document, cls.document)

        cls.find_zaak_patcher = patch("zac.core.api.views.find_zaak", return_value=zaak)

        # can't use generate_oas_component because Kownsl API schema doesn't have components
        # so manually creating review request, author, advicedocument, advice
        cls._uuid = uuid.uuid4()
        review_request = {
            "id": cls._uuid,
            "created": "2021-01-07T12:00:00Z",
            "for_zaak": zaak.url,
            "review_type": KownslTypes.advice,
            "documents": [document.url],
            "frontend_url": "http://some-kownsl-url.com/frontend-stuff",
            "num_advices": 1,
            "num_approvals": 0,
            "num_assigned_users": 2,
            "toelichting": "",
            "user_deadlines": {"some-user": "2021-01-07", "some-user-2": "2021-01-08"},
            "requester": "some-other-user",
        }
        review_request = factory(ReviewRequest, review_request)

        cls.get_review_requests_patcher = patch(
            "zac.core.api.views.get_review_requests", return_value=[review_request]
        )

        advice_document = {
            "document": document.url,
            "source_version": 1,
            "advice_version": 1,
        }

        author = {
            "username": cls.user.username,
            "first_name": "some-first-name",
            "last_name": "some-last-name",
        }

        advices = [
            {
                "created": "2021-01-07T12:00:00Z",
                "author": author,
                "advice": "some-advice",
                "documents": [advice_document],
            },
        ]
        advices = factory(Advice, advices)

        cls.get_review_requests_advices_patcher = patch(
            "zac.core.api.views.retrieve_advices", return_value=advices
        )
        cls.get_review_requests_approvals_patcher = patch(
            "zac.core.api.views.retrieve_approvals", return_value=[]
        )

        cls.endpoint_completed = reverse(
            "zaak-review-requests-completed",
            kwargs={
                "bronorganisatie": "123456782",
                "identificatie": "ZAAK-2020-0010",
            },
        )
        cls.endpoint_detail = reverse(
            "zaak-review-requests-detail",
            kwargs={
                "bronorganisatie": "123456782",
                "identificatie": "ZAAK-2020-0010",
            },
        )

    def setUp(self):
        super().setUp()

        self.find_zaak_patcher.start()
        self.addCleanup(self.find_zaak_patcher.stop)

        self.get_review_requests_patcher.start()
        self.addCleanup(self.get_review_requests_patcher.stop)

        self.get_review_requests_advices_patcher.start()
        self.addCleanup(self.get_review_requests_advices_patcher.stop)

        self.get_review_requests_approvals_patcher.start()
        self.addCleanup(self.get_review_requests_approvals_patcher.stop)

        # ensure that we have a user with all permissions
        self.client.force_authenticate(user=self.user)

    def test_get_zaak_review_requests_completed(self, m):
        response = self.client.get(self.endpoint_completed)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(
            response_data,
            [
                {
                    "id": str(self._uuid),
                    "reviewType": KownslTypes.advice,
                    "completed": 1,
                    "numAssignedUsers": 2,
                }
            ],
        )

    def test_get_zaak_review_requests_detail(self, m):
        response = self.client.get(self.endpoint_detail)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(
            response_data,
            [
                {
                    "id": str(self._uuid),
                    "reviewType": KownslTypes.advice,
                    "reviews": [
                        {
                            "created": "2021-01-07T12:00:00Z",
                            "author": {
                                "firstName": "some-first-name",
                                "lastName": "some-last-name",
                            },
                            "advice": "some-advice",
                            "documents": [
                                {
                                    "document": self.document["url"],
                                    "sourceVersion": 1,
                                    "adviceVersion": 1,
                                }
                            ],
                        }
                    ],
                }
            ],
        )

    def test_no_review_requests(self, m):
        with patch("zac.core.api.views.get_review_requests", return_value=[]):
            response = self.client.get(self.endpoint_completed)

        self.assertEqual(response.data, [])

    def test_zaak_not_found(self, m):
        with patch("zac.core.api.views.find_zaak", side_effect=ObjectDoesNotExist):
            response = self.client.get(self.endpoint_completed)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ZaakReviewRequestsPermissionTests(ClearCachesMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.endpoint_completed = reverse(
            "zaak-review-requests-completed",
            kwargs={
                "bronorganisatie": "123456782",
                "identificatie": "ZAAK-2020-0010",
            },
        )
        cls.endpoint_detail = reverse(
            "zaak-review-requests-detail",
            kwargs={
                "bronorganisatie": "123456782",
                "identificatie": "ZAAK-2020-0010",
            },
        )

    def test_rr_completed_not_authenticated(self):
        response = self.client.get(self.endpoint_completed)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_rr_detail_not_authenticated(self):
        response = self.client.get(self.endpoint_detail)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_rr_completed_authenticated_no_permissions(self):
        user = UserFactory.create()
        self.client.force_authenticate(user=user)

        response = self.client.get(self.endpoint_completed)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_rr_detail_authenticated_no_permissions(self):
        user = UserFactory.create()
        self.client.force_authenticate(user=user)

        response = self.client.get(self.endpoint_detail)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
