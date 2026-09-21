from django.urls import path

from . import views


app_name = "agenda"


urlpatterns = [
    # =========================================================
    # AGENDA
    # =========================================================

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

    # =========================================================
    # GOOGLE CALENDAR
    # =========================================================

    path(
        "google/conectar/",
        views.google_calendar_connect,
        name="google_connect",
    ),
    path(
        "google/callback/",
        views.google_calendar_callback,
        name="google_callback",
    ),
    path(
        "google/sincronizar/",
        views.google_calendar_sync,
        name="google_sync",
    ),

    # =========================================================
    # GOOGLE CALENDAR - REENVIO
    # =========================================================

    path(
        "<int:pk>/google/reenviar/",
        views.google_calendar_resend,
        name="google_resend",
    ),
]