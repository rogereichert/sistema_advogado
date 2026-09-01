from django.urls import path

from . import views


app_name = "clients"


urlpatterns = [
    path(
        "",
        views.client_list,
        name="list",
    ),

    path(
        "novo/",
        views.client_create,
        name="create",
    ),

    path(
        "<int:pk>/",
        views.client_detail,
        name="detail",
    ),
]