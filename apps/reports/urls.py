from django.urls import path

from . import views


app_name = "reports"


urlpatterns = [
    path(
        "cliente/<int:client_pk>/dossie/",
        views.client_dossier,
        name="client_dossier",
    ),
]