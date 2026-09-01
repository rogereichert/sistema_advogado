from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.clients.models import Client

from .forms import CaseMovementForm, LegalCaseForm
from .models import CaseHistory, CaseMovement, CaseStatus, LegalCase

from django.db.models import Q

@login_required
def case_create(request, client_pk):
    client = get_object_or_404(
        Client,
        pk=client_pk,
    )

    if request.method == "POST":
        form = LegalCaseForm(request.POST)

        if form.is_valid():
            legal_case = form.save(commit=False)

            legal_case.cliente = client

            legal_case.save()

            CaseHistory.objects.create(
                caso=legal_case,
                usuario=request.user,
                titulo="Caso criado",
                descricao=(
                    f"Caso jurídico criado com status "
                    f"'{legal_case.status.nome}'."
                ),
            )

            return redirect(
                "cases:detail",
                pk=legal_case.pk,
            )

    else:
        form = LegalCaseForm()

    return render(
        request,
        "cases/case_form.html",
        {
            "form": form,
            "client": client,
        },
    )

@login_required
def case_detail(request, pk):
    legal_case = get_object_or_404(
        LegalCase.objects.select_related(
            "cliente",
            "status",
        ),
        pk=pk,
    )

    history = legal_case.historico.select_related(
        "usuario"
    ).all()

    documents = legal_case.documentos.select_related(
        "enviado_por"
    ).all()

    required_documents = legal_case.documentos_necessarios.all()

    required_total = required_documents.count()

    required_received = required_documents.filter(
        recebido=True
    ).count()

    events = legal_case.eventos.all()

    required_progress = (
        round(
            (required_received / required_total) * 100
        )
        if required_total
        else 0
    )

    return render(
        request,
        "cases/case_detail.html",
        {
            "case": legal_case,
            "history": history,
            "documents": documents,
            "required_documents": required_documents,
            "required_total": required_total,
            "required_received": required_received,
            "required_progress": required_progress,
            "events": events,
        },
    )

@login_required
def case_update(request, pk):
    legal_case = get_object_or_404(
        LegalCase.objects.select_related(
            "cliente",
            "status",
        ),
        pk=pk,
    )

    old_status = legal_case.status

    if request.method == "POST":
        form = LegalCaseForm(
            request.POST,
            instance=legal_case,
        )

        if form.is_valid():
            updated_case = form.save(commit=False)

            new_status = form.cleaned_data["status"]

            updated_case.save()

            if old_status != new_status:
                CaseHistory.objects.create(
                    caso=updated_case,
                    usuario=request.user,
                    titulo="Status alterado",
                    descricao=(
                        f"Status alterado de "
                        f"'{old_status.nome}' para "
                        f"'{new_status.nome}'."
                    ),
                )

            return redirect(
                "cases:detail",
                pk=updated_case.pk,
            )

    else:
        form = LegalCaseForm(
            instance=legal_case,
        )

    return render(
        request,
        "cases/case_form.html",
        {
            "form": form,
            "client": legal_case.cliente,
            "case": legal_case,
            "editing": True,
        },
    )

@login_required
def movement_create(request, pk):
    legal_case = get_object_or_404(
        LegalCase.objects.select_related(
            "cliente",
            "status",
        ),
        pk=pk,
    )

    if request.method == "POST":
        form = CaseMovementForm(request.POST)

        if form.is_valid():
            movement = form.save(commit=False)

            movement.caso = legal_case
            movement.usuario = request.user

            movement.save()

            CaseHistory.objects.create(
                caso=legal_case,
                usuario=request.user,
                titulo=movement.titulo,
                descricao=movement.descricao,
            )

            return redirect(
                "cases:detail",
                pk=legal_case.pk,
            )

    else:
        form = CaseMovementForm()

    return render(
        request,
        "cases/movement_form.html",
        {
            "form": form,
            "case": legal_case,
        },
    )

@login_required
def case_list(request):
    cases = (
        LegalCase.objects
        .select_related(
            "cliente",
            "status",
        )
        .all()
    )

    search = request.GET.get(
        "q",
        "",
    ).strip()

    status = request.GET.get(
        "status",
        "",
    ).strip()

    area = request.GET.get(
        "area",
        "",
    ).strip()

    if search:
        cases = cases.filter(
            Q(titulo__icontains=search)
            | Q(cliente__nome_completo__icontains=search)
            | Q(cliente__cpf__icontains=search)
            | Q(numero_processo__icontains=search)
        )

    if status:
        cases = cases.filter(
            status_id=status
        )

    if area:
        cases = cases.filter(
            area_juridica__icontains=area
        )

    statuses = CaseStatus.objects.filter(
        ativo=True
    )

    return render(
        request,
        "cases/case_list.html",
        {
            "cases": cases,
            "statuses": statuses,
            "search": search,
            "selected_status": status,
            "area": area,
        },
    )