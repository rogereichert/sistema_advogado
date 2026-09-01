from django.urls import path

from . import views


app_name = "documents"


urlpatterns = [
    # Central de documentos
    path(
        "",
        views.document_list,
        name="list",
    ),

    # Documentos anexados aos casos
    path(
        "caso/<int:case_pk>/enviar/",
        views.document_upload,
        name="upload",
    ),
    path(
        "<int:pk>/download/",
        views.document_download,
        name="download",
    ),
    path(
        "<int:pk>/excluir/",
        views.document_delete,
        name="delete",
    ),

    # Documentação necessária
    path(
        "caso/<int:case_pk>/necessarios/novo/",
        views.required_document_create,
        name="required_create",
    ),
    path(
        "necessarios/<int:pk>/alternar/",
        views.required_document_toggle,
        name="required_toggle",
    ),
    path(
        "necessarios/<int:pk>/excluir/",
        views.required_document_delete,
        name="required_delete",
    ),
]