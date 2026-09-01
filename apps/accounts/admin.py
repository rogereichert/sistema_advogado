from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (
            "Dados profissionais",
            {
                "fields": (
                    "nome_completo",
                    "cpf",
                    "rg",
                    "numero_oab",
                    "uf_oab",
                    "telefone",
                )
            },
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Dados profissionais",
            {
                "fields": (
                    "nome_completo",
                    "cpf",
                    "rg",
                    "numero_oab",
                    "uf_oab",
                    "telefone",
                    "email",
                )
            },
        ),
    )