from calendar import monthrange
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.cases.models import CaseHistory, LegalCase

from .forms import AgendaEventForm
from .models import AgendaEvent, GoogleCalendarConnection
from .services.google_calendar import (
    build_google_oauth_flow,
    create_google_calendar_event,
    get_google_calendar_connection,
    recreate_google_calendar_event,
    sync_google_event_to_lexcontrol,
    update_google_calendar_event,
)


# =========================================================
# HELPERS
# =========================================================


def _is_ajax(request):
    return (
        request.headers.get("x-requested-with")
        == "XMLHttpRequest"
    )


def _sync_created_event_with_google(event, user):
    """
    Tenta criar no Google Calendar o compromisso
    recém-criado no LexControl.

    A falha no Google nunca desfaz o evento local.
    """

    connection = get_google_calendar_connection(user)

    if not connection:
        return {
            "attempted": False,
            "success": False,
        }

    try:
        create_google_calendar_event(
            event,
            user,
        )

        return {
            "attempted": True,
            "success": True,
        }

    except Exception:
        return {
            "attempted": True,
            "success": False,
        }


def _sync_updated_event_with_google(event, user):
    """
    Tenta atualizar no Google Calendar um compromisso
    alterado no LexControl.

    Se o compromisso já foi identificado como removido
    do Google, a edição permanece somente no LexControl
    até que o usuário escolha reenviá-lo.

    A falha no Google nunca desfaz a alteração local.
    """

    connection = get_google_calendar_connection(user)

    if not connection:
        return {
            "attempted": False,
            "success": False,
            "removed": False,
        }

    if (
        event.google_sync_status
        == event.GoogleSyncStatus.REMOVED
    ):
        return {
            "attempted": False,
            "success": False,
            "removed": True,
        }

    try:
        update_google_calendar_event(
            event,
            user,
        )

        return {
            "attempted": True,
            "success": True,
            "removed": False,
        }

    except Exception:
        # A própria camada de serviço pode ter descoberto
        # durante a atualização que o evento foi removido.
        event.refresh_from_db(
            fields=[
                "google_sync_status",
            ]
        )

        return {
            "attempted": True,
            "success": False,
            "removed": (
                event.google_sync_status
                == event.GoogleSyncStatus.REMOVED
            ),
        }


def _build_completion_history_description(event):
    """
    Monta a descrição registrada no histórico do caso
    quando um compromisso é concluído.
    """

    date_text = event.data.strftime("%d/%m/%Y")

    if event.hora:
        time_text = event.hora.strftime("%H:%M")
        scheduled_text = (
            f"{date_text} às {time_text}"
        )
    else:
        scheduled_text = date_text

    description = (
        f"{event.get_tipo_display()} "
        f"'{event.titulo}', previsto para "
        f"{scheduled_text}, foi concluído."
    )

    if event.resultado:
        description += (
            f"\n\nResultado:\n{event.resultado}"
        )

    return description


def _build_not_completed_history_description(event):
    """
    Monta a descrição registrada no histórico do caso
    quando um compromisso é marcado como não realizado.
    """

    date_text = event.data.strftime("%d/%m/%Y")

    if event.hora:
        time_text = event.hora.strftime("%H:%M")
        scheduled_text = f"{date_text} às {time_text}"
    else:
        scheduled_text = date_text

    description = (
        f"{event.get_tipo_display()} "
        f"'{event.titulo}', previsto para "
        f"{scheduled_text}, foi marcado como não realizado."
    )

    if event.resultado:
        description += f"\n\nMotivo / observação:\n{event.resultado}"

    return description


# =========================================================
# LISTA DA AGENDA
# =========================================================


@login_required
def agenda_list(request):
    today = timezone.localdate()

    valid_views = {"overview", "upcoming", "pending", "history"}
    agenda_view = request.GET.get("view", "overview").strip().lower()
    if agenda_view not in valid_views:
        agenda_view = "overview"

    valid_periods = {"day", "week", "month"}
    agenda_period = request.GET.get("period", "month").strip().lower()
    if agenda_period not in valid_periods:
        agenda_period = "month"

    preview_limit = 5
    items_per_page = 10

    # Semana atual: domingo -> sábado.
    days_since_sunday = (today.weekday() + 1) % 7
    week_start = today - timedelta(days=days_since_sunday)
    week_end = week_start + timedelta(days=6)

    # Mês atual: dia 1 -> último dia real (28/29/30/31).
    month_start = today.replace(day=1)
    month_last_day = monthrange(today.year, today.month)[1]
    month_end = today.replace(day=month_last_day)

    active_statuses = [
        AgendaEvent.Status.SCHEDULED,
        AgendaEvent.Status.CONFIRMED,
    ]

    historical_statuses = [
        AgendaEvent.Status.COMPLETED,
        AgendaEvent.Status.NOT_COMPLETED,
        AgendaEvent.Status.CANCELED,
        AgendaEvent.Status.RESCHEDULED,
    ]

    # Os períodos abaixo são somente filtros locais.
    # Nenhuma sincronização Google é executada nesta view.
    active_events_queryset = (
        AgendaEvent.objects
        .select_related("caso", "caso__cliente", "concluido_por")
        .filter(status__in=active_statuses)
    )

    upcoming_period_querysets = {
        "day": (
            active_events_queryset
            .filter(data=today)
            .order_by("data", "hora")
        ),
        "week": (
            active_events_queryset
            .filter(data__range=(week_start, week_end))
            .order_by("data", "hora")
        ),
        "month": (
            active_events_queryset
            .filter(data__range=(month_start, month_end))
            .order_by("data", "hora")
        ),
    }

    upcoming_queryset = upcoming_period_querysets[agenda_period]
    upcoming_month_queryset = upcoming_period_querysets["month"]

    pending_queryset = (
        AgendaEvent.objects
        .select_related("caso", "caso__cliente", "concluido_por")
        .filter(
            data__lt=today,
            status__in=active_statuses,
        )
        .order_by("-data", "-hora")
    )

    historical_queryset = (
        AgendaEvent.objects
        .select_related("caso", "caso__cliente", "concluido_por")
        .filter(status__in=historical_statuses)
        .order_by("-data", "-hora")
    )

    # O card Próximos representa o mês atual.
    upcoming_count = upcoming_month_queryset.count()
    upcoming_period_count = upcoming_queryset.count()
    upcoming_day_count = upcoming_period_querysets["day"].count()
    upcoming_week_count = upcoming_period_querysets["week"].count()
    upcoming_month_count = upcoming_count

    pending_count = pending_queryset.count()
    history_count = historical_queryset.count()

    # Painel principal: prévias enxutas.
    upcoming_events = upcoming_month_queryset[:preview_limit]
    pending_confirmation_events = pending_queryset[:preview_limit]
    historical_events = historical_queryset[:preview_limit]

    agenda_events = None
    page_obj = None
    paginator = None

    if agenda_view != "overview":
        queryset_by_view = {
            "upcoming": upcoming_queryset,
            "pending": pending_queryset,
            "history": historical_queryset,
        }

        selected_queryset = queryset_by_view[agenda_view]
        paginator = Paginator(selected_queryset, items_per_page)
        page_obj = paginator.get_page(request.GET.get("page"))
        agenda_events = page_obj.object_list

    google_connection = (
        GoogleCalendarConnection.objects
        .filter(usuario=request.user)
        .first()
    )

    return render(
        request,
        "agenda/agenda_list.html",
        {
            "agenda_view": agenda_view,
            "agenda_period": agenda_period,

            "today": today,
            "week_start": week_start,
            "week_end": week_end,
            "month_start": month_start,
            "month_end": month_end,

            "upcoming_events": upcoming_events,
            "pending_confirmation_events": pending_confirmation_events,
            "historical_events": historical_events,

            "upcoming_count": upcoming_count,
            "pending_count": pending_count,
            "history_count": history_count,

            "upcoming_period_count": upcoming_period_count,
            "upcoming_day_count": upcoming_day_count,
            "upcoming_week_count": upcoming_week_count,
            "upcoming_month_count": upcoming_month_count,

            "agenda_events": agenda_events,
            "page_obj": page_obj,
            "paginator": paginator,

            "agenda_preview_limit": preview_limit,
            "agenda_items_per_page": items_per_page,

            "google_calendar_connected": bool(google_connection),
            "google_calendar_last_sync": (
                google_connection.ultima_sincronizacao_em
                if google_connection
                else None
            ),
        },
    )

# =========================================================
# CRIAÇÃO DE COMPROMISSO
# =========================================================


@login_required
def agenda_create(request, case_pk):
    legal_case = get_object_or_404(
        LegalCase.objects.select_related(
            "cliente",
            "status",
        ),
        pk=case_pk,
    )

    if request.method == "POST":
        form = AgendaEventForm(
            request.POST
        )

        if form.is_valid():
            event = form.save(
                commit=False
            )

            event.caso = legal_case
            event.criado_por = request.user

            # O LexControl é sempre a fonte principal.
            event.save()

            date_text = event.data.strftime(
                "%d/%m/%Y"
            )

            if event.hora:
                time_text = event.hora.strftime(
                    "%H:%M"
                )

                event_description = (
                    f"{event.get_tipo_display()} "
                    f"'{event.titulo}' agendado para "
                    f"{date_text} às {time_text}."
                )

            else:
                event_description = (
                    f"{event.get_tipo_display()} "
                    f"'{event.titulo}' agendado para "
                    f"{date_text}."
                )

            CaseHistory.objects.create(
                caso=legal_case,
                usuario=request.user,
                titulo="Compromisso agendado",
                descricao=event_description,
            )

            google_sync = (
                _sync_created_event_with_google(
                    event,
                    request.user,
                )
            )

            if google_sync["success"]:
                success_message = (
                    "Compromisso agendado e sincronizado "
                    "com o Google Agenda."
                )

            elif google_sync["attempted"]:
                success_message = (
                    "Compromisso agendado no LexControl, "
                    "mas não foi possível sincronizar "
                    "com o Google Agenda."
                )

            else:
                success_message = (
                    "Compromisso agendado com sucesso."
                )

            if _is_ajax(request):
                return JsonResponse(
                    {
                        "success": True,
                        "event_id": event.pk,
                        "google_sync_attempted": (
                            google_sync["attempted"]
                        ),
                        "google_synced": (
                            google_sync["success"]
                        ),
                        "message": success_message,
                    }
                )

            if (
                google_sync["attempted"]
                and not google_sync["success"]
            ):
                messages.warning(
                    request,
                    success_message,
                )

            else:
                messages.success(
                    request,
                    success_message,
                )

            return redirect(
                "cases:detail",
                pk=legal_case.pk,
            )

    else:
        form = AgendaEventForm()

    context = {
        "form": form,
        "case": legal_case,
    }

    if _is_ajax(request):
        return render(
            request,
            "agenda/_agenda_form_content.html",
            context,
            status=(
                400
                if request.method == "POST"
                else 200
            ),
        )

    return render(
        request,
        "agenda/agenda_form.html",
        context,
    )


# =========================================================
# EDIÇÃO DE COMPROMISSO
# =========================================================


@login_required
def agenda_update(request, pk):
    event = get_object_or_404(
        AgendaEvent.objects.select_related(
            "caso",
            "caso__cliente",
        ),
        pk=pk,
    )

    if request.method == "POST":
        form = AgendaEventForm(
            request.POST,
            instance=event,
        )

        if form.is_valid():
            updated_event = form.save()

            CaseHistory.objects.create(
                caso=updated_event.caso,
                usuario=request.user,
                titulo="Compromisso atualizado",
                descricao=(
                    f"O compromisso "
                    f"'{updated_event.titulo}' foi atualizado."
                ),
            )

            google_sync = (
                _sync_updated_event_with_google(
                    updated_event,
                    request.user,
                )
            )

            if google_sync["success"]:
                result_message = (
                    "Compromisso atualizado e sincronizado "
                    "com o Google Agenda."
                )

            elif google_sync.get("removed"):
                result_message = (
                    "Compromisso atualizado no LexControl. "
                    "Como ele foi removido do Google Agenda, "
                    "a alteração ficou salva apenas no "
                    "LexControl. Use “Reenviar ao Google” "
                    "para recriá-lo."
                )

            elif google_sync["attempted"]:
                result_message = (
                    "Compromisso atualizado no LexControl, "
                    "mas não foi possível sincronizar "
                    "com o Google Agenda."
                )

            else:
                result_message = (
                    "Compromisso atualizado com sucesso."
                )

            if _is_ajax(request):
                return JsonResponse(
                    {
                        "success": True,
                        "event_id": updated_event.pk,
                        "google_sync_attempted": (
                            google_sync["attempted"]
                        ),
                        "google_synced": (
                            google_sync["success"]
                        ),
                        "google_removed": (
                            google_sync.get(
                                "removed",
                                False,
                            )
                        ),
                        "message": result_message,
                    }
                )

            if (
                google_sync.get("removed")
                or (
                    google_sync["attempted"]
                    and not google_sync["success"]
                )
            ):
                messages.warning(
                    request,
                    result_message,
                )

            else:
                messages.success(
                    request,
                    result_message,
                )

            return redirect(
                "cases:detail",
                pk=updated_event.caso.pk,
            )

    else:
        form = AgendaEventForm(
            instance=event,
        )

    return render(
        request,
        "agenda/agenda_form.html",
        {
            "form": form,
            "case": event.caso,
            "event": event,
            "editing": True,
        },
    )

# =========================================================
# CONCLUSÃO DE COMPROMISSO
# =========================================================


@login_required
@require_POST
def agenda_complete(request, pk):
    """
    Conclui um compromisso no LexControl.

    A conclusão é operacional e não altera nem remove
    o compromisso correspondente no Google Agenda.
    """

    event = get_object_or_404(
        AgendaEvent.objects.select_related(
            "caso",
            "caso__cliente",
            "criado_por",
        ),
        pk=pk,
    )

    # -----------------------------------------------------
    # PROTEÇÃO CONTRA CONCLUSÃO DUPLICADA
    # -----------------------------------------------------

    if event.status == event.Status.COMPLETED:
        return JsonResponse(
            {
                "success": False,
                "message": (
                    "Este compromisso já foi concluído."
                ),
            },
            status=400,
        )

    # -----------------------------------------------------
    # SOMENTE EVENTOS ATIVOS PODEM SER CONCLUÍDOS
    # -----------------------------------------------------

    allowed_statuses = {
        event.Status.SCHEDULED,
        event.Status.CONFIRMED,
    }

    if event.status not in allowed_statuses:
        return JsonResponse(
            {
                "success": False,
                "message": (
                    "Este compromisso não pode ser concluído "
                    "no status atual."
                ),
            },
            status=400,
        )

    # -----------------------------------------------------
    # RESULTADO
    # -----------------------------------------------------

    resultado = (
        request.POST.get(
            "resultado",
            "",
        )
        .strip()
    )

    # -----------------------------------------------------
    # CONCLUSÃO
    # -----------------------------------------------------

    event.status = event.Status.COMPLETED
    event.resultado = resultado
    event.concluido_em = timezone.now()
    event.concluido_por = request.user

    event.save(
        update_fields=[
            "status",
            "resultado",
            "concluido_em",
            "concluido_por",
            "atualizado_em",
        ]
    )

    # -----------------------------------------------------
    # HISTÓRICO DO CASO
    # -----------------------------------------------------

    CaseHistory.objects.create(
        caso=event.caso,
        usuario=request.user,
        titulo="Compromisso concluído",
        descricao=(
            _build_completion_history_description(
                event
            )
        ),
    )

    # -----------------------------------------------------
    # IMPORTANTE:
    # nenhuma chamada ao Google Calendar é feita aqui.
    # O evento continua existindo normalmente no Google.
    # -----------------------------------------------------

    return JsonResponse(
        {
            "success": True,
            "event_id": event.pk,
            "status": event.status,
            "status_display": (
                event.get_status_display()
            ),
            "concluido_em": (
                event.concluido_em.isoformat()
            ),
            "message": (
                "Compromisso concluído com sucesso."
            ),
        }
    )


# =========================================================
# COMPROMISSO NÃO REALIZADO
# =========================================================


@login_required
@require_POST
def agenda_not_completed(request, pk):
    """
    Marca um compromisso como não realizado no LexControl.

    O motivo / observação é obrigatório.

    Esta ação é operacional e não altera nem remove
    o compromisso correspondente no Google Agenda.
    """

    event = get_object_or_404(
        AgendaEvent.objects.select_related(
            "caso",
            "caso__cliente",
            "criado_por",
        ),
        pk=pk,
    )

    allowed_statuses = {
        event.Status.SCHEDULED,
        event.Status.CONFIRMED,
    }

    if event.status not in allowed_statuses:
        return JsonResponse(
            {
                "success": False,
                "message": (
                    "Este compromisso não pode ser marcado "
                    "como não realizado no status atual."
                ),
            },
            status=400,
        )

    resultado = request.POST.get("resultado", "").strip()

    if not resultado:
        return JsonResponse(
            {
                "success": False,
                "message": (
                    "Informe o motivo ou uma observação "
                    "para registrar o compromisso como "
                    "não realizado."
                ),
            },
            status=400,
        )

    event.status = event.Status.NOT_COMPLETED
    event.resultado = resultado
    event.concluido_em = timezone.now()
    event.concluido_por = request.user

    event.save(
        update_fields=[
            "status",
            "resultado",
            "concluido_em",
            "concluido_por",
            "atualizado_em",
        ]
    )

    CaseHistory.objects.create(
        caso=event.caso,
        usuario=request.user,
        titulo="Compromisso não realizado",
        descricao=_build_not_completed_history_description(event),
    )

    # Nenhuma chamada ao Google é feita aqui.
    # O evento permanece no Google Agenda.

    return JsonResponse(
        {
            "success": True,
            "event_id": event.pk,
            "status": event.status,
            "status_display": event.get_status_display(),
            "concluido_em": event.concluido_em.isoformat(),
            "message": (
                "Compromisso registrado como não realizado."
            ),
        }
    )


# =========================================================
# GOOGLE OAUTH
# =========================================================


@login_required
def google_calendar_connect(request):
    """
    Inicia o fluxo OAuth do Google Calendar.
    """

    flow = build_google_oauth_flow()

    authorization_url, state = (
        flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
    )

    request.session[
        "google_oauth_state"
    ] = state

    if flow.code_verifier:
        request.session[
            "google_oauth_code_verifier"
        ] = flow.code_verifier

    return redirect(
        authorization_url
    )


@login_required
def google_calendar_callback(request):
    """
    Recebe o retorno do Google após a autorização
    e persiste a conexão do usuário.
    """

    oauth_error = request.GET.get(
        "error"
    )

    if oauth_error:
        messages.error(
            request,
            "A autorização do Google Agenda "
            "foi cancelada.",
        )

        return redirect(
            "agenda:list"
        )

    expected_state = request.session.pop(
        "google_oauth_state",
        None,
    )

    code_verifier = request.session.pop(
        "google_oauth_code_verifier",
        None,
    )

    received_state = request.GET.get(
        "state"
    )

    if (
        not expected_state
        or not received_state
        or expected_state != received_state
    ):
        messages.error(
            request,
            (
                "Não foi possível validar a autorização "
                "do Google Agenda. Tente conectar novamente."
            ),
        )

        return redirect(
            "agenda:list"
        )

    flow = build_google_oauth_flow(
        state=expected_state,
    )

    if code_verifier:
        flow.code_verifier = (
            code_verifier
        )

    try:
        flow.fetch_token(
            authorization_response=(
                request.build_absolute_uri()
            )
        )

    except Exception:
        messages.error(
            request,
            (
                "Não foi possível concluir a conexão "
                "com o Google Agenda."
            ),
        )

        return redirect(
            "agenda:list"
        )

    credentials = flow.credentials

    existing_connection = (
        GoogleCalendarConnection.objects
        .filter(
            usuario=request.user,
        )
        .first()
    )

    refresh_token = (
        credentials.refresh_token
    )

    if (
        not refresh_token
        and existing_connection
    ):
        refresh_token = (
            existing_connection.refresh_token
        )

    if not refresh_token:
        messages.error(
            request,
            (
                "O Google não forneceu uma autorização "
                "persistente. Tente conectar novamente."
            ),
        )

        return redirect(
            "agenda:list"
        )

    granted_scopes = (
        credentials.scopes
        or settings.GOOGLE_CALENDAR_SCOPES
    )

    GoogleCalendarConnection.objects.update_or_create(
        usuario=request.user,
        defaults={
            "refresh_token": refresh_token,
            "calendar_id": "primary",
            "scopes": " ".join(
                granted_scopes
            ),
        },
    )

    messages.success(
        request,
        "Google Agenda conectado com sucesso.",
    )

    return redirect(
        "agenda:list"
    )


# =========================================================
# SINCRONIZAÇÃO MANUAL GOOGLE -> LEXCONTROL
# =========================================================


@login_required
@require_POST
def google_calendar_sync(request):
    """
    Consulta no Google Calendar os compromissos
    vinculados ao LexControl e importa alterações.

    Também identifica eventos removidos do Google,
    sem apagar o compromisso local.
    """

    connection = (
        get_google_calendar_connection(
            request.user
        )
    )

    if not connection:
        return JsonResponse(
            {
                "success": False,
                "message": (
                    "Conecte sua conta do Google Agenda "
                    "antes de sincronizar."
                ),
            },
            status=400,
        )

    events = (
        AgendaEvent.objects
        .select_related(
            "caso",
            "caso__cliente",
            "criado_por",
        )
        .filter(
            criado_por=request.user,
        )
        .exclude(
            google_event_id="",
        )
        .order_by(
            "data",
            "hora",
        )
    )

    checked_count = 0
    updated_count = 0
    removed_count = 0
    error_count = 0
    auth_error = False

    for event in events:
        checked_count += 1

        try:
            result = (
                sync_google_event_to_lexcontrol(
                    event,
                    request.user,
                )
            )

        except Exception:
            error_count += 1
            continue

        reason = result.get(
            "reason"
        )

        if reason in (
            "deleted",
            "cancelled",
        ):
            removed_count += 1
            continue

        if reason == "auth_error":
            auth_error = True
            error_count += 1

            # Se a autenticação falhou, repetir a mesma
            # chamada para todos os demais eventos não
            # acrescenta informação útil.
            break

        if not result.get(
            "success",
            False,
        ):
            error_count += 1
            continue

        if result.get(
            "changed",
            False,
        ):
            updated_count += 1

    if auth_error:
        message = (
            "Não foi possível acessar o Google Agenda. "
            "A autorização da conta precisa ser renovada."
        )

    elif error_count:
        message = (
            "Sincronização concluída com avisos. "
            f"{updated_count} compromisso(s) atualizado(s), "
            f"{removed_count} removido(s) do Google e "
            f"{error_count} não puderam ser sincronizados."
        )

    elif removed_count and updated_count:
        message = (
            "Google Agenda sincronizado. "
            f"{updated_count} compromisso(s) atualizado(s) "
            f"e {removed_count} identificado(s) como "
            "removido(s) do Google."
        )

    elif removed_count:
        message = (
            "Google Agenda sincronizado. "
            f"{removed_count} compromisso(s) foi(ram) "
            "identificado(s) como removido(s) do Google."
        )

    elif updated_count:
        message = (
            "Google Agenda sincronizado. "
            f"{updated_count} compromisso(s) atualizado(s)."
        )

    else:
        message = (
            "Google Agenda sincronizado. "
            "Nenhuma alteração encontrada."
        )

    # =====================================================
    # ÚLTIMA SINCRONIZAÇÃO BEM-SUCEDIDA
    # =====================================================
    #
    # Só atualizamos este horário quando a consulta ao Google
    # termina sem falha de autenticação e sem erros de eventos.
    #
    # Eventos identificados como removidos no Google não são
    # considerados falha: eles foram consultados corretamente
    # e o LexControl conseguiu registrar esse estado.
    #
    # Se houver erro, preservamos a data/hora da última
    # sincronização realmente bem-sucedida.
    #

    sync_completed_successfully = (
        not auth_error
        and error_count == 0
    )

    if sync_completed_successfully:
        connection.ultima_sincronizacao_em = timezone.now()
        connection.save(
            update_fields=[
                "ultima_sincronizacao_em",
                "atualizado_em",
            ]
        )

    return JsonResponse(
        {
            "success": not auth_error,
            "checked": checked_count,
            "updated": updated_count,
            "removed": removed_count,
            "errors": error_count,
            "auth_error": auth_error,
            "sync_completed_successfully": (
                sync_completed_successfully
            ),
            "last_sync_at": (
                connection.ultima_sincronizacao_em.isoformat()
                if connection.ultima_sincronizacao_em
                else None
            ),
            "message": message,
        },
        status=(
            401
            if auth_error
            else 200
        ),
    )


# =========================================================
# REENVIAR EVENTO REMOVIDO AO GOOGLE
# =========================================================


@login_required
@require_POST
def google_calendar_resend(request, pk):
    """
    Recria no Google Calendar um compromisso que foi
    removido externamente, preservando o AgendaEvent
    existente no LexControl.
    """

    event = get_object_or_404(
        AgendaEvent.objects.select_related(
            "caso",
            "caso__cliente",
            "criado_por",
        ),
        pk=pk,
        criado_por=request.user,
    )

    if (
        event.google_sync_status
        != event.GoogleSyncStatus.REMOVED
    ):
        return JsonResponse(
            {
                "success": False,
                "message": (
                    "Este compromisso não está marcado "
                    "como removido do Google Agenda."
                ),
            },
            status=400,
        )

    connection = (
        get_google_calendar_connection(
            request.user
        )
    )

    if not connection:
        return JsonResponse(
            {
                "success": False,
                "message": (
                    "Conecte sua conta do Google Agenda "
                    "antes de reenviar o compromisso."
                ),
            },
            status=400,
        )

    old_google_event_id = (
        event.google_event_id
    )

    try:
        google_event = (
            recreate_google_calendar_event(
                event,
                request.user,
            )
        )

    except Exception:
        # A recriação falhou. O service foi projetado
        # para não apagar previamente os metadados
        # do vínculo antigo.
        event.refresh_from_db()

        return JsonResponse(
            {
                "success": False,
                "message": (
                    "Não foi possível reenviar o "
                    "compromisso ao Google Agenda. "
                    "O compromisso continua preservado "
                    "no LexControl."
                ),
            },
            status=502,
        )

    event.refresh_from_db()

    return JsonResponse(
        {
            "success": True,
            "event_id": event.pk,
            "old_google_event_id": (
                old_google_event_id
            ),
            "google_event_id": (
                event.google_event_id
            ),
            "google_event_link": (
                event.google_event_link
            ),
            "google_sync_status": (
                event.google_sync_status
            ),
            "message": (
                "Compromisso reenviado ao Google "
                "Agenda com sucesso."
            ),
        }
    )