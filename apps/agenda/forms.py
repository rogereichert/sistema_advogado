from django import forms

from .models import AgendaEvent


INPUT_CLASSES = (
    "w-full rounded-xl border border-slate-200 "
    "bg-white px-4 py-3 text-sm text-slate-900 "
    "shadow-sm outline-none transition "
    "focus:border-slate-400 "
    "focus:ring-4 focus:ring-slate-100"
)


class AgendaEventForm(forms.ModelForm):
    class Meta:
        model = AgendaEvent

        fields = [
            "tipo",
            "titulo",
            "descricao",
            "data",
            "hora",
            "local",
            "observacoes",
        ]

        widgets = {
            "descricao": forms.Textarea(
                attrs={"rows": 4}
            ),

            "observacoes": forms.Textarea(
                attrs={"rows": 4}
            ),

            "data": forms.DateInput(
                attrs={"type": "date"}
            ),

            "hora": forms.TimeInput(
                attrs={"type": "time"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs["class"] = INPUT_CLASSES