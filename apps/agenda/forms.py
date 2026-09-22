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
                format="%Y-%m-%d",
                attrs={"type": "date"},
            ),

            "hora": forms.TimeInput(
                format="%H:%M",
                attrs={"type": "time"},
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["data"].input_formats = [
            "%Y-%m-%d",
            "%d/%m/%Y",
        ]

        self.fields["hora"].input_formats = [
            "%H:%M",
            "%H:%M:%S",
        ]

        for field in self.fields.values():
            field.widget.attrs["class"] = INPUT_CLASSES


class AgendaRescheduleForm(forms.Form):
    nova_data = forms.DateField(
        label="Nova data",
        input_formats=[
            "%Y-%m-%d",
            "%d/%m/%Y",
        ],
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={
                "type": "date",
                "class": INPUT_CLASSES,
            },
        ),
    )

    novo_horario = forms.TimeField(
        label="Novo horário",
        required=False,
        input_formats=[
            "%H:%M",
            "%H:%M:%S",
        ],
        widget=forms.TimeInput(
            format="%H:%M",
            attrs={
                "type": "time",
                "class": INPUT_CLASSES,
            },
        ),
    )

    motivo = forms.CharField(
        label="Motivo do reagendamento",
        required=True,
        strip=True,
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "class": INPUT_CLASSES,
                "placeholder": (
                    "Ex.: Reagendado a pedido do cliente."
                ),
            },
        ),
    )

    def clean_motivo(self):
        motivo = self.cleaned_data["motivo"].strip()

        if not motivo:
            raise forms.ValidationError(
                "Informe o motivo do reagendamento."
            )

        return motivo

    def clean(self):
        cleaned_data = super().clean()

        nova_data = cleaned_data.get("nova_data")
        novo_horario = cleaned_data.get("novo_horario")

        if nova_data is None:
            return cleaned_data

        event = getattr(self, "event", None)

        if event is None:
            return cleaned_data

        if (
            nova_data == event.data
            and novo_horario == event.hora
        ):
            raise forms.ValidationError(
                "Informe uma nova data ou um novo horário "
                "para reagendar o compromisso."
            )

        return cleaned_data

    def __init__(self, *args, event=None, **kwargs):
        self.event = event

        super().__init__(*args, **kwargs)

        if event is not None and not self.is_bound:
            self.initial["nova_data"] = event.data
            self.initial["novo_horario"] = event.hora