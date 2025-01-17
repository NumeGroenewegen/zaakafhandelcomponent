import uuid
from unittest.mock import patch

from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse

import requests_mock
from rest_framework import status
from rest_framework.test import APITestCase
from zds_client.client import ClientError
from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.catalogi import ZaakType
from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen
from zgw_consumers.api_models.documenten import Document
from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.models import Service
from zgw_consumers.test import generate_oas_component, mock_service_oas_get

from zac.accounts.tests.factories import (
    BlueprintPermissionFactory,
    SuperUserFactory,
    UserFactory,
)
from zac.contrib.dowc.constants import DocFileTypes
from zac.contrib.kownsl.api import get_client
from zac.contrib.kownsl.data import Advice, KownslTypes, ReviewRequest
from zac.contrib.kownsl.models import KownslConfig
from zac.core.permissions import zaken_inzien
from zac.core.tests.utils import ClearCachesMixin
from zac.tests.utils import paginated_response
from zgw.models.zrc import Zaak

from .utils import (
    ADVICE,
    CATALOGI_ROOT,
    DOCUMENT_URL,
    DOCUMENTS_ROOT,
    KOWNSL_ROOT,
    REVIEW_REQUEST,
    ZAAK_URL,
    ZAKEN_ROOT,
)


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
        cls.kownsl_service = Service.objects.create(
            label="kownsl",
            api_type=APITypes.orc,
            api_root=KOWNSL_ROOT,
            auth_type=AuthTypes.zgw,
            client_id="zac",
            secret="supersecret",
            user_id="zac",
        )

        config = KownslConfig.get_solo()
        config.service = cls.kownsl_service
        config.save()

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
        cls.zaak = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=ZAAK_URL,
            identificatie="ZAAK-2020-0010",
            bronorganisatie="123456782",
            zaaktype=cls.zaaktype["url"],
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
            startdatum="2020-12-25",
            uiterlijkeEinddatumAfdoening="2021-01-04",
        )
        cls.documenttype = generate_oas_component(
            "ztc",
            "schemas/InformatieObjectType",
            url=f"{CATALOGI_ROOT}informatieobjecttypen/d5d7285d-ce95-4f9e-a36f-181f1c642aa6",
            omschrijving="bijlage",
            catalogus=catalogus_url,
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        cls.document = generate_oas_component(
            "drc",
            "schemas/EnkelvoudigInformatieObject",
            url=DOCUMENT_URL,
            identificatie="DOC-2020-007",
            bronorganisatie="123456782",
            informatieobjecttype=cls.documenttype["url"],
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
            bestandsomvang=10,
        )

        zaak = factory(Zaak, cls.zaak)
        zaak.zaaktype = factory(ZaakType, cls.zaaktype)

        cls.find_zaak_patcher = patch("zac.core.api.views.find_zaak", return_value=zaak)
        cls.get_zaak_patcher = patch(
            "zac.contrib.kownsl.views.get_zaak", return_value=zaak
        )
        document = factory(Document, cls.document)
        cls.get_document_patcher = patch(
            "zac.contrib.kownsl.views.get_document", return_value=document
        )

        review_request = factory(ReviewRequest, REVIEW_REQUEST)
        cls.get_review_request_patcher = patch(
            "zac.contrib.kownsl.views.get_review_request", return_value=review_request
        )
        cls.get_review_requests_patcher = patch(
            "zac.contrib.kownsl.views.get_review_requests",
            return_value=[review_request],
        )
        advices = factory(Advice, [ADVICE])
        cls.get_advices_patcher = patch(
            "zac.contrib.kownsl.views.retrieve_advices", return_value=advices
        )
        cls.get_approvals_patcher = patch(
            "zac.contrib.kownsl.views.retrieve_approvals", return_value=[]
        )
        cls.endpoint_summary = reverse(
            "kownsl:zaak-review-requests-summary",
            kwargs={
                "bronorganisatie": "123456782",
                "identificatie": "ZAAK-2020-0010",
            },
        )
        cls.endpoint_detail = reverse(
            "kownsl:zaak-review-requests-detail",
            kwargs={
                "request_uuid": review_request.id,
            },
        )

    def setUp(self):
        super().setUp()

        self.find_zaak_patcher.start()
        self.addCleanup(self.find_zaak_patcher.stop)

        self.get_zaak_patcher.start()
        self.addCleanup(self.get_zaak_patcher.stop)

        self.get_review_requests_patcher.start()
        self.addCleanup(self.get_review_requests_patcher.stop)

        self.get_advices_patcher.start()
        self.addCleanup(self.get_advices_patcher.stop)

        self.get_approvals_patcher.start()
        self.addCleanup(self.get_approvals_patcher.stop)

        self.get_document_patcher.start()
        self.addCleanup(self.get_document_patcher.stop)

        # ensure that we have a user with all permissions
        self.client.force_authenticate(user=self.user)

    def test_get_zaak_review_requests_completed(self, m):
        response = self.client.get(self.endpoint_summary)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(
            response_data,
            [
                {
                    "id": REVIEW_REQUEST["id"],
                    "reviewType": KownslTypes.advice,
                    "completed": 1,
                    "numAssignedUsers": 1,
                    "canLock": False,
                    "locked": False,
                    "lockReason": "",
                }
            ],
        )

    def test_get_zaak_review_requests_can_lock(self, m):
        some_other_user = SuperUserFactory(
            username=REVIEW_REQUEST["requester"]["username"]
        )
        self.client.force_authenticate(user=some_other_user)
        response = self.client.get(self.endpoint_summary)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(
            response_data,
            [
                {
                    "id": REVIEW_REQUEST["id"],
                    "reviewType": KownslTypes.advice,
                    "completed": 1,
                    "numAssignedUsers": 1,
                    "canLock": True,
                    "locked": False,
                    "lockReason": "",
                }
            ],
        )

    def test_get_zaak_review_requests_is_locked(self, m):
        rr = factory(
            ReviewRequest,
            {**REVIEW_REQUEST, "locked": True, "lockReason": "just a reason"},
        )
        with patch(
            "zac.contrib.kownsl.views.get_review_requests",
            return_value=[rr],
        ):
            response = self.client.get(self.endpoint_summary)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(
            response_data,
            [
                {
                    "id": REVIEW_REQUEST["id"],
                    "reviewType": KownslTypes.advice,
                    "completed": 1,
                    "numAssignedUsers": 1,
                    "canLock": False,
                    "locked": True,
                    "lockReason": "just a reason",
                }
            ],
        )

    def test_get_zaak_review_requests_detail(self, m):
        self.get_review_request_patcher.start()
        response = self.client.get(self.endpoint_detail)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()

        doc_url = reverse(
            "dowc:request-doc",
            kwargs={
                "bronorganisatie": self.document["bronorganisatie"],
                "identificatie": self.document["identificatie"],
                "purpose": DocFileTypes.read,
            },
        )
        self.assertEqual(
            response_data,
            {
                "id": REVIEW_REQUEST["id"],
                "reviewType": REVIEW_REQUEST["reviewType"],
                "advices": [
                    {
                        **ADVICE,
                        "documents": [
                            {
                                "adviceVersion": 2,
                                "adviceUrl": doc_url + "?versie=2",
                                "sourceUrl": doc_url + "?versie=1",
                                "sourceVersion": 1,
                                "title": self.document["bestandsnaam"],
                            }
                        ],
                    }
                ],
            },
        )
        self.get_review_request_patcher.stop()

    def test_no_review_request(self, m):
        mock_service_oas_get(m, KOWNSL_ROOT, "kownsl")

        kownsl_client = get_client()
        with patch.object(
            kownsl_client, "get_operation_url", return_value="", create=True
        ):
            with patch.object(
                kownsl_client, "request", side_effect=ClientError, create=True
            ):
                with patch(
                    "zac.contrib.kownsl.api.get_client", return_value=kownsl_client
                ):
                    response = self.client.get(self.endpoint_detail)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_zaak_not_found(self, m):
        self.get_review_request_patcher.start()
        with patch("zac.contrib.kownsl.views.get_zaak", side_effect=ObjectDoesNotExist):
            response = self.client.get(self.endpoint_detail)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.get_review_request_patcher.stop()

    def test_no_review_requests(self, m):
        with patch("zac.contrib.kownsl.views.get_review_requests", return_value=[]):
            response = self.client.get(self.endpoint_summary)
        self.assertEqual(response.data, [])

    def test_find_zaak_not_found(self, m):
        with patch("zac.core.api.views.find_zaak", side_effect=ObjectDoesNotExist):
            response = self.client.get(self.endpoint_summary)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_lock_review_request(self, m):
        mock_service_oas_get(m, KOWNSL_ROOT, "kownsl")
        m.get(
            f"{KOWNSL_ROOT}api/v1/review-requests/{REVIEW_REQUEST['id']}",
            json=REVIEW_REQUEST,
        )
        m.get(
            f"{KOWNSL_ROOT}api/v1/review-requests/{REVIEW_REQUEST['id']}/advices",
            json=[ADVICE],
        )
        m.patch(
            f"{KOWNSL_ROOT}api/v1/review-requests/{REVIEW_REQUEST['id']}",
            json={**REVIEW_REQUEST, "locked": True, "lock_reason": "some-reason"},
            status_code=200,
        )

        url = reverse(
            "kownsl:zaak-review-requests-detail",
            kwargs={"request_uuid": REVIEW_REQUEST["id"]},
        )
        body = {"lock_reason": "some-reason"}
        # log in - we need to see the user ID in the auth from ZAC to Kownsl
        user = SuperUserFactory.create(username=REVIEW_REQUEST["requester"]["username"])
        self.client.force_authenticate(user=user)
        response = self.client.patch(url, body)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ZaakReviewRequestsPermissionTests(ClearCachesMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        Service.objects.create(api_type=APITypes.ztc, api_root=CATALOGI_ROOT)
        Service.objects.create(api_type=APITypes.zrc, api_root=ZAKEN_ROOT)
        Service.objects.create(api_type=APITypes.drc, api_root=DOCUMENTS_ROOT)
        cls.kownsl_service = Service.objects.create(
            label="Kownsl",
            api_type=APITypes.orc,
            api_root=KOWNSL_ROOT,
            auth_type=AuthTypes.zgw,
            client_id="zac",
            secret="supersecret",
            user_id="zac",
        )

        config = KownslConfig.get_solo()
        config.service = cls.kownsl_service
        config.save()

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
            omschrijving="ZT1",
        )
        cls.zaak = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=ZAAK_URL,
            identificatie="ZAAK-2020-0010",
            bronorganisatie="123456782",
            zaaktype=cls.zaaktype["url"],
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.beperkt_openbaar,
            startdatum="2020-12-25",
            uiterlijkeEinddatumAfdoening="2021-01-04",
        )
        cls.documenttype = generate_oas_component(
            "ztc",
            "schemas/InformatieObjectType",
            url=f"{CATALOGI_ROOT}informatieobjecttypen/d5d7285d-ce95-4f9e-a36f-181f1c642aa6",
            omschrijving="bijlage",
            catalogus=catalogus_url,
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
        )
        cls.document = generate_oas_component(
            "drc",
            "schemas/EnkelvoudigInformatieObject",
            url=DOCUMENT_URL,
            identificatie="DOC-2020-007",
            bronorganisatie="123456782",
            informatieobjecttype=cls.documenttype["url"],
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.beperkt_openbaar,
            bestandsomvang=10,
        )

        zaak = factory(Zaak, cls.zaak)
        zaak.zaaktype = factory(ZaakType, cls.zaaktype)

        cls.find_zaak_patcher = patch("zac.core.api.views.find_zaak", return_value=zaak)
        cls.get_zaak_patcher = patch(
            "zac.contrib.kownsl.views.get_zaak", return_value=zaak
        )

        cls.review_request = factory(ReviewRequest, REVIEW_REQUEST)
        cls.advices = factory(Advice, [ADVICE])
        cls.get_advices_patcher = patch(
            "zac.contrib.kownsl.api.retrieve_advices", return_value=cls.advices
        )
        cls.get_approvals_patcher = patch(
            "zac.contrib.kownsl.api.retrieve_approvals", return_value=[]
        )
        document = factory(Document, cls.document)
        cls.get_document_patcher = patch(
            "zac.contrib.kownsl.views.get_document", return_value=document
        )
        cls.endpoint_summary = reverse(
            "kownsl:zaak-review-requests-summary",
            kwargs={
                "bronorganisatie": "123456782",
                "identificatie": "ZAAK-2020-0010",
            },
        )
        cls.endpoint_detail = reverse(
            "kownsl:zaak-review-requests-detail",
            kwargs={
                "request_uuid": REVIEW_REQUEST["id"],
            },
        )

    def setUp(self):
        super().setUp()

        self.find_zaak_patcher.start()
        self.addCleanup(self.find_zaak_patcher.stop)

        self.get_zaak_patcher.start()
        self.addCleanup(self.get_zaak_patcher.stop)

        self.get_document_patcher.start()
        self.addCleanup(self.get_document_patcher.stop)

    def test_rr_summary_not_authenticated(self):
        response = self.client.get(self.endpoint_summary)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_rr_detail_not_authenticated(self):
        response = self.client.get(self.endpoint_detail)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @requests_mock.Mocker()
    def test_get_rr_summary_authenticated_no_permissions(self, m):
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        mock_service_oas_get(m, KOWNSL_ROOT, "kownsl")
        m.get(
            f"{ZAKEN_ROOT}rollen?zaak={self.zaak['url']}",
            json=paginated_response([]),
        )
        m.get(
            f"{KOWNSL_ROOT}api/v1/review-requests?for_zaak={self.zaak['url']}",
            json=[],
        )
        user = UserFactory.create()
        self.client.force_authenticate(user=user)

        response = self.client.get(self.endpoint_summary)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_rr_detail_authenticated_no_permissions(self):
        user = UserFactory.create()
        self.client.force_authenticate(user=user)

        response = self.client.get(self.endpoint_detail)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @requests_mock.Mocker()
    def test_has_get_perm_but_not_for_zaaktype(self, m):
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        mock_service_oas_get(m, KOWNSL_ROOT, "kownsl")
        m.get(
            f"{ZAKEN_ROOT}rollen?zaak={self.zaak['url']}",
            json=paginated_response([]),
        )
        m.get(
            f"{KOWNSL_ROOT}api/v1/review-requests?for_zaak={self.zaak['url']}",
            json=[],
        )
        # gives them access to the page, but no catalogus specified -> nothing visible
        user = UserFactory.create()
        BlueprintPermissionFactory.create(
            role__permissions=[zaken_inzien.name],
            for_user=user,
            policy={
                "catalogus": "",
                "zaaktype_omschrijving": "",
                "max_va": VertrouwelijkheidsAanduidingen.openbaar,
            },
        )
        self.client.force_authenticate(user=user)

        with patch(
            "zac.contrib.kownsl.views.get_review_requests",
            return_value=[self.review_request],
        ):
            response_summary = self.client.get(self.endpoint_summary)
        self.assertEqual(response_summary.status_code, status.HTTP_403_FORBIDDEN)

        with patch(
            "zac.contrib.kownsl.views.get_review_request",
            return_value=self.review_request,
        ):
            response_detail = self.client.get(self.endpoint_detail)
        self.assertEqual(response_detail.status_code, status.HTTP_403_FORBIDDEN)

    @requests_mock.Mocker()
    def test_has_get_perm_but_not_for_va(self, m):
        mock_service_oas_get(m, CATALOGI_ROOT, "ztc")
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        mock_service_oas_get(m, KOWNSL_ROOT, "kownsl")
        m.get(
            f"{CATALOGI_ROOT}zaaktypen?catalogus={self.zaaktype['catalogus']}",
            json=paginated_response([self.zaaktype]),
        )
        m.get(
            f"{ZAKEN_ROOT}rollen?zaak={self.zaak['url']}",
            json=paginated_response([]),
        )
        m.get(
            f"{KOWNSL_ROOT}api/v1/review-requests?for_zaak={self.zaak['url']}",
            json=[],
        )
        user = UserFactory.create()
        # gives them access to the page and zaaktype, but insufficient VA
        BlueprintPermissionFactory.create(
            role__permissions=[zaken_inzien.name],
            for_user=user,
            policy={
                "catalogus": self.zaaktype["catalogus"],
                "zaaktype_omschrijving": "ZT1",
                "max_va": VertrouwelijkheidsAanduidingen.openbaar,
            },
        )
        self.client.force_authenticate(user=user)

        with patch(
            "zac.contrib.kownsl.views.get_review_requests",
            return_value=[self.review_request],
        ):
            response_summary = self.client.get(self.endpoint_summary)
        self.assertEqual(response_summary.status_code, status.HTTP_403_FORBIDDEN)

        with patch(
            "zac.contrib.kownsl.views.get_review_request",
            return_value=self.review_request,
        ):
            response_detail = self.client.get(self.endpoint_detail)
        self.assertEqual(response_detail.status_code, status.HTTP_403_FORBIDDEN)

    @requests_mock.Mocker()
    def test_has_get_perm(self, m):
        mock_service_oas_get(m, CATALOGI_ROOT, "ztc")
        m.get(
            f"{CATALOGI_ROOT}zaaktypen?catalogus={self.zaaktype['catalogus']}",
            json=paginated_response([self.zaaktype]),
        )
        user = UserFactory.create()
        # gives them access to the page, zaaktype and VA specified -> visible
        BlueprintPermissionFactory.create(
            role__permissions=[zaken_inzien.name],
            for_user=user,
            policy={
                "catalogus": self.zaaktype["catalogus"],
                "zaaktype_omschrijving": "ZT1",
                "max_va": VertrouwelijkheidsAanduidingen.zeer_geheim,
            },
        )
        self.client.force_authenticate(user=user)

        with patch(
            "zac.contrib.kownsl.views.get_review_requests",
            return_value=[self.review_request],
        ):
            response_summary = self.client.get(self.endpoint_summary)
        self.assertEqual(response_summary.status_code, status.HTTP_200_OK)

        with patch(
            "zac.contrib.kownsl.views.get_review_request",
            return_value=self.review_request,
        ):
            with patch(
                "zac.contrib.kownsl.views.retrieve_advices", return_value=self.advices
            ):
                with patch(
                    "zac.contrib.kownsl.views.retrieve_approvals", return_value=[]
                ):
                    response_detail = self.client.get(self.endpoint_detail)
        self.assertEqual(response_detail.status_code, status.HTTP_200_OK)

    @requests_mock.Mocker()
    def test_has_lock_perm(self, m):
        mock_service_oas_get(m, KOWNSL_ROOT, "kownsl")
        mock_service_oas_get(m, CATALOGI_ROOT, "ztc")
        m.get(
            f"{CATALOGI_ROOT}zaaktypen?catalogus={self.zaaktype['catalogus']}",
            json=paginated_response([self.zaaktype]),
        )
        user = UserFactory.create(username=REVIEW_REQUEST["requester"]["username"])
        # gives them access to the page, zaaktype and VA specified -> visible
        BlueprintPermissionFactory.create(
            role__permissions=[zaken_inzien.name],
            for_user=user,
            policy={
                "catalogus": self.zaaktype["catalogus"],
                "zaaktype_omschrijving": "ZT1",
                "max_va": VertrouwelijkheidsAanduidingen.zeer_geheim,
            },
        )
        self.client.force_authenticate(user=user)
        m.patch(
            f"{KOWNSL_ROOT}api/v1/review-requests/{REVIEW_REQUEST['id']}",
            json={**REVIEW_REQUEST, "locked": True, "lock_reason": "zomaar"},
            status_code=200,
        )
        with patch(
            "zac.contrib.kownsl.views.get_review_request",
            return_value=self.review_request,
        ):
            with patch(
                "zac.contrib.kownsl.views.retrieve_advices", return_value=self.advices
            ):
                with patch(
                    "zac.contrib.kownsl.views.retrieve_approvals", return_value=[]
                ):
                    response_detail = self.client.patch(
                        self.endpoint_detail, {"lock_reason": "zomaar"}
                    )
        self.assertEqual(response_detail.status_code, status.HTTP_200_OK)
