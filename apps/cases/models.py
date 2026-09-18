from django.db import models

from apps.clients.models import Client


class CaseStatus(models.Model):
    nome = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nome",
    )

    descricao = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Descrição",
    )

    ordem = models.PositiveIntegerField(
        default=0,
        verbose_name="Ordem",
    )

    ativo = models.BooleanField(
        default=True,
        verbose_name="Ativo",
    )

    criado_em = models.DateTimeField(
        auto_now_add=True,
    )

    atualizado_em = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["ordem", "nome"]
        verbose_name = "Status da causa"
        verbose_name_plural = "Status das causas"

    def __str__(self):
        return self.nome


class LegalCase(models.Model):
    cliente = models.ForeignKey(
        Client,
        on_delete=models.PROTECT,
        related_name="casos",
        verbose_name="Cliente",
    )

    status = models.ForeignKey(
        CaseStatus,
        on_delete=models.PROTECT,
        related_name="casos",
        verbose_name="Status",
    )

    titulo = models.CharField(
        max_length=255,
        verbose_name="Título",
    )

    area_juridica = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Área jurídica",
    )

    descricao = models.TextField(
        verbose_name="Descrição da causa",
    )

    numero_processo = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Número do processo",
    )

    vara = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Vara",
    )

    comarca = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Comarca",
    )

    data_abertura = models.DateField(
        auto_now_add=True,
        verbose_name="Data de abertura",
    )

    data_encerramento = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data de encerramento",
    )

    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações",
    )

    criado_em = models.DateTimeField(
        auto_now_add=True,
    )

    atualizado_em = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "Caso jurídico"
        verbose_name_plural = "Casos jurídicos"

    def __str__(self):
        return (
            f"{self.titulo} - "
            f"{self.cliente.nome_completo}"
        )

    def save(self, *args, **kwargs):
        self.titulo = self._normalizar_texto(
            self.titulo,
        )

        self.area_juridica = self._normalizar_texto(
            self.area_juridica,
        )

        self.numero_processo = (
            self.numero_processo.strip()
            if self.numero_processo
            else ""
        )

        self.vara = self._normalizar_texto(
            self.vara,
        )

        self.comarca = self._normalizar_texto(
            self.comarca,
        )

        self.descricao = (
            self.descricao.strip()
            if self.descricao
            else ""
        )

        self.observacoes = (
            self.observacoes.strip()
            if self.observacoes
            else ""
        )

        super().save(*args, **kwargs)

    @staticmethod
    def _normalizar_texto(valor):
        if not valor:
            return ""

        return " ".join(
            valor.strip().split()
        )

    @property
    def possui_processo(self):
        return bool(
            self.numero_processo.strip()
            if self.numero_processo
            else False
        )

    @property
    def numero_identificacao(self):
        return f"#{self.pk:05d}" if self.pk else ""

    @property
    def encerrado(self):
        return self.data_encerramento is not None


class CaseHistory(models.Model):
    caso = models.ForeignKey(
        LegalCase,
        on_delete=models.CASCADE,
        related_name="historico",
        verbose_name="Caso",
    )

    usuario = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Usuário",
    )

    titulo = models.CharField(
        max_length=150,
        verbose_name="Título",
    )

    descricao = models.TextField(
        blank=True,
        verbose_name="Descrição",
    )

    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em",
    )

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "Histórico da causa"
        verbose_name_plural = "Históricos das causas"

    def __str__(self):
        return (
            f"{self.caso.titulo} - "
            f"{self.titulo}"
        )

    def save(self, *args, **kwargs):
        self.titulo = " ".join(
            self.titulo.strip().split()
        )

        self.descricao = (
            self.descricao.strip()
            if self.descricao
            else ""
        )

        super().save(*args, **kwargs)


class CaseMovement(models.Model):
    caso = models.ForeignKey(
        LegalCase,
        on_delete=models.CASCADE,
        related_name="movimentacoes",
        verbose_name="Caso",
    )

    usuario = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Usuário",
    )

    titulo = models.CharField(
        max_length=150,
        verbose_name="Título",
    )

    descricao = models.TextField(
        verbose_name="Descrição",
    )

    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em",
    )

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "Movimentação"
        verbose_name_plural = "Movimentações"

    def __str__(self):
        return (
            f"{self.caso.titulo} - "
            f"{self.titulo}"
        )

    def save(self, *args, **kwargs):
        self.titulo = " ".join(
            self.titulo.strip().split()
        )

        self.descricao = (
            self.descricao.strip()
            if self.descricao
            else ""
        )

        super().save(*args, **kwargs)