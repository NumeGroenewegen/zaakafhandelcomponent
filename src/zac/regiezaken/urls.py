from django.urls import path

from .views import IndexView, RegieZaakDetailView

app_name = 'regiezaken'

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    # path("login/", LoginView.as_view(), name="login"),
    path("regiezaken/<pk>/", RegieZaakDetailView.as_view(), name="regiezaak-detail"),
]
