from django.urls import reverse
from django.utils import timezone

from apps.agenda.models import AgendaEvent

from .models import Notification


# ==============================================================
# CHAVES DE NOTIFICAÇÃO
# ==============================================================


def _document_pending_key(required_document):
    """
    Retorna a chave única utilizada para identificar a notificação
    referente à pendência de um documento necessário.
    """
    return f"document:pending:{required_document.pk}"


def _agenda_pending_key(event):
    """
    Retorna a chave única utilizada para identificar a notificação
    referente a um compromisso ou prazo pendente da Agenda.
    """
    return f"agenda:pending:{event.pk}"


# ==============================================================
# DOCUMENTAÇÃO PENDENTE
# ==============================================================


def create_pending_document_notification(
    *,
    required_document,
    usuario,
):
    """
    Cria a notificação de documentação pendente.

    A chave única impede que o mesmo documento necessário gere
    notificações duplicadas enquanto representar a mesma pendência.

    Se o documento já estiver recebido, nenhuma notificação é criada.
    """

    if required_document.recebido:
        return None, False

    key = _document_pending_key(required_document)

    legal_case = required_document.caso

    destination_url = reverse(
        "cases:detail",
        kwargs={
            "pk": legal_case.pk,
        },
    )

    notification, created = Notification.objects.get_or_create(
        chave=key,
        defaults={
            "usuario": usuario,
            "tipo": Notification.Type.DOCUMENT,
            "nivel": Notification.Level.ATTENTION,
            "titulo": "Documento pendente",
            "mensagem": (
                f"{required_document.nome} — "
                f"{legal_case.cliente.nome_completo}"
            ),
            "url_destino": destination_url,
        },
    )

    return notification, created


# ==============================================================
# RESOLUÇÃO DA PENDÊNCIA DOCUMENTAL
# ==============================================================


def resolve_pending_document_notification(
    *,
    required_document,
):
    """
    Remove a notificação ativa relacionada à pendência documental.

    A notificação representa uma situação que ainda exige atenção.
    Quando o documento é recebido ou removido do checklist, essa
    pendência deixa de existir.

    Neste primeiro modelo, a notificação é excluída porque ainda não
    possuímos um estado separado de "resolvida".
    """

    key = _document_pending_key(required_document)

    deleted_count, _ = Notification.objects.filter(
        chave=key,
    ).delete()

    return deleted_count > 0


# ==============================================================
# REABERTURA DA PENDÊNCIA DOCUMENTAL
# ==============================================================


def reopen_pending_document_notification(
    *,
    required_document,
    usuario,
):
    """
    Recria a notificação quando um documento anteriormente recebido
    volta ao estado pendente.

    Como a notificação anterior é removida ao resolver a pendência,
    a mesma chave pode ser utilizada novamente com segurança.
    """

    if required_document.recebido:
        return None, False

    return create_pending_document_notification(
        required_document=required_document,
        usuario=usuario,
    )


# ==============================================================
# AGENDA PENDENTE
# ==============================================================


def _create_pending_agenda_notification(event):
    """
    Cria uma notificação para um compromisso ou prazo que permaneceu
    ativo após a sua data prevista.

    Prazo:
        nível urgente

    Demais compromissos:
        nível atenção
    """

    if not event.criado_por_id:
        return None, False

    today = timezone.localdate()

    active_statuses = {
        AgendaEvent.Status.SCHEDULED,
        AgendaEvent.Status.CONFIRMED,
    }

    if (
        event.data >= today
        or event.status not in active_statuses
    ):
        return None, False

    is_deadline = event.tipo == "prazo"

    key = _agenda_pending_key(event)

    destination_url = (
        f'{reverse("agenda:list")}?view=pending'
    )

    notification, created = Notification.objects.get_or_create(
        chave=key,
        defaults={
            "usuario": event.criado_por,
            "tipo": (
                Notification.Type.DEADLINE
                if is_deadline
                else Notification.Type.AGENDA
            ),
            "nivel": (
                Notification.Level.URGENT
                if is_deadline
                else Notification.Level.ATTENTION
            ),
            "titulo": (
                "Prazo pendente"
                if is_deadline
                else "Compromisso pendente"
            ),
            "mensagem": (
                f"{event.titulo} — "
                f"{event.caso.cliente.nome_completo}"
            ),
            "url_destino": destination_url,
        },
    )

    return notification, created


# ==============================================================
# SINCRONIZAÇÃO DAS PENDÊNCIAS DA AGENDA
# ==============================================================


def sync_pending_agenda_notifications(usuario):
    """
    Mantém as notificações da Agenda sincronizadas com o estado
    atual dos compromissos pertencentes ao usuário.

    Regra de pendência:

        data < hoje
        +
        status Agendado ou Confirmado

    A função é idempotente:

    - cria notificações que estão faltando;
    - não duplica notificações existentes;
    - remove notificações automáticas de eventos que deixaram
      de ser pendentes.
    """

    if not usuario or not usuario.is_authenticated:
        return {
            "created": 0,
            "removed": 0,
        }

    today = timezone.localdate()

    active_statuses = [
        AgendaEvent.Status.SCHEDULED,
        AgendaEvent.Status.CONFIRMED,
    ]

    pending_events = (
        AgendaEvent.objects
        .select_related(
            "caso",
            "caso__cliente",
            "criado_por",
        )
        .filter(
            criado_por=usuario,
            data__lt=today,
            status__in=active_statuses,
        )
        .order_by(
            "data",
            "hora",
            "pk",
        )
    )

    pending_event_ids = []

    created_count = 0

    for event in pending_events:
        pending_event_ids.append(
            event.pk
        )

        _, created = (
            _create_pending_agenda_notification(
                event
            )
        )

        if created:
            created_count += 1

    # ==========================================================
    # LIMPEZA DE NOTIFICAÇÕES QUE NÃO SÃO MAIS PENDÊNCIAS
    # ==========================================================

    agenda_notifications = Notification.objects.filter(
        usuario=usuario,
        chave__startswith="agenda:pending:",
    )

    valid_keys = {
        f"agenda:pending:{event_id}"
        for event_id in pending_event_ids
    }

    obsolete_notification_ids = []

    for notification in agenda_notifications.only(
        "pk",
        "chave",
    ):
        if notification.chave not in valid_keys:
            obsolete_notification_ids.append(
                notification.pk
            )

    removed_count = 0

    if obsolete_notification_ids:
        removed_count, _ = (
            Notification.objects
            .filter(
                pk__in=obsolete_notification_ids,
            )
            .delete()
        )

    return {
        "created": created_count,
        "removed": removed_count,
    }