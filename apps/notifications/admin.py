from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "titulo",
        "usuario",
        "tipo",
        "nivel",
        "lida",
        "criada_em",
    )

    list_filter = (
        "tipo",
        "nivel",
        "lida",
        "criada_em",
    )

    search_fields = (
        "titulo",
        "mensagem",
        "usuario__username",
        "usuario__first_name",
        "usuario__last_name",
        "usuario__email",
    )

    readonly_fields = (
        "criada_em",
        "lida_em",
    )

    ordering = (
        "-criada_em",
    )