from django.urls import path

from . import views


app_name = "cases"


urlpatterns = [
    path(
        "novo/<int:client_pk>/",
        views.case_create,
        name="create",
    ),

    path(
        "<int:pk>/",
        views.case_detail,
        name="detail",
    ),

    path(
        "<int:pk>/editar/",
        views.case_update,
        name="update",
    ),

    path(
        "<int:pk>/movimentacoes/nova/",
        views.movement_create,
        name="movement_create",
    ),

    path(
        "",
        views.case_list,
        name="list",
    ),
]