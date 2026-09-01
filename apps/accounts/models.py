from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    nome_completo = models.CharField(
        max_length=255,
        verbose_name="Nome completo",
    )

    cpf = models.CharField(
        max_length=14,
        unique=True,
        verbose_name="CPF",
    )

    rg = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="RG",
    )

    numero_oab = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Número da OAB",
    )

    uf_oab = models.CharField(
        max_length=2,
        blank=True,
        verbose_name="UF da OAB",
    )

    telefone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Telefone",
    )

    email = models.EmailField(
        unique=True,
        verbose_name="E-mail",
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nome_completo or self.username