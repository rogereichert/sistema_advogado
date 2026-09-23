from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from apps.clients.models import Client

from .pdf import ClientDossierPDF
from .services import ClientDossierService


# ==============================================================
# SEÇÕES PERMITIDAS NO DOSSIÊ
# ==============================================================

ALLOWED_SECTIONS = {
    "client",
    "cases",
    "history",
    "movements",
    "documents",
    "agenda",
    "internal_notes",
}


# ==============================================================
# SEÇÕES QUE DEPENDEM DE PELO MENOS UM CASO
# ==============================================================

CASE_DEPENDENT_SECTIONS = {
    "cases",
    "history",
    "movements",
    "documents",
    "agenda",
    "internal_notes",
}


@login_required
def client_dossier(request, client_pk):
    """
    Gera o dossiê PDF de um cliente.

    O conteúdo do documento é determinado exclusivamente por:
        - casos selecionados;
        - seções selecionadas.

    Não existe mais "tipo de dossiê".

    Um dossiê pode ser gerado sem casos quando somente seções
    independentes de casos forem selecionadas, como os dados
    cadastrais do cliente.
    """

    client = get_object_or_404(
        Client,
        pk=client_pk,
    )

    # ==========================================================
    # VALORES PADRÃO
    # ==========================================================

    selected_case_ids = list(
        client.casos.values_list(
            "pk",
            flat=True,
        )
    )

    selected_sections = list(
        ALLOWED_SECTIONS
    )

    # ==========================================================
    # POST — ESCOLHAS DO USUÁRIO
    # ==========================================================

    if request.method == "POST":
        selected_case_ids = request.POST.getlist(
            "cases"
        )

        selected_sections = request.POST.getlist(
            "sections"
        )

        # ------------------------------------------------------
        # VALIDAÇÃO DAS SEÇÕES
        # ------------------------------------------------------

        invalid_sections = (
            set(selected_sections)
            - ALLOWED_SECTIONS
        )

        if invalid_sections:
            return HttpResponse(
                "Uma ou mais seções selecionadas são inválidas.",
                status=400,
            )

        if not selected_sections:
            return HttpResponse(
                "Selecione pelo menos uma seção para gerar o dossiê.",
                status=400,
            )

        # ------------------------------------------------------
        # CASOS QUE REALMENTE PERTENCEM AO CLIENTE
        # ------------------------------------------------------

        client_case_ids = set(
            client.casos.values_list(
                "pk",
                flat=True,
            )
        )

        valid_case_ids = []

        for case_id in selected_case_ids:
            try:
                case_id = int(
                    case_id
                )
            except (TypeError, ValueError):
                continue

            if case_id in client_case_ids:
                valid_case_ids.append(
                    case_id
                )

        selected_case_ids = valid_case_ids

        # ------------------------------------------------------
        # VALIDAÇÃO DAS SEÇÕES DEPENDENTES DE CASOS
        # ------------------------------------------------------

        selected_case_dependent_sections = (
            set(selected_sections)
            & CASE_DEPENDENT_SECTIONS
        )

        if (
            selected_case_dependent_sections
            and not selected_case_ids
        ):
            return HttpResponse(
                (
                    "Selecione pelo menos um caso para incluir "
                    "as informações jurídicas escolhidas no dossiê."
                ),
                status=400,
            )

    # ==========================================================
    # SERVIÇO
    # ==========================================================

    service = ClientDossierService(
        client
    )

    data = service.get_data(
        case_ids=selected_case_ids,
        sections=selected_sections,
    )

    # ==========================================================
    # PDF
    # ==========================================================

    pdf = ClientDossierPDF(
        data
    )

    pdf_content = pdf.build()

    response = HttpResponse(
        pdf_content,
        content_type="application/pdf",
    )

    response["Content-Disposition"] = (
        f'inline; filename="dossie-{client.pk}.pdf"'
    )

    return response