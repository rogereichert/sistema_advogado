from django.urls import path

from . import views


app_name = "clients"


urlpatterns = [
    # Listagem de clientes
    path(
        "",
        views.client_list,
        name="list",
    ),

    # Cadastro de cliente
    path(
        "novo/",
        views.client_create,
        name="create",
    ),

    # Edição de cliente
    path(
        "<int:pk>/editar/",
        views.client_update,
        name="update",
    ),

    # Detalhes do cliente
    path(
        "<int:pk>/",
        views.client_detail,
        name="detail",
    ),
]