import logging
from typing import List, Union

from django.contrib.auth.models import Group

import requests
from django_camunda.camunda_models import factory
from django_camunda.client import get_client

from zac.accounts.models import User
from zac.camunda.constants import AssigneeTypeChoices
from zac.camunda.data import ProcessInstance, Task
from zac.camunda.forms import extract_task_form

logger = logging.getLogger(__name__)


# FIXME: cleanup
FORM_KEYS = {
    "zac:documentSelectie": True,
    "zac:gebruikerSelectie": True,
    "zac:configureAdviceRequest": True,
    "zac:configureApprovalRequest": True,
    "zac:startProcessForm": True,
    "zac:zetResultaat": True,
}


def resolve_assignee(name: str) -> Union[Group, User]:
    try:  # Encapsulate in a try-except to not cause breaking changes
        user_or_group, _name = name.split(":", 1)
        if user_or_group == AssigneeTypeChoices.group:
            try:
                group = Group.objects.get(name=_name)
            except Group.DoesNotExist:
                group = Group.objects.create(name=_name)
                logger.info(f"Created group {group.name}.")
            return group
        else:
            try:
                user = User.objects.get(username=_name)
            except User.DoesNotExist:
                user = User.objects.create_user(username=_name)
            return user
    except ValueError:
        try:
            user = User.objects.get(username=name)
        except User.DoesNotExist:
            user = User.objects.create_user(username=name)
        return user


def get_process_tasks(process: ProcessInstance) -> List[Task]:
    client = get_client()
    tasks = client.get("task", {"processInstanceId": process.id})
    tasks = factory(Task, tasks)

    for task in tasks:
        if task.assignee:
            task.assignee = resolve_assignee(task.assignee)

        task.form = extract_task_form(task, FORM_KEYS)
    return tasks


def get_process_zaak_url(
    process: ProcessInstance, zaak_url_variable: str = "zaakUrl"
) -> str:
    try:
        return process.get_variable(zaak_url_variable)
    except requests.RequestException as exc:
        if exc.response.status_code != 404:
            raise

    camunda_client = get_client()
    # search parent processes
    parent_processes_response = camunda_client.get(
        "process-instance", {"subProcessInstance": process.id}
    )
    if not parent_processes_response:
        raise RuntimeError(
            f"None of the (parent) processes had a {zaak_url_variable} process variable!"
        )

    parent_process = factory(ProcessInstance, parent_processes_response[0])
    return get_process_zaak_url(parent_process)
