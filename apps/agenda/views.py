from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.cases.models import CaseHistory, LegalCase

from .forms import AgendaEventForm
from .models import AgendaEvent


def _is_ajax(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


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

    return render(
        request,
        "agenda/agenda_list.html",
        {
            "upcoming_events": upcoming_events,
            "past_events": past_events,
            "today": today,
        },
    )


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

            if _is_ajax(request):
                return JsonResponse(
                    {
                        "success": True,
                        "event_id": event.pk,
                        "message": (
                            "Compromisso agendado com sucesso."
                        ),
                    }
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