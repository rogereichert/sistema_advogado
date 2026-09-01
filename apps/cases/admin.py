from django.contrib import admin

from .models import (
    CaseHistory,
    CaseMovement,
    CaseStatus,
    LegalCase,
)


@admin.register(CaseStatus)
class CaseStatusAdmin(admin.ModelAdmin):
    list_display = (
        "nome",
        "ordem",
        "ativo",
    )

    list_editable = (
        "ordem",
        "ativo",
    )

    search_fields = (
        "nome",
    )


@admin.register(LegalCase)
class LegalCaseAdmin(admin.ModelAdmin):
    list_display = (
        "titulo",
        "cliente",
        "status",
        "area_juridica",
        "numero_processo",
        "data_abertura",
    )

    search_fields = (
        "titulo",
        "cliente__nome_completo",
        "cliente__cpf",
        "numero_processo",
    )

    list_filter = (
        "status",
        "area_juridica",
        "data_abertura",
    )

@admin.register(CaseHistory)
class CaseHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "caso",
        "titulo",
        "usuario",
        "criado_em",
    )

    search_fields = (
        "caso__titulo",
        "titulo",
        "descricao",
    )

    list_filter = (
        "criado_em",
    )

@admin.register(CaseMovement)
class CaseMovementAdmin(admin.ModelAdmin):
    list_display = (
        "titulo",
        "caso",
        "usuario",
        "criado_em",
    )

    search_fields = (
        "titulo",
        "descricao",
        "caso__titulo",
        "caso__cliente__nome_completo",
    )

    list_filter = (
        "criado_em",
    )