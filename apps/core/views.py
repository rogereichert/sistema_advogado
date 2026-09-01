from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render
from django.utils import timezone

from apps.agenda.models import AgendaEvent
from apps.cases.models import LegalCase
from apps.clients.models import Client


@login_required
def dashboard(request):
    today = timezone.localdate()

    total_clients = Client.objects.count()

    closed_statuses = [
        "Concluído",
        "Arquivado",
        "Cancelado",
    ]

    active_cases = (
        LegalCase.objects
        .exclude(status__nome__in=closed_statuses)
        .count()
    )

    waiting_documents = LegalCase.objects.filter(
        status__nome="Aguardando documentação"
    ).count()

    recent_cases = (
        LegalCase.objects
        .select_related(
            "cliente",
            "status",
        )
        .order_by("-criado_em")[:5]
    )

    status_summary = (
        LegalCase.objects
        .values("status__nome")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    upcoming_events = (
        AgendaEvent.objects
        .select_related(
            "caso",
            "caso__cliente",
        )
        .filter(data__gte=today)
        .order_by(
            "data",
            "hora",
        )[:5]
    )

    next_event = upcoming_events.first()

    return render(
        request,
        "core/dashboard.html",
        {
            "total_clients": total_clients,
            "active_cases": active_cases,
            "waiting_documents": waiting_documents,
            "recent_cases": recent_cases,
            "status_summary": status_summary,
            "upcoming_events": upcoming_events,
            "next_event": next_event,
        },
    )