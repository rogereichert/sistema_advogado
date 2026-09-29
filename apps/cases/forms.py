
from django import forms

from .models import CaseMovement, LegalCase


INPUT_CLASSES = "app-input"


class LegalCaseForm(forms.ModelForm):
    class Meta:
        model = LegalCase

        fields = [
            "titulo",
            "area_juridica",
            "status",
            "descricao",
            "numero_processo",
            "tribunal",
            "grau",
            "classe_processual",
            "sistema_processual",
            "orgao_julgador_nome",
            "data_ajuizamento",
            "vara",
            "comarca",
            "observacoes",
        ]

        widgets = {
            "titulo": forms.TextInput(
                attrs={
                    "placeholder": (
                        "Ex.: Reclamação trabalhista - horas extras"
                    ),
                }
            ),
            "area_juridica": forms.TextInput(
                attrs={
                    "placeholder": "Ex.: Trabalhista",
                }
            ),
            "descricao": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": (
                        "Descreva os fatos, o objeto da demanda "
                        "e as principais informações do caso..."
                    ),
                }
            ),
            "numero_processo": forms.TextInput(
                attrs={
                    "id": "id_numero_processo",
                    "placeholder": (
                        "Ex.: 0000000-00.0000.0.00.0000"
                    ),
                    "autocomplete": "off",
                    "inputmode": "numeric",
                }
            ),
            "tribunal": forms.TextInput(
                attrs={
                    "placeholder": "Ex.: TRF1, TJPE, TRT6",
                }
            ),
            "grau": forms.TextInput(
                attrs={
                    "placeholder": "Ex.: G1, G2, JE",
                }
            ),
            "classe_processual": forms.TextInput(
                attrs={
                    "placeholder": (
                        "Ex.: Procedimento do Juizado Especial Cível"
                    ),
                }
            ),
            "sistema_processual": forms.TextInput(
                attrs={
                    "placeholder": "Ex.: PJe",
                }
            ),
            "orgao_julgador_nome": forms.TextInput(
                attrs={
                    "placeholder": "Ex.: 1ª Vara Cível",
                }
            ),
            "data_ajuizamento": forms.DateInput(
                format="%Y-%m-%d",
                attrs={
                    "type": "date",
                },
            ),
            "vara": forms.TextInput(
                attrs={
                    "placeholder": "Ex.: 1ª Vara do Trabalho",
                }
            ),
            "comarca": forms.TextInput(
                attrs={
                    "placeholder": "Ex.: Recife/PE",
                }
            ),
            "observacoes": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": (
                        "Registre observações internas relevantes "
                        "ao acompanhamento do caso..."
                    ),
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Todos os campos processuais são opcionais.
        optional_process_fields = [
            "numero_processo",
            "tribunal",
            "grau",
            "classe_processual",
            "sistema_processual",
            "orgao_julgador_nome",
            "data_ajuizamento",
            "vara",
            "comarca",
        ]

        for field_name in optional_process_fields:
            self.fields[field_name].required = False

        # O campo do model é DateTimeField, mas a interface
        # precisa receber somente a data.
        self.fields["data_ajuizamento"].input_formats = [
            "%Y-%m-%d",
        ]

        for field in self.fields.values():
            existing_classes = field.widget.attrs.get(
                "class",
                "",
            )

            field.widget.attrs["class"] = (
                f"{existing_classes} {INPUT_CLASSES}"
            ).strip()

        self.fields["titulo"].widget.attrs[
            "autofocus"
        ] = True

        self.fields["status"].empty_label = (
            "Selecione o status"
        )

    def clean_titulo(self):
        titulo = self.cleaned_data["titulo"]

        return " ".join(
            titulo.strip().split()
        )

    def clean_area_juridica(self):
        area = self.cleaned_data.get(
            "area_juridica",
            "",
        )

        if not area:
            return area

        return " ".join(
            area.strip().split()
        )

    def clean_numero_processo(self):
        numero = self.cleaned_data.get(
            "numero_processo",
            "",
        )

        if not numero:
            return numero

        return numero.strip()

    def clean_vara(self):
        vara = self.cleaned_data.get(
            "vara",
            "",
        )

        if not vara:
            return vara

        return " ".join(
            vara.strip().split()
        )

    def clean_comarca(self):
        comarca = self.cleaned_data.get(
            "comarca",
            "",
        )

        if not comarca:
            return comarca

        return " ".join(
            comarca.strip().split()
        )

    def clean_descricao(self):
        descricao = self.cleaned_data.get(
            "descricao",
            "",
        )

        if not descricao:
            return descricao

        return descricao.strip()

    def clean_observacoes(self):
        observacoes = self.cleaned_data.get(
            "observacoes",
            "",
        )

        if not observacoes:
            return observacoes

        return observacoes.strip()


class CaseMovementForm(forms.ModelForm):
    class Meta:
        model = CaseMovement

        fields = [
            "titulo",
            "descricao",
        ]

        widgets = {
            "titulo": forms.TextInput(
                attrs={
                    "placeholder": "Ex.: Audiência realizada",
                }
            ),
            "descricao": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": (
                        "Descreva a movimentação e as informações "
                        "relevantes para o histórico do caso..."
                    ),
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            existing_classes = field.widget.attrs.get(
                "class",
                "",
            )

            field.widget.attrs["class"] = (
                f"{existing_classes} {INPUT_CLASSES}"
            ).strip()

        self.fields["titulo"].widget.attrs[
            "autofocus"
        ] = True

    def clean_titulo(self):
        titulo = self.cleaned_data["titulo"]

        return " ".join(
            titulo.strip().split()
        )

    def clean_descricao(self):
        descricao = self.cleaned_data.get(
            "descricao",
            "",
        )

        if not descricao:
            return descricao

        return descricao.strip()
