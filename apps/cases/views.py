import re
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import OuterRef, Q, Subquery
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.clients.models import Client

from .forms import CaseMovementForm, LegalCaseForm
from .models import CaseHistory, CaseMovement, CaseStatus, LegalCase
from .services.datajud import (
    DataJudConfigurationError,
    DataJudConnectionError,
    DataJudError,
    DataJudInvalidResponseError,
    DataJudRateLimitError,
    DataJudTimeoutError,
    DataJudTribunalNaoSuportadoError,
    DataJudUnavailableError,
    consultar_processo,
)


CASES_PER_PAGE = 10


def _is_ajax(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


def _datajud_session_key(request):
    """

    Gera uma chave de sessão específica para o usuário autenticado.

    A sessão já pertence ao navegador atual, mas manter o user id

    explícito torna a finalidade da chave mais clara.

    """
    return f"datajud_consulta_usuario_{request.user.pk}"


def _guardar_consulta_datajud(request, resultado):
    """

    Guarda temporariamente na sessão somente os dados necessários

    para uma futura vinculação ao caso.

    Nenhum LegalCase é alterado nesta etapa.

    """
    dados = resultado.get("dados") or {}
    consulta = {
        "numero_processo": resultado.get("numero_processo") or "",
        "tribunal": resultado.get("tribunal") or {},
        "dados": {
            "numero_processo": dados.get("numero_processo"),
            "tribunal": dados.get("tribunal"),
            "grau": dados.get("grau"),
            "data_ajuizamento": dados.get("data_ajuizamento"),
            "classe": dados.get("classe") or {},
            "sistema": dados.get("sistema") or {},
            "orgao_julgador": dados.get("orgao_julgador") or {},
        },
        "consultado_em": timezone.now().isoformat(),
    }
    request.session[
        _datajud_session_key(request)
    ] = consulta
    request.session.modified = True


def _normalizar_numero_cnj_local(numero):
    """

    Normaliza o número apenas para comparação interna.

    A validação estrutural/roteamento continua sendo responsabilidade

    do service DataJud.

    """
    return re.sub(r"\D", "", str(numero or ""))


def _parse_datajud_datetime(valor):
    """

    Converte datas recebidas/armazenadas pela integração em datetime

    timezone-aware quando possível.

    """
    if not valor:
        return None
    if isinstance(valor, datetime):
        data = valor
    else:
        texto = str(valor).strip()
        data = None
        formatos = (
            "%Y%m%d%H%M%S",
            "%Y%m%d",
        )
        for formato in formatos:
            try:
                data = datetime.strptime(texto, formato)
                break
            except ValueError:
                continue
        if data is None:
            try:
                data = datetime.fromisoformat(
                    texto.replace("Z", "+00:00")
                )
            except ValueError:
                return None
    if timezone.is_naive(data):
        data = timezone.make_aware(
            data,
            timezone.get_current_timezone(),
        )
    return data


def _obter_valor_datajud(dados, campo, subcampo="nome"):
    """

    Aceita tanto valores simples quanto objetos do DataJud.

    Exemplos:

        "PJe"

        {"codigo": 1, "nome": "PJe"}

    """
    valor = dados.get(campo)
    if isinstance(valor, dict):
        return valor.get(subcampo) or ""
    return valor or ""


def _aplicar_consulta_datajud(request, legal_case):
    """Confirma consulta válida sem sobrescrever os campos editados no formulário.

    Os códigos oficiais só são preservados quando os nomes correspondem aos
    valores retornados. Vara e comarca nunca são inferidas do órgão julgador.
    """
    if request.POST.get("datajud_aplicar") != "1":
        return False
    chave = _datajud_session_key(request)
    consulta = request.session.get(chave)
    if not consulta:
        return False
    numero_caso = _normalizar_numero_cnj_local(legal_case.numero_processo)
    numero_consultado = _normalizar_numero_cnj_local(
        consulta.get("numero_processo")
    )
    if not numero_caso or numero_caso != numero_consultado:
        return False
    dados = consulta.get("dados") or {}
    classe = dados.get("classe") or {}
    orgao = dados.get("orgao_julgador") or {}
    if not isinstance(classe, dict):
        classe = {}
    if not isinstance(orgao, dict):
        orgao = {}

    def mesmo_nome(valor_atual, valor_oficial):
        def normalizar(valor):
            return " ".join(str(valor or "").casefold().split())
        return bool(valor_oficial) and normalizar(valor_atual) == normalizar(valor_oficial)
    # form.save(commit=False) já contém os valores finais digitados/revisados.
    # Não aplicar novamente os nomes e a data da sessão por cima deles.
    if mesmo_nome(legal_case.classe_processual, classe.get("nome")):
        legal_case.classe_processual_codigo = str(classe.get("codigo") or "")
    else:
        legal_case.classe_processual_codigo = ""
    if mesmo_nome(legal_case.orgao_julgador_nome, orgao.get("nome")):
        legal_case.orgao_julgador_codigo = str(orgao.get("codigo") or "")
    else:
        legal_case.orgao_julgador_codigo = ""
    legal_case.datajud_consultado_em = (
        _parse_datajud_datetime(consulta.get("consultado_em"))
        or timezone.now()
    )
    request.session.pop(chave, None)
    request.session.modified = True
    return True


@login_required

@require_POST


def datajud_consultar_processo(request):
    """

    Consulta um processo judicial na API pública do DataJud.

    Esta view não cria nem altera um LegalCase.

    Ela apenas recebe o número CNJ e devolve os dados

    encontrados para a interface.

    """
    numero_processo = request.POST.get(
        "numero_processo",
        "",
    ).strip()
    if not numero_processo:
        return JsonResponse(
            {
                "success": False,
                "status": "NUMERO_OBRIGATORIO",
                "message": (
                    "Informe o número do processo para realizar "
                    "a consulta."
                ),
            },
            status=400,
        )
    try:
        resultado = consultar_processo(
            numero_processo,
        )
    except DataJudTribunalNaoSuportadoError as erro:
        return JsonResponse(
            {
                "success": False,
                "status": erro.codigo,
                "message": str(erro),
            },
            status=400,
        )
    except DataJudRateLimitError as erro:
        resposta = {
            "success": False,
            "status": erro.codigo,
            "message": str(erro),
        }
        if erro.retry_after:
            resposta["retry_after"] = erro.retry_after
        return JsonResponse(
            resposta,
            status=429,
        )
    except DataJudTimeoutError as erro:
        return JsonResponse(
            {
                "success": False,
                "status": erro.codigo,
                "message": str(erro),
            },
            status=504,
        )
    except (
        DataJudConnectionError,
        DataJudUnavailableError,
    ) as erro:
        return JsonResponse(
            {
                "success": False,
                "status": erro.codigo,
                "message": str(erro),
            },
            status=503,
        )
    except (
        DataJudConfigurationError,
        DataJudInvalidResponseError,
    ) as erro:
        return JsonResponse(
            {
                "success": False,
                "status": erro.codigo,
                "message": str(erro),
            },
            status=502,
        )
    except DataJudError as erro:
        return JsonResponse(
            {
                "success": False,
                "status": erro.codigo,
                "message": str(erro),
            },
            status=502,
        )
    # =========================================================
    # PROCESSO NÃO ENCONTRADO
    # =========================================================
    #
    # A consulta pode ter sido executada com sucesso no DataJud
    # e, ainda assim, não existir nenhum processo correspondente.
    #
    # Nesse cenário, o service retorna:
    #     sucesso=True
    #     status=PROCESSO_NAO_ENCONTRADO
    #
    # Portanto, esse estado precisa ser tratado antes do retorno
    # genérico de sucesso da view.
    # =========================================================
    if resultado.get("status") == "PROCESSO_NAO_ENCONTRADO":
        return JsonResponse(
            {
                "success": False,
                "status": "PROCESSO_NAO_ENCONTRADO",
                "message": resultado.get(
                    "mensagem",
                    "Nenhum processo foi encontrado no DataJud.",
                ),
                "numero_processo": resultado.get(
                    "numero_processo",
                    numero_processo,
                ),
            },
            status=404,
        )
    # =========================================================
    # OUTROS RESULTADOS SEM SUCESSO
    # =========================================================
    if not resultado.get("sucesso"):
        return JsonResponse(
            {
                "success": False,
                "status": resultado.get(
                    "status",
                    "ERRO_DATAJUD",
                ),
                "message": resultado.get(
                    "mensagem",
                    "Não foi possível consultar o processo.",
                ),
                "numero_processo": resultado.get(
                    "numero_processo",
                    numero_processo,
                ),
            },
            status=400,
        )
    # =========================================================
    # PROCESSO ENCONTRADO
    # =========================================================
    _guardar_consulta_datajud(
        request,
        resultado,
    )
    return JsonResponse(
        {
            "success": True,
            "status": resultado.get(
                "status",
                "PROCESSO_ENCONTRADO",
            ),
            "message": resultado.get(
                "mensagem",
                "Processo encontrado no DataJud.",
            ),
            "numero_processo": resultado.get(
                "numero_processo",
            ),
            "tribunal": resultado.get(
                "tribunal",
            ),
            "dados": resultado.get(
                "dados",
                {},
            ),
        }
    )


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


def _build_process_update_history(old_values, legal_case):
    """Registra mudanças dos campos processuais editáveis no mesmo evento."""
    changes = []
    labels = {
        "tribunal": "Tribunal",
        "grau": "Grau",
        "classe_processual": "Classe processual",
        "sistema_processual": "Sistema processual",
        "orgao_julgador_nome": "Órgão julgador",
        "data_ajuizamento": "Data de ajuizamento",
    }

    def comparable_date(value):
        if value is None:
            return None
        if isinstance(value, datetime):
            return timezone.localtime(value).date() if timezone.is_aware(value) else value.date()
        return value  # datetime.date, se o formulário o fornecer
    for field, label in labels.items():
        old = old_values.get(field)
        new = getattr(legal_case, field)
        if field == "data_ajuizamento":
            old = comparable_date(old)
            new = comparable_date(new)
        if old == new:
            continue
        if old and new:
            changes.append(f"{label} atualizado.")
        elif new:
            changes.append(f"{label} informado.")
        else:
            changes.append(f"{label} removido.")
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
            datajud_vinculado = _aplicar_consulta_datajud(
                request,
                legal_case,
            )
            legal_case.save()
            descricao_historico = (
                f"Caso jurídico criado com status "
                f"'{legal_case.status.nome}'."
            )
            if datajud_vinculado:
                descricao_historico += (
                    "\nDados processuais vinculados via DataJud."
                )
            CaseHistory.objects.create(
                caso=legal_case,
                usuario=request.user,
                titulo="Caso criado",
                descricao=descricao_historico,
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
        LegalCase.objects.select_related("cliente", "status"), pk=pk
    )
    old_values = {
        "titulo": legal_case.titulo,
        "area_juridica": legal_case.area_juridica,
        "status": legal_case.status,
        "descricao": legal_case.descricao,
        "numero_processo": legal_case.numero_processo,
        "vara": legal_case.vara,
        "comarca": legal_case.comarca,
        "observacoes": legal_case.observacoes,
        "tribunal": legal_case.tribunal,
        "grau": legal_case.grau,
        "classe_processual": legal_case.classe_processual,
        "sistema_processual": legal_case.sistema_processual,
        "orgao_julgador_nome": legal_case.orgao_julgador_nome,
        "data_ajuizamento": legal_case.data_ajuizamento,
    }
    if request.method == "POST":
        form = LegalCaseForm(request.POST, instance=legal_case)
        if form.is_valid():
            new_values = {
                "titulo": form.cleaned_data["titulo"],
                "area_juridica": form.cleaned_data.get("area_juridica"),
                "status": form.cleaned_data["status"],
                "descricao": form.cleaned_data.get("descricao"),
                "numero_processo": form.cleaned_data.get("numero_processo"),
                "vara": form.cleaned_data.get("vara"),
                "comarca": form.cleaned_data.get("comarca"),
                "observacoes": form.cleaned_data.get("observacoes"),
            }
            changes = _build_case_update_history(old_values, new_values)
            updated_case = form.save(commit=False)
            datajud_vinculado = _aplicar_consulta_datajud(request, updated_case)
            if not datajud_vinculado:
                if updated_case.classe_processual != old_values["classe_processual"]:
                    updated_case.classe_processual_codigo = ""
                if updated_case.orgao_julgador_nome != old_values["orgao_julgador_nome"]:
                    updated_case.orgao_julgador_codigo = ""
            changes.extend(_build_process_update_history(old_values, updated_case))
            if datajud_vinculado:
                changes.append("Dados processuais vinculados via DataJud.")
            updated_case.save()
            if changes:
                CaseHistory.objects.create(
                    caso=updated_case,
                    usuario=request.user,
                    titulo="Caso atualizado",
                    descricao="\n".join(changes),
                )
            if _is_ajax(request):
                return JsonResponse({
                    "success": True,
                    "case_id": updated_case.pk,
                    "changed": bool(changes),
                    "changes_count": len(changes),
                    "message": (
                        "Caso atualizado com sucesso."
                        if changes else "Nenhuma alteração foi realizada."
                    ),
                })
            return redirect("cases:detail", pk=updated_case.pk)
    else:
        form = LegalCaseForm(instance=legal_case)
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
            status=400 if request.method == "POST" else 200,
        )
    return render(request, "cases/case_form.html", context)


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
