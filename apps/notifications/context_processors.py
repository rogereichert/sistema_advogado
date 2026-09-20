from .models import Notification


def notifications_context(request):
    """
    Disponibiliza as notificações do usuário autenticado
    para os templates globais do sistema.
    """
    if not request.user.is_authenticated:
        return {
            "notifications_unread_count": 0,
            "notifications_recent": Notification.objects.none(),
        }

    notifications = Notification.objects.filter(
        usuario=request.user,
    )

    return {
        "notifications_unread_count": notifications.filter(
            lida=False,
        ).count(),
        "notifications_recent": notifications[:6],
    }