from django.conf import settings
from django.db import models

from apps.cases.models import LegalCase


class AgendaEvent(models.Model):
    EVENT_TYPE_CHOICES = [
        ("audiencia", "Audiência"),
        ("prazo", "Prazo"),
        ("reuniao", "Reunião"),
        ("pericia", "Perícia"),
        ("diligencia", "Diligência"),
        ("outro", "Outro"),
    ]

    caso = models.ForeignKey(
        LegalCase,
        on_delete=models.CASCADE,
        related_name="eventos",
        verbose_name="Caso",
    )

    tipo = models.CharField(
        max_length=20,
        choices=EVENT_TYPE_CHOICES,
        verbose_name="Tipo",
    )

    titulo = models.CharField(
        max_length=150,
        verbose_name="Título",
    )

    descricao = models.TextField(
        blank=True,
        verbose_name="Descrição",
    )

    data = models.DateField(
        verbose_name="Data",
    )

    hora = models.TimeField(
        null=True,
        blank=True,
        verbose_name="Hora",
    )

    local = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Local",
    )

    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações",
    )

    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="eventos_criados",
        verbose_name="Criado por",
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = [
            "data",
            "hora",
        ]

        verbose_name = "Evento da agenda"
        verbose_name_plural = "Eventos da agenda"

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.titulo}"