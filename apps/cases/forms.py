from django import forms

from .models import LegalCase, CaseMovement


INPUT_CLASSES = (
    "w-full rounded-xl border border-slate-200 "
    "bg-white px-4 py-3 text-sm text-slate-900 "
    "shadow-sm outline-none transition "
    "placeholder:text-slate-400 "
    "focus:border-slate-400 "
    "focus:ring-4 focus:ring-slate-100"
)


class LegalCaseForm(forms.ModelForm):
    class Meta:
        model = LegalCase

        fields = [
            "titulo",
            "area_juridica",
            "status",
            "descricao",
            "numero_processo",
            "vara",
            "comarca",
            "observacoes",
        ]

        widgets = {
            "descricao": forms.Textarea(
                attrs={"rows": 5}
            ),
            "observacoes": forms.Textarea(
                attrs={"rows": 4}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs["class"] = INPUT_CLASSES

class CaseMovementForm(forms.ModelForm):
    class Meta:
        model = CaseMovement

        fields = [
            "titulo",
            "descricao",
        ]

        widgets = {
            "descricao": forms.Textarea(
                attrs={"rows": 5}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs["class"] = INPUT_CLASSES