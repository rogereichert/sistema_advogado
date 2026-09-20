from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Notification


@login_required
@require_POST
def mark_as_read(request, pk):
    """
    Marca uma única notificação do usuário autenticado como lida.
    """
    notification = get_object_or_404(
        Notification,
        pk=pk,
        usuario=request.user,
    )

    notification.marcar_como_lida()

    unread_count = Notification.objects.filter(
        usuario=request.user,
        lida=False,
    ).count()

    return JsonResponse(
        {
            "success": True,
            "notification_id": notification.pk,
            "unread_count": unread_count,
        }
    )


@login_required
@require_POST
def mark_all_as_read(request):
    """
    Marca todas as notificações não lidas do usuário autenticado como lidas.
    """
    now = timezone.now()

    updated_count = Notification.objects.filter(
        usuario=request.user,
        lida=False,
    ).update(
        lida=True,
        lida_em=now,
    )

    return JsonResponse(
        {
            "success": True,
            "updated_count": updated_count,
            "unread_count": 0,
        }
    )