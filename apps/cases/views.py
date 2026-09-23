import re

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import OuterRef, Q, Subquery
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.clients.models import Client

from .forms import CaseMovementForm, LegalCaseForm
from .models import CaseHistory, CaseMovement, CaseStatus, LegalCase

CASES_PER_PAGE = 10

def _is_ajax(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


def _display_history_value(value):
    """
    Converte valores para uma apresentação amigável no histórico.
    """
    if value is None:
        return ""

    return str(value).strip()


def _build_case_update_history(old_values, new_values):
    """
    Compara os dados anteriores e novos do caso e devolve
    uma lista de descrições para o histórico.

    Campos curtos:
        mostram o valor anterior e o novo.

    Campos longos:
        registram apenas que o conteúdo foi atualizado.
    """

    changes = []

    # =========================================================
    # TÍTULO
    # =========================================================

    old_title = _display_history_value(
        old_values.get("titulo")
    )
    new_title = _display_history_value(
        new_values.get("titulo")
    )

    if old_title != new_title:
        changes.append(
            f"Título alterado de "
            f"'{old_title}' para '{new_title}'."
        )

    # =========================================================
    # ÁREA JURÍDICA
    # =========================================================

    old_area = _display_history_value(
        old_values.get("area_juridica")
    )
    new_area = _display_history_value(
        new_values.get("area_juridica")
    )

    if old_area != new_area:

        if not old_area and new_area:
            changes.append(
                f"Área jurídica informada: '{new_area}'."
            )

        elif old_area and not new_area:
            changes.append(
                f"Área jurídica removida. "
                f"Valor anterior: '{old_area}'."
            )

        else:
            changes.append(
                f"Área jurídica alterada de "
                f"'{old_area}' para '{new_area}'."
            )

    # =========================================================
    # STATUS
    # =========================================================

    old_status = old_values.get("status")
    new_status = new_values.get("status")

    old_status_id = (
        old_status.pk
        if old_status
        else None
    )

    new_status_id = (
        new_status.pk
        if new_status
        else None
    )

    if old_status_id != new_status_id:

        old_status_name = (
            old_status.nome
            if old_status
            else ""
        )

        new_status_name = (
            new_status.nome
            if new_status
            else ""
        )

        if not old_status_name and new_status_name:
            changes.append(
                f"Status informado: '{new_status_name}'."
            )

        elif old_status_name and not new_status_name:
            changes.append(
                f"Status removido. "
                f"Valor anterior: '{old_status_name}'."
            )

        else:
            changes.append(
                f"Status alterado de "
                f"'{old_status_name}' para "
                f"'{new_status_name}'."
            )

    # =========================================================
    # DESCRIÇÃO DA CAUSA
    # =========================================================

    old_description = _display_history_value(
        old_values.get("descricao")
    )
    new_description = _display_history_value(
        new_values.get("descricao")
    )

    if old_description != new_description:

        if not old_description and new_description:
            changes.append(
                "Descrição da causa adicionada."
            )

        elif old_description and not new_description:
            changes.append(
                "Descrição da causa removida."
            )

        else:
            changes.append(
                "Descrição da causa atualizada."
            )

    # =========================================================
    # NÚMERO DO PROCESSO
    # =========================================================

    old_process_number = _display_history_value(
        old_values.get("numero_processo")
    )
    new_process_number = _display_history_value(
        new_values.get("numero_processo")
    )

    if old_process_number != new_process_number:

        if not old_process_number and new_process_number:
            changes.append(
                f"Número do processo informado: "
                f"'{new_process_number}'."
            )

        elif old_process_number and not new_process_number:
            changes.append(
                f"Número do processo removido. "
                f"Valor anterior: '{old_process_number}'."
            )

        else:
            changes.append(
                f"Número do processo alterado de "
                f"'{old_process_number}' para "
                f"'{new_process_number}'."
            )

    # =========================================================
    # VARA
    # =========================================================

    old_court = _display_history_value(
        old_values.get("vara")
    )
    new_court = _display_history_value(
        new_values.get("vara")
    )

    if old_court != new_court:

        if not old_court and new_court:
            changes.append(
                f"Vara informada: '{new_court}'."
            )

        elif old_court and not new_court:
            changes.append(
                f"Vara removida. "
                f"Valor anterior: '{old_court}'."
            )

        else:
            changes.append(
                f"Vara alterada de "
                f"'{old_court}' para '{new_court}'."
            )

    # =========================================================
    # COMARCA
    # =========================================================

    old_district = _display_history_value(
        old_values.get("comarca")
    )
    new_district = _display_history_value(
        new_values.get("comarca")
    )

    if old_district != new_district:

        if not old_district and new_district:
            changes.append(
                f"Comarca informada: '{new_district}'."
            )

        elif old_district and not new_district:
            changes.append(
                f"Comarca removida. "
                f"Valor anterior: '{old_district}'."
            )

        else:
            changes.append(
                f"Comarca alterada de "
                f"'{old_district}' para "
                f"'{new_district}'."
            )

    # =========================================================
    # OBSERVAÇÕES INTERNAS
    # =========================================================

    old_notes = _display_history_value(
        old_values.get("observacoes")
    )
    new_notes = _display_history_value(
        new_values.get("observacoes")
    )

    if old_notes != new_notes:

        if not old_notes and new_notes:
            changes.append(
                "Observações internas adicionadas."
            )

        elif old_notes and not new_notes:
            changes.append(
                "Observações internas removidas."
            )

        else:
            changes.append(
                "Observações internas atualizadas."
            )

    return changes


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

            # =================================================
            # AJAX
            # =================================================

            if _is_ajax(request):
                return JsonResponse(
                    {
                        "success": True,
                        "case_id": legal_case.pk,
                        "redirect_url": (
                            redirect(
                                "cases:detail",
                                pk=legal_case.pk,
                            ).url
                        ),
                        "message": (
                            "Caso jurídico criado com sucesso."
                        ),
                    }
                )

            return redirect(
                "cases:detail",
                pk=legal_case.pk,
            )

    else:
        form = LegalCaseForm()

    context = {
        "form": form,
        "client": client,
        "case": None,
        "editing": False,
    }

    if _is_ajax(request):
        return render(
            request,
            "cases/_case_form_content.html",
            context,
            status=(
                400
                if request.method == "POST"
                else 200
            ),
        )

    return render(
        request,
        "cases/case_form.html",
        context,
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

    required_documents = (
        legal_case.documentos_necessarios.all()
    )

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

    # =========================================================
    # SNAPSHOT DOS DADOS ANTES DA EDIÇÃO
    # =========================================================

    old_values = {
        "titulo": legal_case.titulo,
        "area_juridica": legal_case.area_juridica,
        "status": legal_case.status,
        "descricao": legal_case.descricao,
        "numero_processo": legal_case.numero_processo,
        "vara": legal_case.vara,
        "comarca": legal_case.comarca,
        "observacoes": legal_case.observacoes,
    }

    if request.method == "POST":
        form = LegalCaseForm(
            request.POST,
            instance=legal_case,
        )

        if form.is_valid():

            # =================================================
            # NOVOS VALORES JÁ VALIDADOS E NORMALIZADOS
            # =================================================

            new_values = {
                "titulo": form.cleaned_data["titulo"],
                "area_juridica": form.cleaned_data.get(
                    "area_juridica"
                ),
                "status": form.cleaned_data["status"],
                "descricao": form.cleaned_data.get(
                    "descricao"
                ),
                "numero_processo": form.cleaned_data.get(
                    "numero_processo"
                ),
                "vara": form.cleaned_data.get(
                    "vara"
                ),
                "comarca": form.cleaned_data.get(
                    "comarca"
                ),
                "observacoes": form.cleaned_data.get(
                    "observacoes"
                ),
            }

            changes = _build_case_update_history(
                old_values,
                new_values,
            )

            updated_case = form.save()

            # =================================================
            # HISTÓRICO
            # Uma edição gera somente um evento.
            # Se nada mudou, nenhum evento é criado.
            # =================================================

            if changes:
                CaseHistory.objects.create(
                    caso=updated_case,
                    usuario=request.user,
                    titulo="Caso atualizado",
                    descricao="\n".join(changes),
                )

            # =================================================
            # AJAX
            # =================================================

            if _is_ajax(request):
                return JsonResponse(
                    {
                        "success": True,
                        "case_id": updated_case.pk,
                        "changed": bool(changes),
                        "changes_count": len(changes),
                        "message": (
                            "Caso atualizado com sucesso."
                            if changes
                            else "Nenhuma alteração foi realizada."
                        ),
                    }
                )

            return redirect(
                "cases:detail",
                pk=updated_case.pk,
            )

    else:
        form = LegalCaseForm(
            instance=legal_case,
        )

    context = {
        "form": form,
        "client": legal_case.cliente,
        "case": legal_case,
        "editing": True,
    }

    if _is_ajax(request):
        return render(
            request,
            "cases/_case_form_content.html",
            context,
            status=(
                400
                if request.method == "POST"
                else 200
            ),
        )

    return render(
        request,
        "cases/case_form.html",
        context,
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

            if _is_ajax(request):
                return JsonResponse(
                    {
                        "success": True,
                        "movement_id": movement.pk,
                        "message": (
                            "Movimentação registrada com sucesso."
                        ),
                    }
                )

            return redirect(
                "cases:detail",
                pk=legal_case.pk,
            )

    else:
        form = CaseMovementForm()

    context = {
        "form": form,
        "case": legal_case,
    }

    if _is_ajax(request):
        return render(
            request,
            "cases/_movement_form_content.html",
            context,
            status=(
                400
                if request.method == "POST"
                else 200
            ),
        )

    return render(
        request,
        "cases/movement_form.html",
        context,
    )


@login_required
def case_list(request):
    # =========================================================
    # ÚLTIMA ATIVIDADE REGISTRADA NO HISTÓRICO
    # =========================================================
    #
    # A data da última modificação não vem simplesmente de uma
    # edição do cadastro do caso.
    #
    # Ela representa a atividade mais recente registrada no
    # CaseHistory: criação, edição, movimentação etc.
    #
    # A Subquery evita fazer uma consulta separada para cada
    # caso exibido na listagem.
    # =========================================================

    latest_history = (
        CaseHistory.objects
        .filter(caso_id=OuterRef("pk"))
        .order_by("-criado_em")
        .values("criado_em")[:1]
    )

    cases_queryset = (
        LegalCase.objects
        .select_related(
            "cliente",
            "status",
        )
        .annotate(
            ultima_modificacao=Subquery(
                latest_history
            )
        )
        .all()
    )

    # =========================================================
    # PARÂMETROS DE FILTRO
    # =========================================================

    search = request.GET.get(
        "q",
        "",
    ).strip()

    status = request.GET.get(
        "status",
        "",
    ).strip()

    # =========================================================
    # BUSCA
    # =========================================================

    if search:
        search_digits = re.sub(
            r"\D",
            "",
            search,
        )

        search_filter = (
            Q(titulo__icontains=search)
            | Q(
                cliente__nome_completo__icontains=search
            )
            | Q(
                numero_processo__icontains=search
            )
        )

        if search_digits:
            search_filter |= Q(
                cliente__cpf__icontains=search_digits
            )

        cases_queryset = cases_queryset.filter(
            search_filter
        )

    # =========================================================
    # STATUS
    # =========================================================

    if status:
        cases_queryset = cases_queryset.filter(
            status_id=status
        )

    # =========================================================
    # STATUS DISPONÍVEIS
    # =========================================================

    statuses = CaseStatus.objects.filter(
        ativo=True
    )

    # =========================================================
    # PAGINAÇÃO
    # =========================================================

    paginator = Paginator(
        cases_queryset,
        CASES_PER_PAGE,
    )

    page_number = request.GET.get(
        "page"
    )

    page_obj = paginator.get_page(
        page_number
    )

    # =========================================================
    # CLIENTES CADASTRADOS
    # =========================================================

    has_clients = Client.objects.exists()

    # =========================================================
    # TEMPLATE
    # =========================================================

    return render(
        request,
        "cases/case_list.html",
        {
            "cases": page_obj.object_list,
            "page_obj": page_obj,
            "paginator": paginator,
            "statuses": statuses,
            "search": search,
            "selected_status": status,
            "total_cases": paginator.count,
        },
    )