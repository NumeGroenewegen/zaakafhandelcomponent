from datetime import date, datetime
from unittest.mock import patch

from django.contrib.sites.models import Site
from django.urls import reverse
from django.utils import timezone

import requests_mock
from freezegun import freeze_time
from rest_framework import status
from rest_framework.test import APITestCase, APITransactionTestCase
from zgw_consumers.api_models.base import factory
from zgw_consumers.constants import APITypes
from zgw_consumers.models import Service
from zgw_consumers.test import generate_oas_component, mock_service_oas_get

from zac.core.permissions import zaken_inzien
from zac.core.tests.utils import ClearCachesMixin
from zac.tests.utils import mock_resource_get
from zgw.models.zrc import Zaak

from ...constants import PermissionObjectTypeChoices
from ...models import AccessRequest
from ...tests.factories import (
    AccessRequestFactory,
    AtomicPermissionFactory,
    SuperUserFactory,
    UserAtomicPermissionFactory,
    UserFactory,
)

CATALOGI_ROOT = "https://api.catalogi.nl/api/v1/"
CATALOGUS_URL = f"{CATALOGI_ROOT}catalogi/dfb14eb7-9731-4d22-95c2-dff4f33ef36d"
ZAKEN_ROOT = "https://api.zaken.nl/api/v1/"
ZAAK_URL = f"{ZAKEN_ROOT}zaken/482de5b2-4779-4b29-b84f-add888352182"
BRONORGANISATIE = "123456782"
IDENTIFICATIE = "ZAAK-001"


class CreateAccessRequestPermissionsTests(ClearCachesMixin, APITestCase):
    def setUp(self) -> None:
        super().setUp()

        self.requester = UserFactory.create()
        self.client.force_authenticate(self.requester)

        Service.objects.create(api_type=APITypes.zrc, api_root=ZAKEN_ROOT)
        Service.objects.create(api_type=APITypes.ztc, api_root=CATALOGI_ROOT)
        self.zaaktype = generate_oas_component(
            "ztc",
            "schemas/ZaakType",
            url=f"{CATALOGI_ROOT}zaaktypen/17e08a91-67ff-401d-aae1-69b1beeeff06",
            identificatie="ZT1",
            catalogus=CATALOGUS_URL,
            omschrijving="ZT1",
        )
        self.zaak = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=ZAAK_URL,
            bronorganisatie=BRONORGANISATIE,
            identificatie=IDENTIFICATIE,
            zaaktype=self.zaaktype["url"],
        )
        zaak = factory(Zaak, self.zaak)

        self.endpoint = reverse("accessrequest-list")
        self.data = {
            "zaak": {
                "identificatie": IDENTIFICATIE,
                "bronorganisatie": BRONORGANISATIE,
            },
            "comment": "some comment",
        }
        find_zaak_patcher = patch(
            "zac.accounts.api.serializers.find_zaak", return_value=zaak
        )
        find_zaak_patcher.start()
        self.addCleanup(find_zaak_patcher.stop)

    @requests_mock.Mocker()
    def test_no_permissions(self, m):
        # mock ZTC and ZRC data
        mock_service_oas_get(m, CATALOGI_ROOT, "ztc")
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        mock_resource_get(m, self.zaaktype)
        mock_resource_get(m, self.zaak)

        response = self.client.post(self.endpoint, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


@freeze_time("2020-01-01")
class CreateAccessRequestAPITests(APITransactionTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.requester = SuperUserFactory.create()

        site = Site.objects.get_current()
        site.domain = "testserver"
        site.save()

        Service.objects.create(api_type=APITypes.zrc, api_root=ZAKEN_ROOT)
        self.zaak = generate_oas_component(
            "zrc",
            "schemas/Zaak",
            url=ZAAK_URL,
            bronorganisatie=BRONORGANISATIE,
            identificatie=IDENTIFICATIE,
            zaaktype=f"{CATALOGI_ROOT}zaaktypen/17e08a91-67ff-401d-aae1-69b1beeeff06",
        )
        zaak = factory(Zaak, self.zaak)
        self.client.force_authenticate(self.requester)
        self.endpoint = reverse("accessrequest-list")

        find_zaak_patcher = patch(
            "zac.accounts.api.serializers.find_zaak", return_value=zaak
        )
        find_zaak_patcher.start()
        self.addCleanup(find_zaak_patcher.stop)

    @requests_mock.Mocker()
    def test_request_access_success(self, m):
        # mock ZRC data
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        mock_resource_get(m, self.zaak)

        data = {
            "zaak": {
                "identificatie": IDENTIFICATIE,
                "bronorganisatie": BRONORGANISATIE,
            },
            "comment": "some comment",
        }

        response = self.client.post(self.endpoint, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AccessRequest.objects.count(), 1)

        access_request = AccessRequest.objects.get()

        self.assertIsNone(access_request.handler)
        self.assertEqual(access_request.requester, self.requester)
        self.assertEqual(access_request.zaak, ZAAK_URL)
        self.assertEqual(access_request.result, "")
        self.assertEqual(access_request.comment, "some comment")
        self.assertEqual(access_request.requested_date, date(2020, 1, 1))
        self.assertIsNone(access_request.handled_date)

        data = response.json()

        self.assertEqual(
            data,
            {
                "url": f"http://testserver{reverse('accessrequest-detail', args=[access_request.id])}",
                "requester": self.requester.username,
                "zaak": {
                    "url": ZAAK_URL,
                    "identificatie": IDENTIFICATIE,
                    "bronorganisatie": BRONORGANISATIE,
                },
                "comment": "some comment",
            },
        )

    def test_request_access_with_existing_permission(self):
        AtomicPermissionFactory.create(
            object_url=ZAAK_URL,
            object_type=PermissionObjectTypeChoices.zaak,
            permission=zaken_inzien.name,
            for_user=self.requester,
        )
        data = {
            "zaak": {
                "identificatie": IDENTIFICATIE,
                "bronorganisatie": BRONORGANISATIE,
            },
            "comment": "some comment",
        }

        response = self.client.post(self.endpoint, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["nonFieldErrors"],
            [
                f"Gebruiker `{self.requester.username}` heeft al toegang tot ZAAK `{ZAAK_URL}`."
            ],
        )

    @requests_mock.Mocker()
    def test_request_access_with_existing_permission_expired(self, m):
        # mock ZRC data
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        mock_resource_get(m, self.zaak)

        UserAtomicPermissionFactory.create(
            atomic_permission__object_url=ZAAK_URL,
            atomic_permission__object_type=PermissionObjectTypeChoices.zaak,
            atomic_permission__permission=zaken_inzien.name,
            user=self.requester,
            end_date=timezone.make_aware(datetime(2019, 12, 31)),
        )
        data = {
            "zaak": {
                "identificatie": IDENTIFICATIE,
                "bronorganisatie": BRONORGANISATIE,
            },
            "comment": "some comment",
        }

        response = self.client.post(self.endpoint, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AccessRequest.objects.count(), 1)

        access_request = AccessRequest.objects.get()

        self.assertEqual(access_request.requester, self.requester)
        self.assertIsNone(access_request.handled_date)
        self.assertEqual(access_request.result, "")
        self.assertEqual(access_request.comment, "some comment")

    @requests_mock.Mocker()
    def test_request_access_with_existing_pending_request(self, m):
        # mock ZRC data
        mock_service_oas_get(m, ZAKEN_ROOT, "zrc")
        mock_resource_get(m, self.zaak)

        AccessRequestFactory.create(requester=self.requester, result="", zaak=ZAAK_URL)
        data = {
            "requester": self.requester.username,
            "zaak": {
                "identificatie": IDENTIFICATIE,
                "bronorganisatie": BRONORGANISATIE,
            },
            "comment": "some comment",
            "end_date": "2021-01-01",
        }

        response = self.client.post(self.endpoint, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json()["nonFieldErrors"],
            [
                f"Er is al een toegangsverzoek tot ZAAK `{ZAAK_URL}` voor gebruiker `{self.requester.username}` in behandeling."
            ],
        )
