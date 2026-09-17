from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.agenda.models import AgendaEvent

from .forms import ClientForm
from .models import Client


CLOSED_CASE_STATUSES = (
    "Concluído",
    "Arquivado",
    "Cancelado",
)


def _is_ajax(request):
    """
    Identifica requisições realizadas pela interface via AJAX.
    """
    return (
        request.headers.get("x-requested-with")
        == "XMLHttpRequest"
    )


def _render_client_form(
    request,
    form,
    *,
    client=None,
    status=200,
):
    """
    Renderiza o formulário de cliente.

    Requisições normais recebem a página completa.
    Requisições AJAX recebem somente o conteúdo necessário
    para o modal.
    """
    context = {
        "form": form,
        "client": client,
    }

    if _is_ajax(request):
        return render(
            request,
            "clients/_client_form.html",
            context,
            status=status,
        )

    return render(
        request,
        "clients/client_form.html",
        context,
        status=status,
    )


@login_required
def client_list(request):
    clients = Client.objects.all()

    return render(
        request,
        "clients/client_list.html",
        {
            "clients": clients,
        },
    )


@login_required
def client_create(request):
    if request.method == "POST":
        form = ClientForm(request.POST)

        if form.is_valid():
            client = form.save()

            if _is_ajax(request):
                return JsonResponse(
                    {
                        "success": True,
                        "client_id": client.pk,
                        "message": (
                            "Cliente cadastrado com sucesso."
                        ),
                    }
                )

            return redirect(
                "clients:detail",
                pk=client.pk,
            )

        return _render_client_form(
            request,
            form,
            status=400,
        )

    form = ClientForm()

    return _render_client_form(
        request,
        form,
    )


@login_required
def client_update(request, pk):
    client = get_object_or_404(
        Client,
        pk=pk,
    )

    if request.method == "POST":
        form = ClientForm(
            request.POST,
            instance=client,
        )

        if form.is_valid():
            client = form.save()

            if _is_ajax(request):
                return JsonResponse(
                    {
                        "success": True,
                        "client_id": client.pk,
                        "message": (
                            "Cliente atualizado com sucesso."
                        ),
                    }
                )

            return redirect(
                "clients:detail",
                pk=client.pk,
            )

        return _render_client_form(
            request,
            form,
            client=client,
            status=400,
        )

    form = ClientForm(
        instance=client,
    )

    return _render_client_form(
        request,
        form,
        client=client,
    )


@login_required
def client_detail(request, pk):
    client = get_object_or_404(
        Client,
        pk=pk,
    )

    cases = (
        client.casos
        .select_related("status")
        .all()
    )

    active_cases_count = (
        cases
        .exclude(
            status__nome__in=CLOSED_CASE_STATUSES,
        )
        .count()
    )

    today = timezone.localdate()

    next_event = (
        AgendaEvent.objects
        .select_related("caso")
        .filter(
            caso__cliente=client,
            data__gte=today,
        )
        .order_by(
            "data",
            "hora",
        )
        .first()
    )

    return render(
        request,
        "clients/client_detail.html",
        {
            "client": client,
            "cases": cases,
            "active_cases_count": (
                active_cases_count
            ),
            "next_event": next_event,
        },
    )