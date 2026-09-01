from django import forms
from django.contrib.auth.forms import AuthenticationForm


INPUT_CLASSES = (
    "block w-full rounded-xl border border-slate-200 "
    "bg-white px-4 py-3.5 text-sm text-slate-900 "
    "shadow-sm outline-none transition "
    "placeholder:text-slate-400 "
    "focus:border-amber-500 "
    "focus:ring-4 focus:ring-amber-500/10"
)


class LoginForm(AuthenticationForm):

    username = forms.CharField(
        label="Usuário",
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASSES,
                "placeholder": "Digite seu usuário",
                "autocomplete": "username",
                "autofocus": True,
            }
        ),
    )

    password = forms.CharField(
        label="Senha",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": INPUT_CLASSES,
                "placeholder": "Digite sua senha",
                "autocomplete": "current-password",
            }
        ),
    )