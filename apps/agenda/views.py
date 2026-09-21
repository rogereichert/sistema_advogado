from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
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


# =========================================================
# LISTA DA AGENDA
# =========================================================


@login_required
def agenda_list(request):
    today = timezone.localdate()

    upcoming_events = (
        AgendaEvent.objects
        .select_related(
            "caso",
            "caso__cliente",
        )
        .filter(
            data__gte=today,
        )
        .order_by(
            "data",
            "hora",
        )
    )

    past_events = (
        AgendaEvent.objects
        .select_related(
            "caso",
            "caso__cliente",
        )
        .filter(
            data__lt=today,
        )
        .order_by(
            "-data",
            "-hora",
        )[:20]
    )

    google_connection = (
        GoogleCalendarConnection.objects
        .filter(
            usuario=request.user,
        )
        .first()
    )

    return render(
        request,
        "agenda/agenda_list.html",
        {
            "upcoming_events": upcoming_events,
            "past_events": past_events,
            "today": today,
            "google_calendar_connected": bool(
                google_connection
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

    return JsonResponse(
        {
            "success": not auth_error,
            "checked": checked_count,
            "updated": updated_count,
            "removed": removed_count,
            "errors": error_count,
            "auth_error": auth_error,
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