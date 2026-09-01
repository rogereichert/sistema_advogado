from django.db import models


class Client(models.Model):
    ESTADO_CIVIL_CHOICES = [
        ("solteiro", "Solteiro(a)"),
        ("casado", "Casado(a)"),
        ("divorciado", "Divorciado(a)"),
        ("viuvo", "Viúvo(a)"),
        ("uniao_estavel", "União estável"),
        ("outro", "Outro"),
    ]

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

    carteira_trabalho = models.CharField(
        max_length=30,
        blank=True,
        verbose_name="Carteira de trabalho",
    )

    titulo_eleitor = models.CharField(
        max_length=30,
        blank=True,
        verbose_name="Título de eleitor",
    )

    estado_civil = models.CharField(
        max_length=20,
        choices=ESTADO_CIVIL_CHOICES,
        blank=True,
        verbose_name="Estado civil",
    )

    data_nascimento = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data de nascimento",
    )

    cep = models.CharField(
        max_length=9,
        blank=True,
        verbose_name="CEP",
    )

    logradouro = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Logradouro",
    )

    numero = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Número",
    )

    complemento = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Complemento",
    )

    bairro = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Bairro",
    )

    cidade = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Cidade",
    )

    uf = models.CharField(
        max_length=2,
        blank=True,
        verbose_name="UF",
    )

    telefone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Telefone",
    )

    email = models.EmailField(
        blank=True,
        verbose_name="E-mail",
    )

    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações",
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nome_completo"]
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self):
        return self.nome_completo