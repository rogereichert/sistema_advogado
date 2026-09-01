from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.cases.models import CaseHistory, LegalCase

from .forms import AgendaEventForm
from .models import AgendaEvent


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
        ),
        pk=case_pk,
    )

    if request.method == "POST":
        form = AgendaEventForm(request.POST)

        if form.is_valid():
            event = form.save(commit=False)

            event.caso = legal_case
            event.criado_por = request.user

            event.save()

            date_text = event.data.strftime("%d/%m/%Y")

            if event.hora:
                time_text = event.hora.strftime("%H:%M")

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

            return redirect(
                "cases:detail",
                pk=legal_case.pk,
            )

    else:
        form = AgendaEventForm()

    return render(
        request,
        "agenda/agenda_form.html",
        {
            "form": form,
            "case": legal_case,
        },
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