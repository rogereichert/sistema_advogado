import logging
from datetime import datetime, timedelta

from django.conf import settings
from django.utils import timezone

from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from apps.agenda.models import GoogleCalendarConnection


logger = logging.getLogger(__name__)


GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"

DEFAULT_EVENT_DURATION = timedelta(hours=1)


# =========================================================
# OAUTH / CONEXÃO
# =========================================================


def build_google_oauth_flow(state=None):
    """
    Cria o fluxo OAuth utilizado para conectar
    uma conta Google ao LexControl.
    """

    client_config = {
        "web": {
            "client_id": (
                settings.GOOGLE_CALENDAR_CLIENT_ID
            ),
            "client_secret": (
                settings.GOOGLE_CALENDAR_CLIENT_SECRET
            ),
            "auth_uri": (
                "https://accounts.google.com/o/oauth2/auth"
            ),
            "token_uri": GOOGLE_TOKEN_URI,
            "redirect_uris": [
                settings.GOOGLE_CALENDAR_REDIRECT_URI,
            ],
        }
    }

    flow = Flow.from_client_config(
        client_config=client_config,
        scopes=settings.GOOGLE_CALENDAR_SCOPES,
        state=state,
        autogenerate_code_verifier=True,
    )

    flow.redirect_uri = (
        settings.GOOGLE_CALENDAR_REDIRECT_URI
    )

    return flow


def build_google_credentials(connection):
    """
    Reconstrói as credenciais Google a partir
    do refresh token armazenado no LexControl.
    """

    scopes = (
        connection.scopes.split()
        if connection.scopes
        else settings.GOOGLE_CALENDAR_SCOPES
    )

    return Credentials(
        token=None,
        refresh_token=connection.refresh_token,
        token_uri=GOOGLE_TOKEN_URI,
        client_id=(
            settings.GOOGLE_CALENDAR_CLIENT_ID
        ),
        client_secret=(
            settings.GOOGLE_CALENDAR_CLIENT_SECRET
        ),
        scopes=scopes,
    )


def build_google_calendar_service(connection):
    """
    Cria o cliente da Google Calendar API.
    """

    credentials = build_google_credentials(
        connection
    )

    return build(
        "calendar",
        "v3",
        credentials=credentials,
        cache_discovery=False,
    )


def get_google_calendar_connection(user):
    """
    Retorna a conexão Google Calendar do usuário.
    """

    try:
        return GoogleCalendarConnection.objects.get(
            usuario=user
        )

    except GoogleCalendarConnection.DoesNotExist:
        return None


# =========================================================
# CONVERSÃO LEXCONTROL -> GOOGLE
# =========================================================


def build_google_event_body(event):
    """
    Converte um AgendaEvent do LexControl
    para o formato esperado pelo Google Calendar.
    """

    description_parts = []

    if event.descricao:
        description_parts.append(
            event.descricao.strip()
        )

    description_parts.append(
        f"Caso: {event.caso.titulo}"
    )

    description_parts.append(
        (
            "Cliente: "
            f"{event.caso.cliente.nome_completo}"
        )
    )

    if event.observacoes:
        description_parts.append(
            (
                "Observações: "
                f"{event.observacoes.strip()}"
            )
        )

    description_parts.append(
        "Evento sincronizado pelo LexControl."
    )

    body = {
        "summary": event.titulo,
        "description": "\n\n".join(
            description_parts
        ),
    }

    if event.local:
        body["location"] = event.local

    if event.hora:
        local_timezone = (
            timezone.get_current_timezone()
        )

        start_datetime = datetime.combine(
            event.data,
            event.hora,
        )

        start_datetime = timezone.make_aware(
            start_datetime,
            local_timezone,
        )

        end_datetime = (
            start_datetime
            + DEFAULT_EVENT_DURATION
        )

        body["start"] = {
            "dateTime": start_datetime.isoformat(),
            "timeZone": settings.TIME_ZONE,
        }

        body["end"] = {
            "dateTime": end_datetime.isoformat(),
            "timeZone": settings.TIME_ZONE,
        }

    else:
        end_date = (
            event.data
            + timedelta(days=1)
        )

        body["start"] = {
            "date": event.data.isoformat(),
        }

        body["end"] = {
            "date": end_date.isoformat(),
        }

    return body


# =========================================================
# PERSISTÊNCIA DOS DADOS GOOGLE
# =========================================================


def _save_google_event_data(
    event,
    connection,
    google_event,
):
    """
    Persiste os dados do evento criado ou atualizado
    com sucesso no Google Calendar.
    """

    event.google_event_id = (
        google_event.get("id", "")
    )

    event.google_calendar_id = (
        connection.calendar_id
    )

    event.google_event_link = (
        google_event.get("htmlLink", "")
    )

    event.google_synced_at = timezone.now()

    event.google_sync_status = (
        event.GoogleSyncStatus.SYNCED
    )

    event.save(
        update_fields=[
            "google_event_id",
            "google_calendar_id",
            "google_event_link",
            "google_synced_at",
            "google_sync_status",
            "atualizado_em",
        ]
    )


def _set_google_sync_status(
    event,
    status,
):
    """
    Atualiza somente o estado da integração Google.
    """

    if event.google_sync_status == status:
        return

    event.google_sync_status = status

    event.save(
        update_fields=[
            "google_sync_status",
            "atualizado_em",
        ]
    )


# =========================================================
# CRIAÇÃO NO GOOGLE
# =========================================================


def create_google_calendar_event(event, user):
    """
    Cria um compromisso no Google Calendar.

    Se já existir um Google Event ID válido,
    atualiza o compromisso existente.

    Eventos conhecidos como removidos não são
    recriados implicitamente por esta função.
    """

    if (
        event.google_sync_status
        == event.GoogleSyncStatus.REMOVED
    ):
        raise ValueError(
            "O compromisso foi removido do Google Agenda. "
            "Use a opção de reenviar ao Google."
        )

    if event.google_event_id:
        return update_google_calendar_event(
            event,
            user,
        )

    connection = get_google_calendar_connection(
        user
    )

    if not connection:
        raise ValueError(
            "O usuário não possui uma conta "
            "Google Agenda conectada."
        )

    service = build_google_calendar_service(
        connection
    )

    body = build_google_event_body(
        event
    )

    google_event = (
        service.events()
        .insert(
            calendarId=connection.calendar_id,
            body=body,
        )
        .execute()
    )

    _save_google_event_data(
        event,
        connection,
        google_event,
    )

    return google_event


# =========================================================
# REENVIO DE EVENTO REMOVIDO
# =========================================================


def recreate_google_calendar_event(event, user):
    """
    Recria no Google Calendar um compromisso que
    continua existindo no LexControl.

    Esta função NÃO tenta reutilizar o antigo
    google_event_id.

    Os metadados locais somente são substituídos
    depois que o Google confirma a nova criação.
    """

    connection = get_google_calendar_connection(
        user
    )

    if not connection:
        raise ValueError(
            "O usuário não possui uma conta "
            "Google Agenda conectada."
        )

    if (
        event.google_sync_status
        != event.GoogleSyncStatus.REMOVED
    ):
        raise ValueError(
            "Este compromisso não está marcado "
            "como removido do Google Agenda."
        )

    service = build_google_calendar_service(
        connection
    )

    body = build_google_event_body(
        event
    )

    # Importante:
    # não limpamos o google_event_id antigo antes
    # desta chamada. Se o Google falhar, o estado
    # anterior permanece intacto no LexControl.
    google_event = (
        service.events()
        .insert(
            calendarId=connection.calendar_id,
            body=body,
        )
        .execute()
    )

    # Só agora, depois da criação confirmada,
    # substituímos os dados do vínculo antigo.
    _save_google_event_data(
        event,
        connection,
        google_event,
    )

    logger.info(
        (
            "Evento recriado no Google Calendar. "
            "usuario_id=%s agenda_event_id=%s "
            "novo_google_event_id=%s"
        ),
        user.pk,
        event.pk,
        event.google_event_id,
    )

    return google_event


# =========================================================
# ATUALIZAÇÃO LEXCONTROL -> GOOGLE
# =========================================================


def update_google_calendar_event(event, user):
    """
    Atualiza no Google Calendar o compromisso
    correspondente ao AgendaEvent.

    Se ainda não houver vínculo Google, cria.

    Se o vínculo estiver marcado como removido,
    não tenta utilizar o antigo google_event_id.
    """

    if (
        event.google_sync_status
        == event.GoogleSyncStatus.REMOVED
    ):
        raise ValueError(
            "O compromisso foi removido do Google Agenda. "
            "A alteração foi preservada no LexControl, "
            "mas o compromisso precisa ser reenviado "
            "ao Google."
        )

    if not event.google_event_id:
        return create_google_calendar_event(
            event,
            user,
        )

    connection = get_google_calendar_connection(
        user
    )

    if not connection:
        raise ValueError(
            "O usuário não possui uma conta "
            "Google Agenda conectada."
        )

    calendar_id = (
        event.google_calendar_id
        or connection.calendar_id
    )

    service = build_google_calendar_service(
        connection
    )

    body = build_google_event_body(
        event
    )

    try:
        google_event = (
            service.events()
            .update(
                calendarId=calendar_id,
                eventId=event.google_event_id,
                body=body,
            )
            .execute()
        )

    except HttpError as error:
        status = _get_http_status(error)

        if status in (404, 410):
            _set_google_sync_status(
                event,
                event.GoogleSyncStatus.REMOVED,
            )

            logger.info(
                (
                    "Evento não encontrado durante "
                    "atualização no Google Calendar. "
                    "usuario_id=%s agenda_event_id=%s "
                    "google_event_id=%s status=%s"
                ),
                user.pk,
                event.pk,
                event.google_event_id,
                status,
            )

            raise ValueError(
                "O compromisso não existe mais no "
                "Google Agenda. Ele continua salvo no "
                "LexControl e pode ser reenviado."
            ) from error

        _set_google_sync_status(
            event,
            event.GoogleSyncStatus.ERROR,
        )

        raise

    except RefreshError:
        _set_google_sync_status(
            event,
            event.GoogleSyncStatus.ERROR,
        )

        raise

    event.google_event_id = (
        google_event.get(
            "id",
            event.google_event_id,
        )
    )

    event.google_calendar_id = calendar_id

    event.google_event_link = (
        google_event.get(
            "htmlLink",
            event.google_event_link,
        )
    )

    event.google_synced_at = timezone.now()

    event.google_sync_status = (
        event.GoogleSyncStatus.SYNCED
    )

    event.save(
        update_fields=[
            "google_event_id",
            "google_calendar_id",
            "google_event_link",
            "google_synced_at",
            "google_sync_status",
            "atualizado_em",
        ]
    )

    return google_event


# =========================================================
# CONVERSÃO GOOGLE -> LEXCONTROL
# =========================================================


def _parse_google_event_datetime(google_event):
    """
    Converte o início de um evento do Google Calendar
    para data e hora utilizadas pelo LexControl.

    Eventos de dia inteiro retornam hora=None.
    """

    start = google_event.get(
        "start",
        {},
    )

    if start.get("date"):
        event_date = datetime.fromisoformat(
            start["date"]
        ).date()

        return event_date, None

    date_time_value = start.get(
        "dateTime"
    )

    if not date_time_value:
        raise ValueError(
            "O evento do Google não possui "
            "uma data de início válida."
        )

    google_datetime = datetime.fromisoformat(
        date_time_value.replace(
            "Z",
            "+00:00",
        )
    )

    if timezone.is_aware(
        google_datetime
    ):
        google_datetime = timezone.localtime(
            google_datetime,
            timezone.get_current_timezone(),
        )

    return (
        google_datetime.date(),
        google_datetime.time().replace(
            tzinfo=None,
        ),
    )


def _get_http_status(error):
    """
    Obtém o status HTTP de uma exceção da
    Google API de forma segura.
    """

    response = getattr(
        error,
        "resp",
        None,
    )

    return getattr(
        response,
        "status",
        None,
    )


# =========================================================
# SINCRONIZAÇÃO GOOGLE -> LEXCONTROL
# =========================================================


def sync_google_event_to_lexcontrol(event, user):
    """
    Consulta no Google Calendar o evento vinculado
    ao AgendaEvent e traz as alterações para o
    LexControl.

    O compromisso local nunca é excluído
    automaticamente.
    """

    if not event.google_event_id:
        return {
            "success": False,
            "changed": False,
            "reason": "not_linked",
        }

    connection = get_google_calendar_connection(
        user
    )

    if not connection:
        return {
            "success": False,
            "changed": False,
            "reason": "not_connected",
        }

    calendar_id = (
        event.google_calendar_id
        or connection.calendar_id
    )

    try:
        service = build_google_calendar_service(
            connection
        )

        google_event = (
            service.events()
            .get(
                calendarId=calendar_id,
                eventId=event.google_event_id,
            )
            .execute()
        )

    except RefreshError:
        _set_google_sync_status(
            event,
            event.GoogleSyncStatus.ERROR,
        )

        logger.warning(
            (
                "Falha de autenticação Google Calendar. "
                "usuario_id=%s agenda_event_id=%s"
            ),
            user.pk,
            event.pk,
        )

        return {
            "success": False,
            "changed": False,
            "reason": "auth_error",
        }

    except HttpError as error:
        status = _get_http_status(
            error
        )

        if status in (404, 410):
            _set_google_sync_status(
                event,
                event.GoogleSyncStatus.REMOVED,
            )

            logger.info(
                (
                    "Evento Google ausente ou removido. "
                    "usuario_id=%s agenda_event_id=%s "
                    "google_event_id=%s status=%s"
                ),
                user.pk,
                event.pk,
                event.google_event_id,
                status,
            )

            return {
                "success": True,
                "changed": False,
                "reason": "deleted",
                "http_status": status,
            }

        _set_google_sync_status(
            event,
            event.GoogleSyncStatus.ERROR,
        )

        logger.exception(
            (
                "Erro da Google Calendar API. "
                "usuario_id=%s agenda_event_id=%s "
                "google_event_id=%s status=%s"
            ),
            user.pk,
            event.pk,
            event.google_event_id,
            status,
        )

        return {
            "success": False,
            "changed": False,
            "reason": "google_error",
            "http_status": status,
        }

    except Exception:
        _set_google_sync_status(
            event,
            event.GoogleSyncStatus.ERROR,
        )

        logger.exception(
            (
                "Erro inesperado ao consultar "
                "Google Calendar. "
                "usuario_id=%s agenda_event_id=%s "
                "google_event_id=%s"
            ),
            user.pk,
            event.pk,
            event.google_event_id,
        )

        return {
            "success": False,
            "changed": False,
            "reason": "google_error",
        }

    # -----------------------------------------------------
    # CANCELADO / REMOVIDO
    # -----------------------------------------------------

    if (
        google_event.get("status")
        == "cancelled"
    ):
        _set_google_sync_status(
            event,
            event.GoogleSyncStatus.REMOVED,
        )

        logger.info(
            (
                "Evento Google cancelado. "
                "usuario_id=%s agenda_event_id=%s "
                "google_event_id=%s"
            ),
            user.pk,
            event.pk,
            event.google_event_id,
        )

        return {
            "success": True,
            "changed": False,
            "reason": "cancelled",
        }

    # -----------------------------------------------------
    # DATA / HORÁRIO
    # -----------------------------------------------------

    try:
        event_date, event_time = (
            _parse_google_event_datetime(
                google_event
            )
        )

    except (TypeError, ValueError):
        _set_google_sync_status(
            event,
            event.GoogleSyncStatus.ERROR,
        )

        logger.exception(
            (
                "Evento Google com data inválida. "
                "usuario_id=%s agenda_event_id=%s "
                "google_event_id=%s"
            ),
            user.pk,
            event.pk,
            event.google_event_id,
        )

        return {
            "success": False,
            "changed": False,
            "reason": "invalid_event",
        }

    # -----------------------------------------------------
    # DADOS IMPORTADOS
    # -----------------------------------------------------

    google_title = (
        google_event.get("summary")
        or event.titulo
    )

    google_location = (
        google_event.get("location")
        or ""
    )

    changed_fields = []

    if event.titulo != google_title:
        event.titulo = google_title
        changed_fields.append(
            "titulo"
        )

    if event.data != event_date:
        event.data = event_date
        changed_fields.append(
            "data"
        )

    if event.hora != event_time:
        event.hora = event_time
        changed_fields.append(
            "hora"
        )

    if event.local != google_location:
        event.local = google_location
        changed_fields.append(
            "local"
        )

    # O Google respondeu normalmente.
    # Portanto o vínculo está saudável.
    event.google_sync_status = (
        event.GoogleSyncStatus.SYNCED
    )

    event.google_synced_at = (
        timezone.now()
    )

    fields_to_save = list(
        changed_fields
    )

    fields_to_save.extend(
        [
            "google_sync_status",
            "google_synced_at",
            "atualizado_em",
        ]
    )

    event.save(
        update_fields=fields_to_save
    )

    if changed_fields:
        logger.info(
            (
                "Evento atualizado a partir do "
                "Google Calendar. "
                "usuario_id=%s agenda_event_id=%s "
                "campos=%s"
            ),
            user.pk,
            event.pk,
            ", ".join(changed_fields),
        )

    return {
        "success": True,
        "changed": bool(
            changed_fields
        ),
        "reason": None,
        "fields": changed_fields,
        "google_event": google_event,
    }