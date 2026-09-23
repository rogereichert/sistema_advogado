from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render
from django.utils import timezone

from apps.agenda.models import AgendaEvent
from apps.cases.models import CaseHistory, LegalCase
from apps.clients.models import Client
from apps.documents.models import RequiredDocument


# =========================================================
# CONFIGURAÇÕES DO DASHBOARD
# =========================================================

CLOSED_CASE_STATUSES = [
    "Concluído",
    "Arquivado",
    "Cancelado",
]

ACTIVE_AGENDA_STATUSES = [
    AgendaEvent.Status.SCHEDULED,
    AgendaEvent.Status.CONFIRMED,
]

RECENT_ACTIVITY_LIMIT = 7
ATTENTION_ITEMS_LIMIT = 6


@login_required
def dashboard(request):
    """
    Visão geral do escritório.

    A dashboard apresenta:
    - fotografia resumida da carteira;
    - pendências concretas que exigem atenção;
    - movimentações recentes;
    - distribuição dos casos por status;
    - resumo da agenda do dia.

    A Agenda continua responsável pela gestão completa dos
    compromissos e prazos.
    """

    today = timezone.localdate()

    # =========================================================
    # FOTOGRAFIA DO ESCRITÓRIO
    # =========================================================

    total_clients = Client.objects.count()

    active_cases_queryset = (
        LegalCase.objects
        .exclude(status__nome__in=CLOSED_CASE_STATUSES)
    )

    active_cases = active_cases_queryset.count()

    waiting_document_cases = (
        RequiredDocument.objects
        .filter(recebido=False)
        .values("caso_id")
        .distinct()
        .count()
    )

    # =========================================================
    # DOCUMENTOS NECESSÁRIOS PENDENTES
    # =========================================================
    #
    # Aqui usamos a pendência documental real:
    #
    # RequiredDocument.recebido = False
    #
    # Um caso pode possuir mais de um documento pendente.
    # Por isso:
    #
    # waiting_document_cases = quantidade de CASOS cujo status
    # indica espera por documentação.
    #
    # pending_documents_count = quantidade real de DOCUMENTOS
    # necessários ainda não recebidos.
    # =========================================================

    pending_documents_queryset = (
        RequiredDocument.objects
        .select_related(
            "caso",
            "caso__cliente",
        )
        .filter(recebido=False)
        .order_by(
            "criado_em",
            "pk",
        )
    )

    pending_documents_count = pending_documents_queryset.count()

    # =========================================================
    # PENDÊNCIAS DA AGENDA
    # =========================================================
    #
    # Um evento é considerado pendente quando:
    #
    # - continua Agendado ou Confirmado;
    # - sua data já passou;
    # - ainda não recebeu desfecho.
    # =========================================================

    overdue_agenda_queryset = (
        AgendaEvent.objects
        .select_related(
            "caso",
            "caso__cliente",
        )
        .filter(
            status__in=ACTIVE_AGENDA_STATUSES,
            data__lt=today,
        )
        .order_by(
            "data",
            "hora",
            "pk",
        )
    )

    overdue_agenda_count = overdue_agenda_queryset.count()

    overdue_deadlines_count = (
        overdue_agenda_queryset
        .filter(tipo="prazo")
        .count()
    )

    overdue_commitments_count = (
        overdue_agenda_queryset
        .exclude(tipo="prazo")
        .count()
    )

    # =========================================================
    # O QUE PRECISA DE ATENÇÃO
    # =========================================================
    #
    # Cada item possui sua própria origem e seu próprio destino.
    #
    # Não usamos mais um contador genérico que leva sempre para
    # a Agenda.
    # =========================================================

    attention_items = []

    # ---------------------------------------------------------
    # Documentos necessários ainda não recebidos
    # ---------------------------------------------------------

    for required_document in pending_documents_queryset[
        :ATTENTION_ITEMS_LIMIT
    ]:
        attention_items.append(
            {
                "kind": "document",
                "title": "Documento pendente",
                "description": required_document.nome,
                "case": required_document.caso,
                "client": required_document.caso.cliente,
                "date": required_document.criado_em,
                "object_id": required_document.pk,
            }
        )

    # ---------------------------------------------------------
    # Eventos anteriores aguardando desfecho
    # ---------------------------------------------------------

    for event in overdue_agenda_queryset[
        :ATTENTION_ITEMS_LIMIT
    ]:
        is_deadline = event.tipo == "prazo"

        attention_items.append(
            {
                "kind": (
                    "deadline"
                    if is_deadline
                    else "agenda"
                ),
                "title": (
                    "Prazo aguardando desfecho"
                    if is_deadline
                    else "Compromisso aguardando desfecho"
                ),
                "description": event.titulo,
                "case": event.caso,
                "client": event.caso.cliente,
                "date": event.data,
                "time": event.hora,
                "object_id": event.pk,
            }
        )

    # ---------------------------------------------------------
    # Ordenação da atenção
    # ---------------------------------------------------------
    #
    # Eventos vencidos aparecem antes porque possuem natureza
    # temporal. Em seguida aparecem documentos pendentes.
    #
    # Dentro de cada grupo, preservamos a ordem fornecida pelos
    # respectivos querysets.
    # ---------------------------------------------------------

    attention_priority = {
        "deadline": 0,
        "agenda": 1,
        "document": 2,
    }

    attention_items.sort(
        key=lambda item: attention_priority.get(
            item["kind"],
            99,
        )
    )

    attention_items = attention_items[
        :ATTENTION_ITEMS_LIMIT
    ]

    attention_count = (
        pending_documents_count
        + overdue_agenda_count
    )

    # =========================================================
    # DISTRIBUIÇÃO DA CARTEIRA
    # =========================================================

    status_summary = list(
        LegalCase.objects
        .values("status__nome")
        .annotate(total=Count("id"))
        .order_by(
            "-total",
            "status__nome",
        )
    )

    total_cases = sum(
        item["total"]
        for item in status_summary
    )

    # =========================================================
    # ATIVIDADE RECENTE
    # =========================================================
    #
    # CaseHistory representa melhor a movimentação do escritório
    # do que simplesmente listar os últimos casos cadastrados.
    # =========================================================

    recent_activity = (
        CaseHistory.objects
        .select_related(
            "caso",
            "caso__cliente",
            "usuario",
        )
        .order_by("-criado_em")[
            :RECENT_ACTIVITY_LIMIT
        ]
    )

    # =========================================================
    # AGENDA DE HOJE
    # =========================================================

    today_events_queryset = (
        AgendaEvent.objects
        .select_related(
            "caso",
            "caso__cliente",
        )
        .filter(
            data=today,
            status__in=ACTIVE_AGENDA_STATUSES,
        )
        .order_by(
            "hora",
            "pk",
        )
    )

    today_events_count = today_events_queryset.count()

    today_deadlines_count = (
        today_events_queryset
        .filter(tipo="prazo")
        .count()
    )

    today_commitments_count = (
        today_events_queryset
        .exclude(tipo="prazo")
        .count()
    )

    next_today_event = today_events_queryset.first()

    # =========================================================
    # CONTEXTO
    # =========================================================

    context = {
        # -----------------------------------------------------
        # Fotografia do escritório
        # -----------------------------------------------------
        "total_clients": total_clients,
        "active_cases": active_cases,
        "waiting_document_cases": waiting_document_cases,

        # -----------------------------------------------------
        # Documentação
        # -----------------------------------------------------
        "pending_documents_count": pending_documents_count,

        # -----------------------------------------------------
        # Atenção
        # -----------------------------------------------------
        "attention_count": attention_count,
        "attention_items": attention_items,

        # -----------------------------------------------------
        # Agenda pendente
        # -----------------------------------------------------
        "overdue_agenda_count": overdue_agenda_count,
        "overdue_deadlines_count": overdue_deadlines_count,
        "overdue_commitments_count": overdue_commitments_count,

        # -----------------------------------------------------
        # Carteira
        # -----------------------------------------------------
        "total_cases": total_cases,
        "status_summary": status_summary,

        # -----------------------------------------------------
        # Atividade recente
        # -----------------------------------------------------
        "recent_activity": recent_activity,

        # -----------------------------------------------------
        # Agenda de hoje
        # -----------------------------------------------------
        "today": today,
        "today_events_count": today_events_count,
        "today_deadlines_count": today_deadlines_count,
        "today_commitments_count": today_commitments_count,
        "next_today_event": next_today_event,
    }

    return render(
        request,
        "core/dashboard.html",
        context,
    )