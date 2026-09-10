from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from apps.clients.models import Client

from .pdf import ClientDossierPDF
from .services import ClientDossierService


ALLOWED_DOSSIER_TYPES = {
    "complete",
    "client",
    "summary",
}


ALLOWED_SECTIONS = {
    "client",
    "cases",
    "history",
    "movements",
    "documents",
    "agenda",
}


@login_required
def client_dossier(request, client_pk):
    client = get_object_or_404(
        Client,
        pk=client_pk,
    )

    dossier_type = "complete"
    selected_case_ids = []
    selected_sections = list(ALLOWED_SECTIONS)

    if request.method == "POST":
        dossier_type = request.POST.get(
            "dossier_type",
            "complete",
        )

        selected_case_ids = request.POST.getlist(
            "cases"
        )

        selected_sections = request.POST.getlist(
            "sections"
        )

        if dossier_type not in ALLOWED_DOSSIER_TYPES:
            return HttpResponse(
                "Tipo de dossiê inválido.",
                status=400,
            )

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

        client_case_ids = set(
            client.casos.values_list(
                "pk",
                flat=True,
            )
        )

        valid_case_ids = []

        for case_id in selected_case_ids:
            if not case_id.isdigit():
                continue

            case_id = int(case_id)

            if case_id in client_case_ids:
                valid_case_ids.append(case_id)

        selected_case_ids = valid_case_ids

        if not selected_case_ids:
            return HttpResponse(
                "Selecione pelo menos um caso para gerar o dossiê.",
                status=400,
            )

    else:
        selected_case_ids = list(
            client.casos.values_list(
                "pk",
                flat=True,
            )
        )

    service = ClientDossierService(
        client
    )

    data = service.get_data(
        case_ids=selected_case_ids,
        sections=selected_sections,
        dossier_type=dossier_type,
    )

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