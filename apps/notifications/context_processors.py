from .models import Notification
from .services import sync_pending_agenda_notifications


def notifications_context(request):
    """
    Disponibiliza as notificações do usuário autenticado
    para os templates globais do sistema.

    Antes de montar o contexto, sincroniza as pendências
    automáticas da Agenda para manter o sino consistente
    com o estado atual dos compromissos e prazos.
    """

    if not request.user.is_authenticated:
        return {
            "notifications_unread_count": 0,
            "notifications_recent": Notification.objects.none(),
        }

    # ==========================================================
    # SINCRONIZAÇÃO AUTOMÁTICA DA AGENDA
    # ==========================================================

    sync_pending_agenda_notifications(
        request.user
    )

    # ==========================================================
    # NOTIFICAÇÕES DO USUÁRIO
    # ==========================================================

    notifications = Notification.objects.filter(
        usuario=request.user,
    )

    return {
        "notifications_unread_count": notifications.filter(
            lida=False,
        ).count(),
        "notifications_recent": notifications[:6],
    }