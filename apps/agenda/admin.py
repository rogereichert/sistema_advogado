from django.contrib import admin

from .models import AgendaEvent


@admin.register(AgendaEvent)
class AgendaEventAdmin(admin.ModelAdmin):
    list_display = (
        "titulo",
        "tipo",
        "caso",
        "data",
        "hora",
        "local",
    )

    search_fields = (
        "titulo",
        "descricao",
        "local",
        "caso__titulo",
        "caso__cliente__nome_completo",
    )

    list_filter = (
        "tipo",
        "data",
    )