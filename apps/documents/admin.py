from django.contrib import admin

from .models import Document, RequiredDocument


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        "nome_original",
        "caso",
        "enviado_por",
        "criado_em",
    )

    search_fields = (
        "nome_original",
        "descricao",
        "caso__titulo",
        "caso__cliente__nome_completo",
    )

    list_filter = (
        "criado_em",
    )

@admin.register(RequiredDocument)
class RequiredDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "nome",
        "caso",
        "recebido",
        "criado_em",
        "recebido_em",
    )

    list_filter = (
        "recebido",
        "criado_em",
    )

    search_fields = (
        "nome",
        "caso__titulo",
        "caso__cliente__nome_completo",
    )