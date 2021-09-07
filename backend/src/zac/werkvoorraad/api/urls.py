from django.urls import path

from .views import (
    WorkStackAccessRequestsView,
    WorkStackAdhocActivitiesView,
    WorkStackAssigneeCasesView,
    WorkStackGroupsTasksView,
    WorkStackUserTasksView,
)

app_name = "werkvoorraad"

urlpatterns = [
    path("cases", WorkStackAssigneeCasesView.as_view(), name="cases"),
    path("activities", WorkStackAdhocActivitiesView.as_view(), name="activities"),
    path("user-tasks", WorkStackUserTasksView.as_view(), name="user-tasks"),
    path("group-tasks", WorkStackGroupsTasksView.as_view(), name="group-tasks"),
    path(
        "access-requests",
        WorkStackAccessRequestsView.as_view(),
        name="access-requests",
    ),
]
