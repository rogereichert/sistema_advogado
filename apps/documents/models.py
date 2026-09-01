import uuid
from pathlib import Path

from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models

from apps.cases.models import LegalCase


def document_upload_path(instance, filename):
    extension = Path(filename).suffix.lower()

    generated_name = f"{uuid.uuid4().hex}{extension}"

    client_id = str(instance.caso.cliente_id).zfill(6)
    case_id = str(instance.caso_id).zfill(6)

    return (
        f"clientes/{client_id}/"
        f"casos/{case_id}/"
        f"documentos/{generated_name}"
    )


class Document(models.Model):
    caso = models.ForeignKey(
        LegalCase,
        on_delete=models.CASCADE,
        related_name="documentos",
        verbose_name="Caso",
    )

    arquivo = models.FileField(
        upload_to=document_upload_path,
        validators=[
            FileExtensionValidator(
                allowed_extensions=[
                    "pdf",
                    "png",
                    "jpg",
                    "jpeg",
                    "webp",
                    "doc",
                    "docx",
                    "xls",
                    "xlsx",
                    "txt",
                    "zip",
                ]
            )
        ],
        verbose_name="Arquivo",
    )

    nome_original = models.CharField(
        max_length=255,
        verbose_name="Nome original",
    )

    descricao = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Descrição",
    )

    enviado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documentos_enviados",
        verbose_name="Enviado por",
    )

    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Enviado em",
    )

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "Documento"
        verbose_name_plural = "Documentos"

    def __str__(self):
        return self.nome_original

class RequiredDocument(models.Model):
    caso = models.ForeignKey(
        LegalCase,
        on_delete=models.CASCADE,
        related_name="documentos_necessarios",
        verbose_name="Caso",
    )

    nome = models.CharField(
        max_length=150,
        verbose_name="Documento",
    )

    descricao = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Descrição",
    )

    recebido = models.BooleanField(
        default=False,
        verbose_name="Recebido",
    )

    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em",
    )

    recebido_em = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Recebido em",
    )

    class Meta:
        ordering = ["recebido", "nome"]
        verbose_name = "Documento necessário"
        verbose_name_plural = "Documentos necessários"

    def __str__(self):
        return f"{self.nome} - {self.caso.titulo}"