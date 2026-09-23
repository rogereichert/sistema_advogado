from django.urls import path

from . import views


app_name = "notifications"


urlpatterns = [
    # ==========================================================
    # CENTRAL DE NOTIFICAÇÕES
    # ==========================================================

    path(
        "",
        views.notification_list,
        name="list",
    ),

    # ==========================================================
    # AÇÕES
    # ==========================================================

    path(
        "<int:pk>/marcar-como-lida/",
        views.mark_as_read,
        name="mark_as_read",
    ),
    path(
        "marcar-todas-como-lidas/",
        views.mark_all_as_read,
        name="mark_all_as_read",
    ),
]