from datetime import date

from django.core import mail
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

import requests_mock
from freezegun import freeze_time
from rest_framework import status
from rest_framework.test import APITestCase, APITransactionTestCase
from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen
from zgw_consumers.constants import APITypes
from zgw_consumers.models import Service
from zgw_consumers.test import generate_oas_component, mock_service_oas_get

from zac.core.permissions import zaken_handle_access
from zac.tests.utils import paginated_response

from ...constants import AccessRequestResult
from ...models import AccessRequest
from ...tests.factories import (
    AccessRequestFactory,
    PermissionSetFactory,
    SuperUserFactory,
    UserFactory,
)

CATALOGI_ROOT = "https://api.catalogi.nl/api/v1/"
CATALOGUS_URL = f"{CATALOGI_ROOT}catalogi/dfb14eb7-9731-4d22-95c2-dff4f33ef36d"
ZAKEN_ROOT = "https://api.zaken.nl/api/v1/"
ZAAK_URL = f"{ZAKEN_ROOT}zaken/482de5b2-4779-4b29-b84f-add888352182"
BRONORGANISATIE = "123456782"
IDENTIFICATIE = "ZAAK-001"


class AccessRequestPermissionsTests(APITestCase):
    def setUp(self) -> None:
        super().setUp()

        self.handler, self.requester = UserFactory.create_batch(2)
        self.client.force_authenticate(self.handler)

        Service.objects.create(api_type=APITypes.zrc, api_root=ZAKEN_ROOT)
        Service.objects.create(api_type=APITypes.ztc, api_root=CATALOGI_ROOT)
        self.zaaktype = generate_oas_component(
            "ztc",
            "schemas/ZaakType",
            url=f"{CATALOGI_ROOT}zaaktypen/17e08a91-67ff-401d-aae1-69b1beeeff06",
            identificatie="ZT1",
            catalogus=CATALOGUS_URL,
        )
        self.zaak = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=ZAAK_URL,
            bronorganisatie=BRONORGANISATIE,
            identificatie=IDENTIFICATIE,
            zaaktype=self.zaaktype["url"],
        )

        self.endpoint = reverse("accounts:accounts:grant-zaak-access")
        self.data = {
            "requester": self.requester.username,
            "zaak": ZAAK_URL,
            "comment": "some comment",
        }

    @requests_mock.Mocker()
    def test_has_permission(self, m):
        # mock ZTC and ZRC data
        mock_service_oas_get(m, CATALOGI_ROOT, "ztc")
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        m.get(
            f"{CATALOGI_ROOT}zaaktypen?catalogus={CATALOGUS_URL}",
            json=paginated_response([self.zaaktype]),
        )
        m.get(ZAAK_URL, json=self.zaak)

        PermissionSetFactory.create(
            permissions=[zaken_handle_access.name],
            for_user=self.handler,
            catalogus=CATALOGUS_URL,
            zaaktype_identificaties=["ZT1"],
            max_va=VertrouwelijkheidsAanduidingen.zeer_geheim,
        )

        response = self.client.post(self.endpoint, self.data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @requests_mock.Mocker()
    def test_has_permission_but_for_other_zaaktype(self, m):
        # mock ZTC and ZRC data
        mock_service_oas_get(m, CATALOGI_ROOT, "ztc")
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        m.get(
            f"{CATALOGI_ROOT}zaaktypen?catalogus={CATALOGUS_URL}",
            json=paginated_response([self.zaaktype]),
        )
        m.get(ZAAK_URL, json=self.zaak)
        m.get(f"{ZAKEN_ROOT}rollen?zaak={ZAAK_URL}", json=paginated_response([]))

        PermissionSetFactory.create(
            permissions=[zaken_handle_access.name],
            for_user=self.handler,
            catalogus=CATALOGUS_URL,
            zaaktype_identificaties=["ZT2"],
            max_va=VertrouwelijkheidsAanduidingen.zeer_geheim,
        )

        response = self.client.post(self.endpoint, self.data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @requests_mock.Mocker()
    def test_zaak_behandelaar(self, m):
        # mock ZTC and ZRC data
        rol = {
            "url": f"{ZAKEN_ROOT}rollen/b80022cf-6084-4cf6-932b-799effdcdb26",
            "zaak": self.zaak["url"],
            "betrokkene": None,
            "betrokkeneType": "medewerker",
            "roltype": f"{CATALOGI_ROOT}roltypen/bfd62804-f46c-42e7-a31c-4139b4c661ac",
            "omschrijving": "zaak behandelaar",
            "omschrijvingGeneriek": "behandelaar",
            "roltoelichting": "some description",
            "registratiedatum": "2020-09-01T00:00:00Z",
            "indicatieMachtiging": "",
            "betrokkeneIdentificatie": {
                "identificatie": self.handler.username,
            },
        }
        mock_service_oas_get(m, CATALOGI_ROOT, "ztc")
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        m.get(
            f"{CATALOGI_ROOT}zaaktypen?catalogus={CATALOGUS_URL}",
            json=paginated_response([self.zaaktype]),
        )
        m.get(ZAAK_URL, json=self.zaak)
        m.get(f"{ZAKEN_ROOT}rollen?zaak={ZAAK_URL}", json=paginated_response([rol]))

        response = self.client.post(self.endpoint, self.data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_no_permissions(self):
        response = self.client.post(self.endpoint, self.data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


@freeze_time("2020-01-01")
class AccessRequestAPITests(APITransactionTestCase):
    """
    Test GrantZaakAccessView
    """

    def setUp(self) -> None:
        super().setUp()

        self.handler = SuperUserFactory.create()
        self.requester = UserFactory.create()

        Service.objects.create(api_type=APITypes.zrc, api_root=ZAKEN_ROOT)
        self.zaak = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=ZAAK_URL,
            bronorganisatie=BRONORGANISATIE,
            identificatie=IDENTIFICATIE,
            zaaktype=f"{CATALOGI_ROOT}zaaktypen/17e08a91-67ff-401d-aae1-69b1beeeff06",
        )

        self.client.force_authenticate(self.handler)
        self.endpoint = reverse("accounts:accounts:grant-zaak-access")

    @requests_mock.Mocker()
    def test_grant_access_success(self, m):
        # mock ZRC data
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        m.get(ZAAK_URL, json=self.zaak)

        data = {
            "requester": self.requester.username,
            "zaak": ZAAK_URL,
            "comment": "some comment",
        }

        response = self.client.post(self.endpoint, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AccessRequest.objects.count(), 1)

        access_request = AccessRequest.objects.get()

        self.assertEqual(access_request.handler, self.handler)
        self.assertEqual(access_request.requester, self.requester)
        self.assertEqual(access_request.zaak, ZAAK_URL)
        self.assertEqual(access_request.result, AccessRequestResult.approve)
        self.assertEqual(access_request.comment, "some comment")
        self.assertEqual(access_request.start_date, date(2020, 1, 1))
        self.assertIsNone(access_request.end_date)

        data = response.json()

        self.assertEqual(
            data,
            {
                "requester": self.requester.username,
                "handler": self.handler.username,
                "zaak": ZAAK_URL,
                "comment": "some comment",
                "result": AccessRequestResult.approve,
                "startDate": "2020-01-01",
                "endDate": None,
            },
        )

        # test email
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        subject = _("Access Request to %(zaak)s") % {"zaak": IDENTIFICATIE}
        self.assertEqual(email.subject, subject)
        self.assertEqual(email.to, [self.requester.email])

        zaak_detail_path = reverse(
            "core:zaak-detail",
            kwargs={
                "bronorganisatie": BRONORGANISATIE,
                "identificatie": IDENTIFICATIE,
            },
        )
        url = f"http://testserver{zaak_detail_path}"
        self.assertIn(url, email.body)

    def test_grant_access_no_user(self):
        data = {
            "requester": "some user",
            "zaak": ZAAK_URL,
            "comment": "some comment",
        }

        response = self.client.post(self.endpoint, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("requester" in response.json())

    def test_grant_access_with_existing_approved_request(self):
        AccessRequestFactory.create(
            requester=self.requester,
            result=AccessRequestResult.approve,
            zaak=ZAAK_URL,
            end_date=None,
        )
        data = {
            "requester": self.requester.username,
            "zaak": ZAAK_URL,
            "comment": "some comment",
        }

        response = self.client.post(self.endpoint, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["nonFieldErrors"],
            [
                f"User {self.requester.username} already has an access to zaak {ZAAK_URL}"
            ],
        )

    @requests_mock.Mocker()
    def test_grant_access_with_existing_approved_request_expired(self, m):
        # mock ZRC data
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        m.get(ZAAK_URL, json=self.zaak)

        AccessRequestFactory.create(
            requester=self.requester,
            result=AccessRequestResult.approve,
            zaak=ZAAK_URL,
            end_date=date(2019, 12, 31),
        )
        data = {
            "requester": self.requester.username,
            "zaak": ZAAK_URL,
            "comment": "some comment",
        }

        response = self.client.post(self.endpoint, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.requester.initiated_requests.actual().count(), 1)

        actual_access_request = self.requester.initiated_requests.actual().get()

        self.assertIsNone(actual_access_request.end_date)
        self.assertEqual(actual_access_request.result, AccessRequestResult.approve)
        self.assertEqual(actual_access_request.comment, "some comment")

        # check email
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, [self.requester.email])

    @requests_mock.Mocker()
    def test_grant_access_with_existing_pending_request(self, m):
        # mock ZRC data
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        m.get(ZAAK_URL, json=self.zaak)

        pending_request = AccessRequestFactory.create(
            requester=self.requester, result="", zaak=ZAAK_URL
        )
        data = {
            "requester": self.requester.username,
            "zaak": ZAAK_URL,
            "comment": "some comment",
            "end_date": "2021-01-01",
        }

        response = self.client.post(self.endpoint, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.requester.initiated_requests.count(), 2)

        pending_request.refresh_from_db()
        new_request = AccessRequest.objects.exclude(id=pending_request.id).get()

        self.assertEqual(pending_request.result, AccessRequestResult.approve)
        self.assertEqual(pending_request.end_date, date(2021, 1, 1))
        self.assertEqual(
            pending_request.comment,
            f"Automatically approved after access request #{new_request.id}",
        )

        self.assertEqual(new_request.result, AccessRequestResult.approve)
        self.assertEqual(new_request.end_date, date(2021, 1, 1))
        self.assertEqual(new_request.comment, "some comment")

        # check email
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, [self.requester.email])
