from django.urls import reverse

import requests_mock
from rest_framework import status
from rest_framework.test import APITestCase
from zgw_consumers.constants import APITypes
from zgw_consumers.models import Service
from zgw_consumers.test import mock_service_oas_get

from zac.accounts.tests.factories import UserFactory
from zac.core.models import CoreConfig
from zac.core.tests.utils import ClearCachesMixin

OBJECTTYPES_ROOT = "http://objecttype.nl/api/v1/"
OBJECTS_ROOT = "http://object.nl/api/v1/"


@requests_mock.Mocker()
class ObjecttypesListTests(ClearCachesMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.objecttypes_service = Service.objects.create(
            api_type=APITypes.orc, api_root=OBJECTTYPES_ROOT
        )

        cls.objecttype_1 = {
            "url": f"{OBJECTTYPES_ROOT}objecttypes/1",
            "name": "tree",
            "namePlural": "trees",
            "description": "",
            "data_classification": "",
            "maintainer_organization": "",
            "maintainer_department": "",
            "contact_person": "",
            "contact_email": "",
            "source": "",
            "update_frequency": "",
            "provider_organization": "",
            "documentation_url": "",
            "labels": {},
            "created_at": "2019-08-24",
            "modified_at": "2019-08-24",
            "versions": [],
        }
        cls.objecttype_2 = {
            "url": f"{OBJECTTYPES_ROOT}objecttypes/2",
            "name": "bin",
            "namePlural": "bins",
            "description": "",
            "data_classification": "",
            "maintainer_organization": "",
            "maintainer_department": "",
            "contact_person": "",
            "contact_email": "",
            "source": "",
            "update_frequency": "",
            "provider_organization": "",
            "documentation_url": "",
            "labels": {},
            "created_at": "2019-08-24",
            "modified_at": "2019-08-24",
            "versions": [],
        }

    def test_not_authenticated(self, m):
        list_url = reverse("objecttypes-list")
        response = self.client.get(list_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_objecttypes(self, m):
        mock_service_oas_get(m, OBJECTTYPES_ROOT, "objecttypes")
        m.get(
            f"{OBJECTTYPES_ROOT}objecttypes",
            json=[self.objecttype_1, self.objecttype_2],
        )

        config = CoreConfig.get_solo()
        config.primary_objecttypes_api = self.objecttypes_service
        config.save()

        list_url = reverse("objecttypes-list")
        user = UserFactory.create()

        self.client.force_authenticate(user=user)
        response = self.client.get(list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(2, len(response.json()))


@requests_mock.Mocker()
class ObjecttypeVersionTests(ClearCachesMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.objecttypes_service = Service.objects.create(
            api_type=APITypes.orc, api_root=OBJECTTYPES_ROOT
        )

        cls.objecttype_version = {
            "url": f"{OBJECTTYPES_ROOT}objecttypes/e0346ea0-75aa-47e0-9283-cfb35963b725/versions/0",
            "version": 0,
            "object_type": f"{OBJECTTYPES_ROOT}objecttypes/e0346ea0-75aa-47e0-9283-cfb35963b725",
            "status": "published",
            "json_schema": {"title": "Restaurant"},
            "created_at": "2019-08-24",
            "modified_at": "2019-08-24",
            "published_at": "2019-08-24",
        }

    def test_not_authenticated(self, m):
        list_url = reverse(
            "objecttypesversion-read",
            kwargs={"uuid": "e0346ea0-75aa-47e0-9283-cfb35963b725", "version": "1"},
        )
        response = self.client.get(list_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_read_objecttype_version(self, m):
        mock_service_oas_get(m, OBJECTTYPES_ROOT, "objecttypes")
        m.get(
            f"{OBJECTTYPES_ROOT}objecttypes/e0346ea0-75aa-47e0-9283-cfb35963b725/versions/1",
            json=self.objecttype_version,
        )

        config = CoreConfig.get_solo()
        config.primary_objecttypes_api = self.objecttypes_service
        config.save()

        list_url = reverse(
            "objecttypesversion-read",
            kwargs={"uuid": "e0346ea0-75aa-47e0-9283-cfb35963b725", "version": "1"},
        )
        user = UserFactory.create()

        self.client.force_authenticate(user=user)
        response = self.client.get(list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        result = response.json()

        self.assertEqual(0, result["version"])
        self.assertEqual({"title": "Restaurant"}, result["jsonSchema"])


@requests_mock.Mocker()
class ObjectSearchTests(ClearCachesMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.objects_service = Service.objects.create(
            api_type=APITypes.orc, api_root=OBJECTS_ROOT
        )

        cls.object = {
            "url": f"{OBJECTS_ROOT}objects/e0346ea0-75aa-47e0-9283-cfb35963b725",
            "type": f"{OBJECTTYPES_ROOT}objecttypes/1",
            "record": {
                "index": 1,
                "typeVersion": 1,
                "data": {
                    "type": "Laadpaal",
                    "adres": "Utrechtsestraat 41",
                    "status": "Laadpaal in ontwikkeling",
                    "objectid": 2,
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [5.114160150114911, 52.08850095597628],
                },
                "startAt": "2021-07-09",
                "endAt": None,
                "registrationAt": "2021-07-09",
                "correctionFor": None,
                "correctedBy": None,
            },
        }

    def test_not_authenticated(self, m):
        list_url = reverse("object-search")
        response = self.client.get(list_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_filter(self, m):
        mock_service_oas_get(m, OBJECTS_ROOT, "objects")
        m.post(f"{OBJECTS_ROOT}objects/search", status_code=400)

        config = CoreConfig.get_solo()
        config.primary_objects_api = self.objects_service
        config.save()

        user = UserFactory.create()
        self.client.force_authenticate(user=user)

        list_url = reverse("object-search")
        response = self.client.post(
            list_url, {"geometry": {"within": {"type": "Polygon", "coordinates": [[]]}}}
        )

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_filter(self, m):
        mock_service_oas_get(m, OBJECTS_ROOT, "objects")
        m.post(f"{OBJECTS_ROOT}objects/search", json=[self.object])

        config = CoreConfig.get_solo()
        config.primary_objects_api = self.objects_service
        config.save()

        user = UserFactory.create()
        self.client.force_authenticate(user=user)

        list_url = reverse("object-search")
        response = self.client.post(
            list_url,
            {
                "geometry": {
                    "within": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [5.040241219103334, 52.09434351690135],
                                [5.145297981798648, 52.13018632964422],
                                [5.196109749376771, 52.07409013759298],
                                [5.084873177111147, 52.0386246041859],
                                [5.040241219103334, 52.09434351690135],
                            ]
                        ],
                    }
                },
                "type": f"{OBJECTTYPES_ROOT}objecttypes/1",
                "data_attrs": "adres__exact__Utrechtsestraat 41",
                "date": "2021-07-19",
            },
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(1, len(response.json()))