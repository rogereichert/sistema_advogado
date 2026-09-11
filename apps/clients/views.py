from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ClientForm
from .models import Client

from django.utils import timezone

from apps.agenda.models import AgendaEvent


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

            return redirect(
                "clients:detail",
                pk=client.pk,
            )

    else:
        form = ClientForm()

    return render(
        request,
        "clients/client_form.html",
        {
            "form": form,
        },
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
            form.save()

            return redirect(
                "clients:detail",
                pk=client.pk,
            )

    else:
        form = ClientForm(
            instance=client,
        )

    return render(
        request,
        "clients/client_form.html",
        {
            "form": form,
            "client": client,
        },
    )


@login_required
def client_detail(request, pk):
    client = get_object_or_404(
        Client,
        pk=pk,
    )

    cases = client.casos.select_related(
        "status"
    ).all()

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
            "next_event": next_event,
        },
    )


@login_required
def client_detail(request, pk):
    client = get_object_or_404(
        Client,
        pk=pk,
    )

    cases = client.casos.select_related(
        "status"
    ).all()

    closed_statuses = [
        "Concluído",
        "Arquivado",
        "Cancelado",
    ]

    active_cases_count = cases.exclude(
        status__nome__in=closed_statuses
    ).count()

    return render(
        request,
        "clients/client_detail.html",
        {
            "client": client,
            "cases": cases,
            "active_cases_count": active_cases_count,
        },
    )