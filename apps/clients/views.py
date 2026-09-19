import re

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
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

CLIENTS_PER_PAGE = 10


def _is_ajax(request):
    """
    Identifica requisições realizadas pela interface via AJAX.
    """
    return (
        request.headers.get("x-requested-with")
        == "XMLHttpRequest"
    )


def _only_digits(value):
    """
    Retorna somente os dígitos de um valor.

    Exemplos:
    123.456.789-00 -> 12345678900
    (51) 99999-9922 -> 51999999922
    """
    return re.sub(r"\D", "", value or "")


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
    """
    Lista os clientes com busca no banco e paginação.

    A busca é realizada antes da paginação para garantir que
    todos os clientes cadastrados possam ser encontrados,
    independentemente da página em que estejam.

    CPF e telefone também podem ser pesquisados utilizando
    máscara, pois o termo informado é normalizado para dígitos.
    """
    search = request.GET.get("q", "").strip()

    clients_queryset = Client.objects.all()

    if search:
        search_digits = _only_digits(search)

        search_query = (
            Q(nome_completo__icontains=search)
            | Q(email__icontains=search)
            | Q(cpf__icontains=search)
            | Q(telefone__icontains=search)
        )

        if search_digits:
            search_query |= (
                Q(cpf__icontains=search_digits)
                | Q(telefone__icontains=search_digits)
            )

        clients_queryset = clients_queryset.filter(
            search_query
        )

    paginator = Paginator(
        clients_queryset,
        CLIENTS_PER_PAGE,
    )

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "clients/client_list.html",
        {
            "clients": page_obj.object_list,
            "page_obj": page_obj,
            "paginator": paginator,
            "search": search,
            "total_clients": paginator.count,
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