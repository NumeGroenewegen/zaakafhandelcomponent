from django.utils.translation import ugettext_lazy as _

from djchoices import ChoiceItem, DjangoChoices


class AccessRequestResult(DjangoChoices):
    approve = ChoiceItem("approve", _("approved"))
    reject = ChoiceItem("reject", _("rejected"))


class PermissionObjectType(DjangoChoices):
    zaak = ChoiceItem("zaak", _("zaak"))
    document = ChoiceItem("document", _("document"))
    report = ChoiceItem("report", _("report"))


class PermissionReason(DjangoChoices):
    betrokkene = ChoiceItem("betrokkene", _("betrokkene"))
    toegang_verlenen = ChoiceItem("toegang verlenen", _("toegang verlenen"))
    activiteit = ChoiceItem("activiteit", _("activiteit"))
    adviser = ChoiceItem("adviser", _("adviser"))
    akkorder = ChoiceItem("akkorder", _("akkorder"))
