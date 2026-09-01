from django.contrib import admin

from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = (
        "nome_completo",
        "cpf",
        "telefone",
        "email",
        "cidade",
        "uf",
    )

    search_fields = (
        "nome_completo",
        "cpf",
        "rg",
        "telefone",
        "email",
    )

    list_filter = (
        "estado_civil",
        "uf",
    )