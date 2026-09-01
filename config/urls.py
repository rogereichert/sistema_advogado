from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    # Autenticação
    path(
        "",
        include("apps.accounts.urls"),
    ),

    # Administração Django
    path(
        "admin/",
        admin.site.urls,
    ),

    # Dashboard
    path(
        "",
        include("apps.core.urls"),
    ),

    # Clientes
    path(
        "clientes/",
        include("apps.clients.urls"),
    ),

    # Casos jurídicos
    path(
        "casos/",
        include("apps.cases.urls"),
    ),

    # Documentos
    path(
        "documentos/",
        include("apps.documents.urls"),
    ),

    # Agenda
    path(
        "agenda/",
        include("apps.agenda.urls"),
    ),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )