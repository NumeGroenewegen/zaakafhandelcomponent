import uuid

from django.test import TestCase

import requests_mock
from rest_framework.authtoken.models import Token
from zgw_consumers.constants import APITypes
from zgw_consumers.models import Service

from zac.core.tests.utils import ClearCachesMixin
from zac.tests.utils import mock_service_oas_get

from ..models import Subscription
from ..subscriptions import subscribe_all


class SubscribeCommandTests(ClearCachesMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.nrc = Service.objects.create(
            api_root="https://some.nrc.nl/api/v1/", api_type=APITypes.nrc
        )

    @requests_mock.Mocker()
    def test_create_subscription(self, m):
        mock_service_oas_get(m, self.nrc.api_root, "nrc")
        m.post(
            "https://some.nrc.nl/api/v1/abonnement",
            status_code=201,
            json={"url": f"https://some.nrc.nl/api/v1/abonnement/{uuid.uuid4()}"},
        )

        result = subscribe_all("https://zac.example.com")

        self.assertEqual(len(result), 2)
        self.assertEqual(len(m.request_history), 3)

        token = Token.objects.get()
        self.assertEqual(
            m.last_request.json(),
            {
                "callbackUrl": "https://zac.example.com/api/v1/kownsl-callbacks",
                "auth": f"Token {token.key}",
                "kanalen": [
                    {
                        "naam": "kownsl",
                        "filters": {},
                    }
                ],
            },
        )
        self.assertEqual(Subscription.objects.count(), 2)

    @requests_mock.Mocker()
    def test_verify_existing(self, m):
        mock_service_oas_get(m, self.nrc.api_root, "nrc")
        existing = Subscription.objects.create(
            url=f"https://some.nrc.nl/api/v1/abonnement/{uuid.uuid4()}"
        )
        m.get(
            existing.url,
            json={
                "url": existing.url,
                "callbackUrl": "https://zac.example.com/api/v1/kownsl-callbacks",
                "auth": f"Token dummy",
                "kanalen": [
                    {
                        "naam": "kownsl",
                        "filters": {},
                    }
                ],
            },
        )
        m.post(
            "https://some.nrc.nl/api/v1/abonnement",
            status_code=201,
            json={"url": f"https://some.nrc.nl/api/v1/abonnement/{uuid.uuid4()}"},
        )

        result = subscribe_all("https://zac.example.com")

        self.assertEqual(len(result), 1)
        self.assertEqual(len(m.request_history), 3)

        token = Token.objects.get()
        self.assertEqual(
            m.last_request.json(),
            {
                "callbackUrl": "https://zac.example.com/api/v1/notification-callbacks",
                "auth": f"Token {token.key}",
                "kanalen": [
                    {
                        "naam": "zaken",
                        "filters": {},
                    }
                ],
            },
        )
        self.assertEqual(Subscription.objects.count(), 2)