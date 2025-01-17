from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, List, Optional, Union

from django.conf import settings
from django.contrib.auth.models import Group
from django.utils.translation import ugettext_lazy as _

from furl import furl
from rest_framework import serializers
from zgw_consumers.api_models.documenten import Document
from zgw_consumers.drf.serializers import APIModelSerializer

from zac.accounts.api.serializers import GroupSerializer, UserSerializer
from zac.accounts.models import User
from zac.accounts.permission_loaders import add_permissions_for_advisors
from zac.api.context import get_zaak_context
from zac.camunda.constants import AssigneeTypeChoices
from zac.camunda.data import Task
from zac.camunda.user_tasks import Context, register, usertask_context_serializer
from zac.contrib.dowc.constants import DocFileTypes
from zac.contrib.dowc.fields import DowcUrlFieldReadOnly
from zac.core.api.fields import SelectDocumentsField
from zac.core.camunda.utils import resolve_assignee
from zac.core.utils import build_absolute_url
from zgw.models.zrc import Zaak

from .api import create_review_request
from .constants import FORM_KEY_REVIEW_TYPE_MAPPING, KownslTypes


@dataclass
class UsersRevReq:
    user_assignees: List[Optional[User]]
    group_assignees: List[Optional[Group]]


@dataclass
class AdviceApprovalContext(Context):
    title: str
    zaak_informatie: Zaak
    documents: List[Document]
    review_type: str
    assigned_users: UsersRevReq


class ZaakInformatieTaskSerializer(APIModelSerializer):
    class Meta:
        model = Zaak
        fields = (
            "omschrijving",
            "toelichting",
        )


class DocumentUserTaskSerializer(APIModelSerializer):
    read_url = DowcUrlFieldReadOnly(purpose=DocFileTypes.read)

    class Meta:
        model = Document
        fields = (
            "beschrijving",
            "bestandsnaam",
            "read_url",
            "url",
        )


class UsersRevReqSerializer(APIModelSerializer):
    """
    Allows users or groups to be assigned from within the camunda process.

    """

    user_assignees = UserSerializer(many=True)
    group_assignees = GroupSerializer(many=True)

    class Meta:
        model = UsersRevReq
        fields = (
            "user_assignees",
            "group_assignees",
        )


@usertask_context_serializer
class AdviceApprovalContextSerializer(APIModelSerializer):
    documents = DocumentUserTaskSerializer(many=True)
    zaak_informatie = ZaakInformatieTaskSerializer()
    review_type = serializers.ChoiceField(
        choices=KownslTypes.choices,
    )
    assigned_users = UsersRevReqSerializer(
        help_text=_("Users or groups assigned from within the camunda process.")
    )

    class Meta:
        model = AdviceApprovalContext
        fields = (
            "documents",
            "title",
            "zaak_informatie",
            "review_type",
            "assigned_users",
        )


#
# Write serializers
#


@dataclass
class SelectUsersRevReq(UsersRevReq):
    deadline: date
    email_notification: bool = False


class SelectUsersRevReqSerializer(APIModelSerializer):
    """
    Select users or groups and assign deadlines to those users in the configuration of
    review requests such as the advice and approval review requests.

    """

    user_assignees = serializers.SlugRelatedField(
        slug_field="username",
        queryset=User.objects.all(),
        help_text=_("Users assigned to the review request."),
        many=True,
        allow_null=True,
        required=True,
    )
    group_assignees = serializers.SlugRelatedField(
        slug_field="name",
        queryset=Group.objects.all(),
        help_text=_("Groups assigned to the review request."),
        many=True,
        allow_null=True,
        required=True,
    )
    email_notification = serializers.BooleanField(
        default=False,
        help_text=_("Send an email notification about the review request."),
    )
    deadline = serializers.DateField(
        input_formats=["%Y-%m-%d"],
        help_text=_("On this date the review must be submitted."),
    )

    class Meta:
        model = SelectUsersRevReq
        fields = [
            "user_assignees",
            "group_assignees",
            "email_notification",
            "deadline",
        ]

    def validate_user_assignees(self, user_assignees):
        if len(user_assignees) > len(set(user_assignees)):
            raise serializers.ValidationError("Assigned users need to be unique.")
        return user_assignees

    def validate_group_assignees(self, group_assignees):
        if len(group_assignees) > len(set(group_assignees)):
            raise serializers.ValidationError("Assigned groups need to be unique.")
        return group_assignees

    def validate(self, attrs):
        if not attrs["group_assignees"] and not attrs["user_assignees"]:
            raise serializers.ValidationError(
                "You need to select either a user or a group."
            )
        return attrs


@dataclass
class ConfigureReviewRequest:
    assigned_users: List[SelectUsersRevReq]
    selected_documents: List[str]
    toelichting: str


class ConfigureReviewRequestSerializer(APIModelSerializer):
    """
    This serializes configure review requests such as
    advice and approval review requests.

    Must have a ``task`` and ``request`` in its ``context``.
    """

    assigned_users = SelectUsersRevReqSerializer(many=True)
    selected_documents = SelectDocumentsField()
    toelichting = serializers.CharField(
        label=_("Toelichting"),
        allow_blank=True,
    )

    class Meta:
        model = ConfigureReviewRequest
        fields = (
            "assigned_users",
            "selected_documents",
            "toelichting",
        )

    def get_zaak_from_context(self):
        zaak_context = get_zaak_context(self.context["task"])
        return zaak_context.zaak

    def validate_assigned_users(self, assigned_users) -> List:
        """
        Validate that:
            assigned users and groups are unique,
            at least 1 user or group is selected per step, and
            deadlines monotonically increase per step.
        """
        users_list = []
        groups_list = []
        for data in assigned_users:
            if not data["user_assignees"] and not data["group_assignees"]:
                raise serializers.ValidationError(
                    _("Please select at least 1 user or group."),
                    code="empty-assignees",
                )

            if any([user in users_list for user in data["user_assignees"]]):
                raise serializers.ValidationError(
                    _(
                        "Users in a serial review request process need to be unique. Please select unique users."
                    ),
                    code="unique-users",
                )

            if any([group in groups_list for group in data["group_assignees"]]):
                raise serializers.ValidationError(
                    _(
                        "Groups in a serial review request process need to be unique. Please select unique groups."
                    ),
                    code="unique-groups",
                )

            users_list.extend(data["user_assignees"])
            groups_list.extend(data["group_assignees"])

        deadline_old = date.today() - timedelta(days=1)
        for data in assigned_users:
            deadline_new = data["deadline"]
            if deadline_new and not deadline_new > deadline_old:
                raise serializers.ValidationError(
                    _(
                        "Deadlines are not allowed to be equal in a serial review request "
                        "process but need to have at least 1 day in between them. "
                        "Please select a date greater than {minimum_date}."
                    ).format(minimum_date=deadline_old.strftime("%Y-%m-%d")),
                    code="invalid-date",
                )
            deadline_old = deadline_new

        return assigned_users

    def on_task_submission(self) -> None:
        """
        On task submission create the review request in the kownsl.
        """
        assert self.is_valid(), "Serializer must be valid"

        count_users = sum(
            [
                len(data["user_assignees"] or []) + len(data["group_assignees"] or [])
                for data in self.validated_data["assigned_users"]
            ]
        )

        user_deadlines = {
            assignee: str(data["deadline"])
            for data in self.validated_data["assigned_users"]
            for assignee in (
                [
                    f"{AssigneeTypeChoices.user}:{user}"
                    for user in data["user_assignees"]
                ]
            )
            + (
                [
                    f"{AssigneeTypeChoices.group}:{group}"
                    for group in data["group_assignees"]
                ]
            )
        }

        # Derive review_type from task.form_key
        review_type = FORM_KEY_REVIEW_TYPE_MAPPING[self.context["task"].form_key]
        zaak = self.get_zaak_from_context()
        self.review_request = create_review_request(
            zaak.url,
            self.context["request"].user,
            documents=self.validated_data["selected_documents"],
            review_type=review_type,
            num_assigned_users=count_users,
            toelichting=self.validated_data["toelichting"],
            user_deadlines=user_deadlines,
        )
        # add permission for advisors to see the zaak-detail page
        add_permissions_for_advisors(self.review_request)

    def get_process_variables(self) -> Dict[str, Union[List, str]]:
        """
        Get the required BPMN process variables for the BPMN.
        """
        # Assert is_valid has been called so that we can access validated data.
        assert hasattr(
            self, "review_request"
        ), "Must call on_task_submission before getting process variables."

        kownsl_frontend_url = furl(settings.UI_ROOT_URL)
        kownsl_frontend_url.path.segments += [
            "kownsl",
            "review-request",
            self.review_request.review_type,
        ]
        kownsl_frontend_url = build_absolute_url(
            kownsl_frontend_url.url,
            params={"uuid": self.review_request.id},
        )

        kownsl_users_list = []
        email_notification_list = {}
        for data in self.validated_data["assigned_users"]:
            users = [
                f"{AssigneeTypeChoices.user}:{user}" for user in data["user_assignees"]
            ] + [
                f"{AssigneeTypeChoices.group}:{group}"
                for group in data["group_assignees"]
            ]

            kownsl_users_list.append(users)
            for user in users:
                email_notification_list[user] = data["email_notification"]

        return {
            "kownslDocuments": self.validated_data["selected_documents"],
            "kownslUsersList": kownsl_users_list,
            "kownslReviewRequestId": str(self.review_request.id),
            "kownslFrontendUrl": kownsl_frontend_url,
            "emailNotificationList": email_notification_list,
        }


def get_camunda_assigned_users(task: Task) -> Dict[str, List]:
    camunda_assigned_users = task.get_variable("assignedUsers", "")
    assigned_users = {
        "user_assignees": [],
        "group_assignees": [],
    }
    for assignee in camunda_assigned_users:
        assignee = resolve_assignee(assignee)
        if isinstance(assignee, Group):
            assigned_users["group_assignees"].append(assignee)
        else:
            assigned_users["user_assignees"].append(assignee)
    return assigned_users


@register(
    "zac:configureAdviceRequest",
    AdviceApprovalContextSerializer,
    ConfigureReviewRequestSerializer,
)
def get_advice_context(task: Task) -> AdviceApprovalContext:
    zaak_context = get_zaak_context(task, require_zaaktype=True, require_documents=True)
    return AdviceApprovalContext(
        documents=zaak_context.documents,
        review_type=KownslTypes.advice,
        title=f"{zaak_context.zaaktype.omschrijving} - {zaak_context.zaaktype.versiedatum}",
        zaak_informatie=zaak_context.zaak,
        assigned_users=get_camunda_assigned_users(task),
    )


@register(
    "zac:configureApprovalRequest",
    AdviceApprovalContextSerializer,
    ConfigureReviewRequestSerializer,
)
def get_approval_context(task: Task) -> AdviceApprovalContext:
    zaak_context = get_zaak_context(task, require_zaaktype=True, require_documents=True)
    return AdviceApprovalContext(
        documents=zaak_context.documents,
        review_type=KownslTypes.approval,
        title=f"{zaak_context.zaaktype.omschrijving} - {zaak_context.zaaktype.versiedatum}",
        zaak_informatie=zaak_context.zaak,
        assigned_users=get_camunda_assigned_users(task),
    )
