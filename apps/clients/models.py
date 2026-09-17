import re

from django.db import models


class Client(models.Model):
    ESTADO_CIVIL_SOLTEIRO = "solteiro"
    ESTADO_CIVIL_CASADO = "casado"
    ESTADO_CIVIL_DIVORCIADO = "divorciado"
    ESTADO_CIVIL_VIUVO = "viuvo"
    ESTADO_CIVIL_UNIAO_ESTAVEL = "uniao_estavel"
    ESTADO_CIVIL_OUTRO = "outro"

    ESTADO_CIVIL_CHOICES = [
        (ESTADO_CIVIL_SOLTEIRO, "Solteiro(a)"),
        (ESTADO_CIVIL_CASADO, "Casado(a)"),
        (ESTADO_CIVIL_DIVORCIADO, "Divorciado(a)"),
        (ESTADO_CIVIL_VIUVO, "Viúvo(a)"),
        (ESTADO_CIVIL_UNIAO_ESTAVEL, "União estável"),
        (ESTADO_CIVIL_OUTRO, "Outro"),
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

    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em",
    )

    atualizado_em = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizado em",
    )

    class Meta:
        ordering = ["nome_completo"]
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self):
        return self.nome_completo

    @staticmethod
    def _somente_digitos(valor):
        """
        Remove qualquer caractere que não seja numérico.

        Retorna string vazia quando o valor não estiver preenchido.
        """
        if not valor:
            return ""

        return re.sub(r"\D", "", str(valor))

    @staticmethod
    def _normalizar_texto(valor):
        """
        Remove espaços no início e no final de campos textuais.
        """
        if not valor:
            return ""

        return str(valor).strip()

    def save(self, *args, **kwargs):
        """
        Normaliza os dados antes de persistir o cliente.

        A validação das regras de negócio continua sendo responsabilidade
        principal do formulário/model validation. Aqui garantimos apenas
        uma representação consistente dos dados armazenados.
        """
        self.nome_completo = self._normalizar_texto(
            self.nome_completo
        )

        self.cpf = self._somente_digitos(
            self.cpf
        )

        self.cep = self._somente_digitos(
            self.cep
        )

        self.telefone = self._somente_digitos(
            self.telefone
        )

        self.rg = self._normalizar_texto(
            self.rg
        )

        self.carteira_trabalho = self._normalizar_texto(
            self.carteira_trabalho
        )

        self.titulo_eleitor = self._normalizar_texto(
            self.titulo_eleitor
        )

        self.logradouro = self._normalizar_texto(
            self.logradouro
        )

        self.numero = self._normalizar_texto(
            self.numero
        )

        self.complemento = self._normalizar_texto(
            self.complemento
        )

        self.bairro = self._normalizar_texto(
            self.bairro
        )

        self.cidade = self._normalizar_texto(
            self.cidade
        )

        self.uf = self._normalizar_texto(
            self.uf
        ).upper()

        self.email = self._normalizar_texto(
            self.email
        ).lower()

        self.observacoes = (
            self.observacoes.strip()
            if self.observacoes
            else ""
        )

        super().save(*args, **kwargs)

    @property
    def cpf_formatado(self):
        """
        Retorna o CPF no formato 000.000.000-00.
        """
        cpf = self._somente_digitos(
            self.cpf
        )

        if len(cpf) != 11:
            return self.cpf or ""

        return (
            f"{cpf[:3]}."
            f"{cpf[3:6]}."
            f"{cpf[6:9]}-"
            f"{cpf[9:]}"
        )

    @property
    def cep_formatado(self):
        """
        Retorna o CEP no formato 00000-000.
        """
        cep = self._somente_digitos(
            self.cep
        )

        if len(cep) != 8:
            return self.cep or ""

        return f"{cep[:5]}-{cep[5:]}"

    @property
    def telefone_formatado(self):
        """
        Formata telefones brasileiros de 10 ou 11 dígitos.
        """
        telefone = self._somente_digitos(
            self.telefone
        )

        if len(telefone) == 11:
            return (
                f"({telefone[:2]}) "
                f"{telefone[2:7]}-"
                f"{telefone[7:]}"
            )

        if len(telefone) == 10:
            return (
                f"({telefone[:2]}) "
                f"{telefone[2:6]}-"
                f"{telefone[6:]}"
            )

        return self.telefone or ""

    @property
    def endereco_completo(self):
        """
        Monta uma representação textual do endereço do cliente.
        """
        partes = []

        if self.logradouro:
            endereco = self.logradouro

            if self.numero:
                endereco += f", {self.numero}"

            partes.append(endereco)

        if self.complemento:
            partes.append(self.complemento)

        if self.bairro:
            partes.append(self.bairro)

        cidade_uf = ""

        if self.cidade:
            cidade_uf = self.cidade

        if self.uf:
            cidade_uf += (
                f"/{self.uf}"
                if cidade_uf
                else self.uf
            )

        if cidade_uf:
            partes.append(cidade_uf)

        if self.cep:
            partes.append(
                f"CEP {self.cep_formatado}"
            )

        return " - ".join(partes)