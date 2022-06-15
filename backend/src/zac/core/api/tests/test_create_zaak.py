from unittest.mock import patch

from django.test import override_settings
from django.urls import reverse

import requests_mock
from django_camunda.models import CamundaConfig
from requests.exceptions import HTTPError
from rest_framework import status
from rest_framework.test import APITestCase
from zgw_consumers.api_models.base import factory
from zgw_consumers.api_models.catalogi import ZaakType
from zgw_consumers.api_models.constants import VertrouwelijkheidsAanduidingen
from zgw_consumers.constants import APITypes
from zgw_consumers.models import Service
from zgw_consumers.test import generate_oas_component, mock_service_oas_get

from zac.accounts.tests.factories import (
    BlueprintPermissionFactory,
    SuperUserFactory,
    UserFactory,
)
from zac.core.permissions import zaken_aanmaken, zaken_inzien
from zac.core.tests.utils import ClearCachesMixin
from zac.tests.utils import mock_resource_get

CATALOGI_ROOT = "http://catalogus.nl/api/v1/"
ZAKEN_ROOT = "http://zaken.nl/api/v1/"
KOWNSL_ROOT = "https://kownsl.nl/"


@requests_mock.Mocker()
class CreateZaakPermissionTests(ClearCachesMixin, APITestCase):
    """
    Test the permissions for zaak-create endpoint.

    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        Service.objects.create(api_type=APITypes.ztc, api_root=CATALOGI_ROOT)
        catalogus_url = (
            f"{CATALOGI_ROOT}/catalogussen/e13e72de-56ba-42b6-be36-5c280e9b30cd"
        )
        cls._zaaktype = generate_oas_component(
            "ztc",
            "schemas/ZaakType",
            url=f"{CATALOGI_ROOT}zaaktypen/3e2a1218-e598-4bbe-b520-cb56b0584d60",
            identificatie="ZT1",
            catalogus=catalogus_url,
            vertrouwelijkheidaanduiding=VertrouwelijkheidsAanduidingen.openbaar,
            omschrijving="ZT1",
        )
        cls.zaaktype = factory(ZaakType, cls._zaaktype)
        cls.create_zaak_url = reverse(
            "zaak-create",
        )
        cls.data = {
            "zaaktype": cls.zaaktype.url,
            "omschrijving": "some-omschrijving",
            "toelichting": "some-toelichting",
        }
        cls.user = UserFactory.create()

    def test_not_authenticated(self, m):
        response = self.client.post(self.create_zaak_url, self.data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_no_permissions(self, m):
        mock_service_oas_get(m, CATALOGI_ROOT, "ztc")
        mock_resource_get(m, self._zaaktype)

        self.client.force_authenticate(user=self.user)

        response = self.client.post(self.create_zaak_url, self.data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_has_other_perm(self, m):
        mock_service_oas_get(m, CATALOGI_ROOT, "ztc")
        mock_resource_get(m, self._zaaktype)
        BlueprintPermissionFactory.create(
            role__permissions=[zaken_inzien.name],
            for_user=self.user,
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.create_zaak_url, self.data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_has_perm_to_create(self, m):
        mock_service_oas_get(m, CATALOGI_ROOT, "ztc")
        mock_resource_get(m, self._zaaktype)
        user = UserFactory.create()
        BlueprintPermissionFactory.create(
            role__permissions=[zaken_aanmaken.name],
            for_user=self.user,
        )
        self.client.force_authenticate(user=self.user)
        with patch(
            "zac.core.api.views.start_process",
            return_value={"instance_id": "some-uuid", "instance_url": "some-url"},
        ):
            response = self.client.post(self.create_zaak_url, self.data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


@requests_mock.Mocker()
class CreateZaakResponseTests(ClearCachesMixin, APITestCase):
    """
    Test the API response body for zaak-create endpoint.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        Service.objects.create(api_type=APITypes.ztc, api_root=CATALOGI_ROOT)
        Service.objects.create(api_type=APITypes.zrc, api_root=ZAKEN_ROOT)
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

        cls.url = reverse(
            "zaak-create",
        )
        cls.user = SuperUserFactory.create()

        cls.data = {
            "zaaktype": cls.zaaktype["url"],
            "omschrijving": "some-omschrijving",
            "toelichting": "some-toelichting",
        }

    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.user)

    def test_create_zaak_wrong_organisatie_rsin(self, m):
        mock_service_oas_get(m, CATALOGI_ROOT, "ztc")
        mock_resource_get(m, self.zaaktype)
        response = self.client.post(
            self.url, {**self.data, "organisatie_rsin": "1234567890"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {
                "organisatieRsin": [
                    "A RSIN has 9 digits.",
                    "Zorg ervoor dat dit veld niet meer dan 9 karakters bevat.",
                ]
            },
        )

    def test_create_zaak_zaaktype_not_found(self, m):
        mock_service_oas_get(m, CATALOGI_ROOT, "ztc")
        m.get(self.zaaktype["url"], status_code=404, json={})
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {
                "zaaktype": [
                    "ZAAKTYPE can not be found for URL %s." % self.zaaktype["url"]
                ]
            },
        )

    @override_settings(
        CREATE_ZAAK_PROCESS_DEFINITION_KEY="some-model-that-does-not-exist"
    )
    def test_create_zaak_process_definition_not_found(self, m):
        mock_service_oas_get(m, CATALOGI_ROOT, "ztc")
        mock_resource_get(m, self.zaaktype)

        config = CamundaConfig.get_solo()
        config.root_url = "https://camunda.example.com/"
        config.rest_api_path = "engine-rest/"
        config.save()
        m.post(
            "https://camunda.example.com/engine-rest/process-definition/key/some-model-that-does-not-exist/start",
            status_code=404,
            json={
                "type": "InvalidRequestException",
                "message": "No matching definition with id some-model-that-does-not-exist",
            },
        )
        with self.assertRaises(HTTPError):
            response = self.client.post(self.url, self.data)

    @override_settings(CREATE_ZAAK_PROCESS_DEFINITION_KEY="some-model")
    def test_create_zaak(self, m):
        mock_service_oas_get(m, CATALOGI_ROOT, "ztc")
        mock_resource_get(m, self.zaaktype)

        config = CamundaConfig.get_solo()
        config.root_url = "https://camunda.example.com/"
        config.rest_api_path = "engine-rest/"
        config.save()
        m.post(
            "https://camunda.example.com/engine-rest/process-definition/key/some-model/start",
            status_code=201,
            json={
                "links": [{"rel": "self", "href": "https://some-url.com/"}],
                "id": "e13e72de-56ba-42b6-be36-5c280e9b30cd",
            },
        )
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.json(),
            {
                "instanceId": "e13e72de-56ba-42b6-be36-5c280e9b30cd",
                "instanceUrl": "https://some-url.com/",
            },
        )