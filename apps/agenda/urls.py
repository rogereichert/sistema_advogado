from django.urls import path

from . import views


app_name = "agenda"


urlpatterns = [
    path(
        "",
        views.agenda_list,
        name="list",
    ),

    path(
        "caso/<int:case_pk>/novo/",
        views.agenda_create,
        name="create",
    ),

    path(
        "<int:pk>/editar/",
        views.agenda_update,
        name="update",
    ),
]