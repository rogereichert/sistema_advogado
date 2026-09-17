import re
from datetime import date

from django import forms
from django.core.exceptions import ValidationError

from .models import Client


INPUT_CLASSES = "app-input"


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client

        fields = [
            "nome_completo",
            "cpf",
            "rg",
            "carteira_trabalho",
            "titulo_eleitor",
            "estado_civil",
            "data_nascimento",
            "cep",
            "logradouro",
            "numero",
            "complemento",
            "bairro",
            "cidade",
            "uf",
            "telefone",
            "email",
            "observacoes",
        ]

        widgets = {
            "nome_completo": forms.TextInput(
                attrs={
                    "autocomplete": "name",
                    "placeholder": "Nome completo do cliente",
                }
            ),

            "cpf": forms.TextInput(
                attrs={
                    "maxlength": "14",
                    "inputmode": "numeric",
                    "autocomplete": "off",
                    "placeholder": "000.000.000-00",
                }
            ),

            "rg": forms.TextInput(
                attrs={
                    "autocomplete": "off",
                    "placeholder": "RG",
                }
            ),

            "carteira_trabalho": forms.TextInput(
                attrs={
                    "autocomplete": "off",
                    "placeholder": "Carteira de trabalho",
                }
            ),

            "titulo_eleitor": forms.TextInput(
                attrs={
                    "autocomplete": "off",
                    "placeholder": "Título de eleitor",
                }
            ),

            "data_nascimento": forms.DateInput(
                attrs={
                    "type": "date",
                    "autocomplete": "bday",
                }
            ),

            "cep": forms.TextInput(
                attrs={
                    "maxlength": "9",
                    "inputmode": "numeric",
                    "autocomplete": "postal-code",
                    "placeholder": "00000-000",
                }
            ),

            "logradouro": forms.TextInput(
                attrs={
                    "autocomplete": "address-line1",
                    "placeholder": "Rua, avenida, travessa...",
                }
            ),

            "numero": forms.TextInput(
                attrs={
                    "autocomplete": "address-line2",
                    "placeholder": "Número",
                }
            ),

            "complemento": forms.TextInput(
                attrs={
                    "autocomplete": "address-line2",
                    "placeholder": "Apartamento, bloco, referência...",
                }
            ),

            "bairro": forms.TextInput(
                attrs={
                    "placeholder": "Bairro",
                }
            ),

            "cidade": forms.TextInput(
                attrs={
                    "autocomplete": "address-level2",
                    "placeholder": "Cidade",
                }
            ),

            "uf": forms.TextInput(
                attrs={
                    "maxlength": "2",
                    "autocomplete": "address-level1",
                    "placeholder": "UF",
                }
            ),

            "telefone": forms.TextInput(
                attrs={
                    "maxlength": "15",
                    "inputmode": "tel",
                    "autocomplete": "tel",
                    "placeholder": "(00) 00000-0000",
                }
            ),

            "email": forms.EmailInput(
                attrs={
                    "autocomplete": "email",
                    "placeholder": "email@exemplo.com",
                }
            ),

            "observacoes": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": (
                        "Informações adicionais relevantes "
                        "sobre o cliente..."
                    ),
                }
            ),
        }

        error_messages = {
            "nome_completo": {
                "required": "Informe o nome completo do cliente.",
                "max_length": "O nome informado é muito longo.",
            },
            "cpf": {
                "required": "Informe o CPF do cliente.",
                "unique": "Já existe um cliente cadastrado com este CPF.",
                "max_length": "O CPF informado é inválido.",
            },
            "email": {
                "invalid": "Informe um endereço de e-mail válido.",
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            existing_classes = field.widget.attrs.get("class", "")

            field.widget.attrs["class"] = (
                f"{existing_classes} {INPUT_CLASSES}"
            ).strip()

        # Texto inicial do campo Estado civil.
        self.fields["estado_civil"].choices = [
            ("", "Selecione o estado civil"),
            *[
                choice
                for choice in self.fields["estado_civil"].choices
                if choice[0] != ""
            ],
        ]

        # O foco inicial fica no nome do cliente.
        self.fields["nome_completo"].widget.attrs["autofocus"] = True

    @staticmethod
    def _somente_digitos(valor):
        """
        Retorna apenas os números presentes no valor informado.
        """
        if not valor:
            return ""

        return re.sub(r"\D", "", str(valor))

    @staticmethod
    def _cpf_valido(cpf):
        """
        Valida um CPF através dos dois dígitos verificadores.

        Espera receber uma string contendo exatamente 11 dígitos.
        """
        if len(cpf) != 11:
            return False

        # CPFs formados pelo mesmo dígito são inválidos.
        if cpf == cpf[0] * 11:
            return False

        # Primeiro dígito verificador.
        soma = sum(
            int(cpf[indice]) * (10 - indice)
            for indice in range(9)
        )

        resto = soma % 11

        primeiro_digito = (
            0 if resto < 2 else 11 - resto
        )

        if int(cpf[9]) != primeiro_digito:
            return False

        # Segundo dígito verificador.
        soma = sum(
            int(cpf[indice]) * (11 - indice)
            for indice in range(10)
        )

        resto = soma % 11

        segundo_digito = (
            0 if resto < 2 else 11 - resto
        )

        return int(cpf[10]) == segundo_digito

    def clean_nome_completo(self):
        """
        Normaliza o nome e impede valores vazios compostos apenas
        por espaços.
        """
        nome = self.cleaned_data.get("nome_completo", "").strip()

        if not nome:
            raise ValidationError(
                "Informe o nome completo do cliente."
            )

        return nome

    def clean_cpf(self):
        """
        Normaliza, valida matematicamente e verifica duplicidade do CPF.
        """
        cpf = self._somente_digitos(
            self.cleaned_data.get("cpf")
        )

        if len(cpf) != 11:
            raise ValidationError(
                "Informe um CPF válido com 11 dígitos."
            )

        if not self._cpf_valido(cpf):
            raise ValidationError(
                "Informe um CPF válido."
            )

        clientes_com_mesmo_cpf = Client.objects.filter(
            cpf=cpf
        )

        # Durante a edição, o próprio registro não deve ser
        # considerado uma duplicidade.
        if self.instance and self.instance.pk:
            clientes_com_mesmo_cpf = (
                clientes_com_mesmo_cpf.exclude(
                    pk=self.instance.pk
                )
            )

        if clientes_com_mesmo_cpf.exists():
            raise ValidationError(
                "Já existe um cliente cadastrado com este CPF."
            )

        return cpf

    def clean_data_nascimento(self):
        """
        Impede o cadastro de uma data de nascimento futura.
        """
        data_nascimento = self.cleaned_data.get(
            "data_nascimento"
        )

        if (
            data_nascimento
            and data_nascimento > date.today()
        ):
            raise ValidationError(
                "A data de nascimento não pode estar no futuro."
            )

        return data_nascimento

    def clean_cep(self):
        """
        Normaliza e valida o tamanho do CEP quando informado.
        """
        cep = self._somente_digitos(
            self.cleaned_data.get("cep")
        )

        if cep and len(cep) != 8:
            raise ValidationError(
                "Informe um CEP válido com 8 dígitos."
            )

        return cep

    def clean_telefone(self):
        """
        Normaliza telefone fixo ou celular brasileiro.

        Aceita 10 dígitos para telefone fixo e 11 para celular.
        """
        telefone = self._somente_digitos(
            self.cleaned_data.get("telefone")
        )

        if telefone and len(telefone) not in (10, 11):
            raise ValidationError(
                "Informe um telefone válido com DDD."
            )

        return telefone

    def clean_uf(self):
        """
        Normaliza a UF e exige exatamente duas letras quando informada.
        """
        uf = (
            self.cleaned_data.get("uf", "")
            .strip()
            .upper()
        )

        if not uf:
            return ""

        if len(uf) != 2 or not uf.isalpha():
            raise ValidationError(
                "Informe uma UF válida com 2 letras."
            )

        return uf

    def clean_email(self):
        """
        Normaliza o endereço de e-mail.
        """
        email = (
            self.cleaned_data.get("email", "")
            .strip()
            .lower()
        )

        return email