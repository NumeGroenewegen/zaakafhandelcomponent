import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import get_template
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from zac.core.services import get_zaak

from .models import AccessRequest

logger = logging.getLogger(__name__)


def send_email_to_requester(access_request: AccessRequest, request=None):
    user = access_request.requester

    if not user.email:
        logger.warning("Email to %s can't be sent - no known e-mail", user)
        return

    zaak = get_zaak(zaak_url=access_request.zaak)
    zaak_url = reverse(
        "core:zaak-detail",
        kwargs={
            "bronorganisatie": zaak.bronorganisatie,
            "identificatie": zaak.identificatie,
        },
    )
    if request:
        zaak_url = request.build_absolute_uri(zaak_url)

    zaak.absolute_url = zaak_url

    email_template = get_template("core/emails/access_request_result.txt")
    email_context = {
        "zaak": zaak,
        "access_request": access_request,
        "user": user,
    }

    message = email_template.render(email_context)
    send_mail(
        subject=_("Access Request to %(zaak)s") % {"zaak": zaak.identificatie},
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )
