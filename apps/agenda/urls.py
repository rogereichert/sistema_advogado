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
    # AÇÕES DO COMPROMISSO
    # =========================================================

    path(
        "<int:pk>/concluir/",
        views.agenda_complete,
        name="complete",
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

    # =========================================================
    # AÇÕES DO COMPROMISSO
    # =========================================================

    path(
        "<int:pk>/concluir/",
        views.agenda_complete,
        name="complete",
    ),
    path(
        "<int:pk>/nao-realizado/",
        views.agenda_not_completed,
        name="not_completed",
    ),
]