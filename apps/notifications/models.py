from django.conf import settings
from django.db import models
from django.utils import timezone


class Notification(models.Model):
    # =========================================================
    # TIPOS
    # =========================================================

    class Type(models.TextChoices):
        AGENDA = "agenda", "Agenda"
        DEADLINE = "deadline", "Prazo"
        DOCUMENT = "document", "Documento"
        CASE = "case", "Caso jurídico"
        SYSTEM = "system", "Sistema"

    # =========================================================
    # NÍVEIS
    # =========================================================

    class Level(models.TextChoices):
        INFO = "info", "Informação"
        ATTENTION = "attention", "Atenção"
        URGENT = "urgent", "Urgente"

    # =========================================================
    # DESTINATÁRIO
    # =========================================================

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notificacoes",
        verbose_name="Usuário",
    )

    # =========================================================
    # CONTEÚDO
    # =========================================================

    tipo = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.SYSTEM,
        db_index=True,
        verbose_name="Tipo",
    )

    nivel = models.CharField(
        max_length=20,
        choices=Level.choices,
        default=Level.INFO,
        db_index=True,
        verbose_name="Nível",
    )

    titulo = models.CharField(
        max_length=160,
        verbose_name="Título",
    )

    mensagem = models.TextField(
        blank=True,
        verbose_name="Mensagem",
    )

    url_destino = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="URL de destino",
    )

    # =========================================================
    # CONTROLE DE DUPLICIDADE
    # =========================================================

    chave = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True,
        verbose_name="Chave única",
        help_text=(
            "Identificador opcional utilizado para impedir "
            "notificações automáticas duplicadas."
        ),
    )

    # =========================================================
    # LEITURA
    # =========================================================

    lida = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="Lida",
    )

    lida_em = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Lida em",
    )

    # =========================================================
    # DATAS
    # =========================================================

    criada_em = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="Criada em",
    )

    # =========================================================
    # META
    # =========================================================

    class Meta:
        ordering = (
            "-criada_em",
            "-pk",
        )

        verbose_name = "Notificação"
        verbose_name_plural = "Notificações"

        indexes = [
            models.Index(
                fields=[
                    "usuario",
                    "lida",
                    "-criada_em",
                ],
                name="notif_user_read_date_idx",
            ),
        ]

    # =========================================================
    # REPRESENTAÇÃO
    # =========================================================

    def __str__(self):
        return self.titulo

    # =========================================================
    # AÇÕES
    # =========================================================

    def marcar_como_lida(self):
        """
        Marca a notificação como lida.

        Chamadas repetidas não alteram novamente a data de leitura.
        """
        if self.lida:
            return

        self.lida = True
        self.lida_em = timezone.now()

        self.save(
            update_fields=[
                "lida",
                "lida_em",
            ]
        )

    def marcar_como_nao_lida(self):
        """
        Retorna a notificação ao estado não lido.
        """
        if not self.lida and self.lida_em is None:
            return

        self.lida = False
        self.lida_em = None

        self.save(
            update_fields=[
                "lida",
                "lida_em",
            ]
        )