from django.conf import settings
from django.db import models

from apps.cases.models import LegalCase


class GoogleCalendarConnection(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="google_calendar_connection",
        verbose_name="Usuário",
    )

    google_email = models.EmailField(
        blank=True,
        verbose_name="Conta Google",
    )

    calendar_id = models.CharField(
        max_length=255,
        default="primary",
        verbose_name="Calendário",
    )

    refresh_token = models.TextField(
        verbose_name="Refresh token",
    )

    scopes = models.TextField(
        blank=True,
        verbose_name="Escopos autorizados",
    )

    conectado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Conectado em",
    )

    ultima_sincronizacao_em = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Última sincronização",
    )

    atualizado_em = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizado em",
    )

    class Meta:
        verbose_name = "Conexão com Google Calendar"
        verbose_name_plural = "Conexões com Google Calendar"

    def __str__(self):
        if self.google_email:
            return (
                f"{self.usuario} - "
                f"{self.google_email}"
            )

        return (
            f"{self.usuario} - "
            "Google Calendar"
        )


class AgendaEvent(models.Model):
    EVENT_TYPE_CHOICES = [
        ("audiencia", "Audiência"),
        ("prazo", "Prazo"),
        ("reuniao", "Reunião"),
        ("pericia", "Perícia"),
        ("diligencia", "Diligência"),
        ("outro", "Outro"),
    ]

    # =========================================================
    # STATUS OPERACIONAL DO COMPROMISSO
    # =========================================================

    class Status(models.TextChoices):
        SCHEDULED = (
            "scheduled",
            "Agendado",
        )

        CONFIRMED = (
            "confirmed",
            "Confirmado",
        )

        COMPLETED = (
            "completed",
            "Concluído",
        )

        NOT_COMPLETED = (
            "not_completed",
            "Não realizado",
        )

        CANCELED = (
            "canceled",
            "Cancelado",
        )

        RESCHEDULED = (
            "rescheduled",
            "Reagendado",
        )

    # =========================================================
    # STATUS DA SINCRONIZAÇÃO COM GOOGLE
    # =========================================================

    class GoogleSyncStatus(models.TextChoices):
        NOT_SYNCED = (
            "not_synced",
            "Não sincronizado",
        )

        SYNCED = (
            "synced",
            "Sincronizado",
        )

        REMOVED = (
            "removed",
            "Removido do Google",
        )

        ERROR = (
            "error",
            "Erro de sincronização",
        )

    # =========================================================
    # DADOS DO COMPROMISSO
    # =========================================================

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

    # =========================================================
    # SITUAÇÃO OPERACIONAL
    # =========================================================

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
        db_index=True,
        verbose_name="Status",
    )

    resultado = models.TextField(
        blank=True,
        verbose_name="Resultado",
        help_text=(
            "Resultado, providência ou observação referente "
            "à realização do compromisso."
        ),
    )

    concluido_em = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Concluído em",
    )

    concluido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="eventos_concluidos",
        verbose_name="Concluído por",
    )

    # =========================================================
    # GOOGLE CALENDAR
    # =========================================================

    google_event_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="ID do evento no Google",
    )

    google_calendar_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="ID do calendário no Google",
    )

    google_event_link = models.URLField(
        max_length=500,
        blank=True,
        verbose_name="Link do evento no Google",
    )

    google_synced_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Sincronizado com Google em",
    )

    google_sync_status = models.CharField(
        max_length=20,
        choices=GoogleSyncStatus.choices,
        default=GoogleSyncStatus.NOT_SYNCED,
        db_index=True,
        verbose_name="Status da sincronização Google",
    )

    # =========================================================
    # CONTROLE
    # =========================================================

    criado_em = models.DateTimeField(
        auto_now_add=True,
    )

    atualizado_em = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "data",
            "hora",
        ]

        verbose_name = "Evento da agenda"
        verbose_name_plural = "Eventos da agenda"

    def __str__(self):
        return (
            f"{self.get_tipo_display()} - "
            f"{self.titulo}"
        )

    # =========================================================
    # PROPRIEDADES OPERACIONAIS
    # =========================================================

    @property
    def agendado(self):
        return self.status == self.Status.SCHEDULED

    @property
    def confirmado(self):
        return self.status == self.Status.CONFIRMED

    @property
    def concluido(self):
        return self.status == self.Status.COMPLETED

    @property
    def nao_realizado(self):
        return self.status == self.Status.NOT_COMPLETED

    @property
    def cancelado(self):
        return self.status == self.Status.CANCELED

    @property
    def reagendado(self):
        return self.status == self.Status.RESCHEDULED

    # =========================================================
    # PROPRIEDADES GOOGLE
    # =========================================================

    @property
    def sincronizado_com_google(self):
        return (
            self.google_sync_status
            == self.GoogleSyncStatus.SYNCED
            and bool(
                self.google_event_id
                and self.google_calendar_id
            )
        )

    @property
    def removido_do_google(self):
        return (
            self.google_sync_status
            == self.GoogleSyncStatus.REMOVED
        )

    @property
    def erro_sincronizacao_google(self):
        return (
            self.google_sync_status
            == self.GoogleSyncStatus.ERROR
        )