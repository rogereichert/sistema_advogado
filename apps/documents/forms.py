from django import forms
from django.core.exceptions import ValidationError
from .models import RequiredDocument

ALLOWED_EXTENSIONS = {
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
}

MAX_FILE_SIZE = 25 * 1024 * 1024


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault(
            "widget",
            MultipleFileInput(
                attrs={
                    "class": (
                        "block w-full rounded-xl border border-slate-200 "
                        "bg-white px-4 py-3 text-sm text-slate-700 "
                        "shadow-sm file:mr-4 file:rounded-lg file:border-0 "
                        "file:bg-slate-950 file:px-4 file:py-2 "
                        "file:text-sm file:font-semibold file:text-white "
                        "hover:file:bg-slate-800"
                    ),
                    "multiple": True,
                }
            ),
        )

        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean

        if isinstance(data, (list, tuple)):
            result = [
                single_file_clean(file, initial)
                for file in data
            ]

            return result

        return single_file_clean(data, initial)


class DocumentUploadForm(forms.Form):
    arquivos = MultipleFileField(
        label="Arquivos",
    )

    descricao = forms.CharField(
        required=False,
        label="Descrição",
        widget=forms.TextInput(
            attrs={
                "class": (
                    "w-full rounded-xl border border-slate-200 "
                    "bg-white px-4 py-3 text-sm text-slate-900 "
                    "shadow-sm outline-none transition "
                    "focus:border-slate-400 "
                    "focus:ring-4 focus:ring-slate-100"
                ),
                "placeholder": (
                    "Ex.: Documentação inicial enviada pelo cliente"
                ),
            }
        ),
    )

    def clean_arquivos(self):
        arquivos = self.cleaned_data["arquivos"]

        if not isinstance(arquivos, (list, tuple)):
            arquivos = [arquivos]

        for arquivo in arquivos:
            extension = (
                arquivo.name
                .rsplit(".", 1)[-1]
                .lower()
                if "." in arquivo.name
                else ""
            )

            if extension not in ALLOWED_EXTENSIONS:
                raise ValidationError(
                    f"O arquivo '{arquivo.name}' possui "
                    "um formato não permitido."
                )

            if arquivo.size > MAX_FILE_SIZE:
                raise ValidationError(
                    f"O arquivo '{arquivo.name}' ultrapassa "
                    "o limite de 25 MB."
                )

        return arquivos

class RequiredDocumentForm(forms.ModelForm):
    class Meta:
        model = RequiredDocument

        fields = [
            "nome",
            "descricao",
        ]

        widgets = {
            "nome": forms.TextInput(
                attrs={
                    "class": (
                        "w-full rounded-xl border border-slate-200 "
                        "bg-white px-4 py-3 text-sm text-slate-900 "
                        "shadow-sm outline-none transition "
                        "focus:border-slate-400 "
                        "focus:ring-4 focus:ring-slate-100"
                    ),
                    "placeholder": "Ex.: Carteira de Trabalho",
                }
            ),

            "descricao": forms.TextInput(
                attrs={
                    "class": (
                        "w-full rounded-xl border border-slate-200 "
                        "bg-white px-4 py-3 text-sm text-slate-900 "
                        "shadow-sm outline-none transition "
                        "focus:border-slate-400 "
                        "focus:ring-4 focus:ring-slate-100"
                    ),
                    "placeholder": "Informação opcional",
                }
            ),
        }