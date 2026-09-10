from django import forms

from .models import Client


INPUT_CLASSES = (
    "w-full rounded-xl border border-slate-200 "
    "bg-white px-4 py-3 text-sm text-slate-900 "
    "shadow-sm outline-none transition "
    "placeholder:text-slate-400 "
    "focus:border-slate-400 "
    "focus:ring-4 focus:ring-slate-100"
)


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
            "cpf": forms.TextInput(
                attrs={
                    "maxlength": "14",
                    "inputmode": "numeric",
                    "autocomplete": "off",
                }
            ),

            "cep": forms.TextInput(
                attrs={
                    "maxlength": "9",
                    "inputmode": "numeric",
                    "autocomplete": "postal-code",
                }
            ),

            "data_nascimento": forms.DateInput(
                attrs={"type": "date"}
            ),

            "observacoes": forms.Textarea(
                attrs={"rows": 4}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs["class"] = INPUT_CLASSES