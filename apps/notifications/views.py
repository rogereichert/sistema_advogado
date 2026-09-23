from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Notification


NOTIFICATIONS_PER_PAGE = 10


# ==============================================================
# CENTRAL DE NOTIFICAÇÕES
# ==============================================================


@login_required
def notification_list(request):
    """
    Exibe a Central de Notificações do usuário autenticado.

    Filtros disponíveis:
        - Todas
        - Não lidas

    As notificações são sempre restritas ao usuário autenticado.
    """

    selected_filter = request.GET.get(
        "filter",
        "all",
    ).strip().lower()

    if selected_filter not in {
        "all",
        "unread",
    }:
        selected_filter = "all"

    # ==========================================================
    # QUERYSET BASE
    # ==========================================================

    notifications_queryset = Notification.objects.filter(
        usuario=request.user,
    )

    # ==========================================================
    # CONTADORES
    # ==========================================================

    total_notifications = notifications_queryset.count()

    unread_notifications = notifications_queryset.filter(
        lida=False,
    ).count()

    # ==========================================================
    # FILTRO
    # ==========================================================

    if selected_filter == "unread":
        notifications_queryset = notifications_queryset.filter(
            lida=False,
        )

    # ==========================================================
    # PAGINAÇÃO
    # ==============================================================

    paginator = Paginator(
        notifications_queryset,
        NOTIFICATIONS_PER_PAGE,
    )

    page_number = request.GET.get(
        "page"
    )

    page_obj = paginator.get_page(
        page_number
    )

    # ==========================================================
    # TEMPLATE
    # ==============================================================

    return render(
        request,
        "notifications/notification_list.html",
        {
            "notifications": page_obj.object_list,
            "page_obj": page_obj,
            "paginator": paginator,
            "selected_filter": selected_filter,
            "total_notifications": total_notifications,
            "unread_notifications": unread_notifications,
        },
    )


# ==============================================================
# MARCAR UMA NOTIFICAÇÃO COMO LIDA
# ==============================================================


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


# ==============================================================
# MARCAR TODAS COMO LIDAS
# ==============================================================


@login_required
@require_POST
def mark_all_as_read(request):
    """
    Marca todas as notificações não lidas do usuário autenticado
    como lidas.
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