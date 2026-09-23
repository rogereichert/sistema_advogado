from pathlib import Path

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import FileResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.cases.models import CaseHistory, LegalCase
from apps.clients.models import Client
from apps.notifications.services import (
    create_pending_document_notification,
    reopen_pending_document_notification,
    resolve_pending_document_notification,
)

from .forms import DocumentUploadForm, RequiredDocumentForm
from .models import Document, RequiredDocument


def _is_ajax(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


# ==============================================================
# LISTAGEM DE DOCUMENTOS
# ==============================================================


@login_required
def document_list(request):
    documents = (
        Document.objects
        .select_related(
            "caso",
            "caso__cliente",
            "caso__status",
            "enviado_por",
        )
        .all()
        .order_by("-criado_em")
    )

    search = request.GET.get("q", "").strip()
    client = request.GET.get("client", "").strip()
    file_type = request.GET.get("type", "").strip().lower()

    if search:
        documents = documents.filter(
            Q(nome_original__icontains=search)
            | Q(descricao__icontains=search)
            | Q(caso__titulo__icontains=search)
            | Q(caso__numero_processo__icontains=search)
            | Q(caso__cliente__nome_completo__icontains=search)
            | Q(caso__cliente__cpf__icontains=search)
        )

    if client:
        documents = documents.filter(
            caso__cliente_id=client
        )

    if file_type:
        documents = documents.filter(
            nome_original__iendswith=f".{file_type}"
        )

    clients = Client.objects.order_by(
        "nome_completo"
    )

    all_document_names = Document.objects.values_list(
        "nome_original",
        flat=True,
    )

    extensions = sorted(
        {
            Path(filename).suffix.lower().lstrip(".")
            for filename in all_document_names
            if Path(filename).suffix
        }
    )

    total_documents = documents.count()

    return render(
        request,
        "documents/document_list.html",
        {
            "documents": documents,
            "clients": clients,
            "extensions": extensions,
            "search": search,
            "selected_client": client,
            "selected_type": file_type,
            "total_documents": total_documents,
        },
    )


# ==============================================================
# UPLOAD DE DOCUMENTOS
# ==============================================================


@login_required
def document_upload(request, case_pk):
    legal_case = get_object_or_404(
        LegalCase.objects.select_related(
            "cliente",
            "status",
        ),
        pk=case_pk,
    )

    if request.method == "POST":
        form = DocumentUploadForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            arquivos = form.cleaned_data["arquivos"]
            descricao = form.cleaned_data["descricao"]

            documents_created = []

            for uploaded_file in arquivos:
                document = Document.objects.create(
                    caso=legal_case,
                    arquivo=uploaded_file,
                    nome_original=uploaded_file.name,
                    descricao=descricao,
                    enviado_por=request.user,
                )

                documents_created.append(document)

            quantidade = len(documents_created)

            if quantidade == 1:
                titulo = "Documento anexado"

                descricao_historico = (
                    f"Documento "
                    f"'{documents_created[0].nome_original}' "
                    f"foi anexado ao caso."
                )

            else:
                titulo = "Documentos anexados"

                nomes = ", ".join(
                    document.nome_original
                    for document in documents_created
                )

                descricao_historico = (
                    f"{quantidade} documentos foram anexados: "
                    f"{nomes}."
                )

            CaseHistory.objects.create(
                caso=legal_case,
                usuario=request.user,
                titulo=titulo,
                descricao=descricao_historico,
            )

            return redirect(
                "cases:detail",
                pk=legal_case.pk,
            )

    else:
        form = DocumentUploadForm()

    return render(
        request,
        "documents/document_upload.html",
        {
            "form": form,
            "case": legal_case,
        },
    )


# ==============================================================
# DOWNLOAD
# ==============================================================


@login_required
def document_download(request, pk):
    document = get_object_or_404(
        Document.objects.select_related(
            "caso",
            "caso__cliente",
        ),
        pk=pk,
    )

    return FileResponse(
        document.arquivo.open("rb"),
        as_attachment=True,
        filename=document.nome_original,
    )


# ==============================================================
# EXCLUSÃO DE DOCUMENTO
# ==============================================================


@login_required
@require_POST
def document_delete(request, pk):
    document = get_object_or_404(
        Document.objects.select_related(
            "caso",
        ),
        pk=pk,
    )

    legal_case = document.caso
    nome_original = document.nome_original

    document.arquivo.delete(
        save=False
    )

    document.delete()

    CaseHistory.objects.create(
        caso=legal_case,
        usuario=request.user,
        titulo="Documento removido",
        descricao=(
            f"O documento '{nome_original}' "
            f"foi removido do caso."
        ),
    )

    return redirect(
        "cases:detail",
        pk=legal_case.pk,
    )


# ==============================================================
# DOCUMENTAÇÃO NECESSÁRIA
# ==============================================================


@login_required
def required_document_create(request, case_pk):
    legal_case = get_object_or_404(
        LegalCase.objects.select_related(
            "cliente",
            "status",
        ),
        pk=case_pk,
    )

    if request.method == "POST":
        form = RequiredDocumentForm(
            request.POST
        )

        if form.is_valid():
            required_document = form.save(
                commit=False
            )

            required_document.caso = legal_case
            required_document.save()

            CaseHistory.objects.create(
                caso=legal_case,
                usuario=request.user,
                titulo="Documento solicitado",
                descricao=(
                    f"O documento "
                    f"'{required_document.nome}' "
                    f"foi adicionado à documentação "
                    f"necessária."
                ),
            )

            # ==================================================
            # NOTIFICAÇÃO
            # ==================================================

            create_pending_document_notification(
                required_document=required_document,
                usuario=request.user,
            )

            if _is_ajax(request):
                return JsonResponse(
                    {
                        "success": True,
                        "required_document_id": (
                            required_document.pk
                        ),
                        "message": (
                            "Documento solicitado com sucesso."
                        ),
                    }
                )

            return redirect(
                "cases:detail",
                pk=legal_case.pk,
            )

    else:
        form = RequiredDocumentForm()

    context = {
        "form": form,
        "case": legal_case,
    }

    if _is_ajax(request):
        return render(
            request,
            "documents/_required_document_form_content.html",
            context,
            status=(
                400
                if request.method == "POST"
                else 200
            ),
        )

    return render(
        request,
        "documents/required_document_form.html",
        context,
    )


# ==============================================================
# ALTERAR STATUS DO DOCUMENTO NECESSÁRIO
# ==============================================================


@login_required
@require_POST
def required_document_toggle(request, pk):
    required_document = get_object_or_404(
        RequiredDocument.objects.select_related(
            "caso",
            "caso__cliente",
        ),
        pk=pk,
    )

    if required_document.recebido:
        # ======================================================
        # RECEBIDO -> PENDENTE
        # ======================================================

        required_document.recebido = False
        required_document.recebido_em = None

        titulo = "Documento marcado como pendente"

        descricao = (
            f"O documento "
            f"'{required_document.nome}' "
            f"foi marcado novamente como pendente."
        )

    else:
        # ======================================================
        # PENDENTE -> RECEBIDO
        # ======================================================

        required_document.recebido = True
        required_document.recebido_em = timezone.now()

        titulo = "Documento recebido"

        descricao = (
            f"O documento "
            f"'{required_document.nome}' "
            f"foi marcado como recebido."
        )

    required_document.save(
        update_fields=[
            "recebido",
            "recebido_em",
        ]
    )

    CaseHistory.objects.create(
        caso=required_document.caso,
        usuario=request.user,
        titulo=titulo,
        descricao=descricao,
    )

    # ==========================================================
    # SINCRONIZAÇÃO DA NOTIFICAÇÃO
    # ==========================================================

    if required_document.recebido:
        resolve_pending_document_notification(
            required_document=required_document,
        )

    else:
        reopen_pending_document_notification(
            required_document=required_document,
            usuario=request.user,
        )

    return redirect(
        "cases:detail",
        pk=required_document.caso.pk,
    )


# ==============================================================
# REMOVER DOCUMENTO NECESSÁRIO
# ==============================================================


@login_required
@require_POST
def required_document_delete(request, pk):
    required_document = get_object_or_404(
        RequiredDocument.objects.select_related(
            "caso",
        ),
        pk=pk,
    )

    legal_case = required_document.caso
    nome = required_document.nome

    # ==========================================================
    # REMOVE A NOTIFICAÇÃO ANTES DO OBJETO SER EXCLUÍDO
    # ==========================================================

    resolve_pending_document_notification(
        required_document=required_document,
    )

    required_document.delete()

    CaseHistory.objects.create(
        caso=legal_case,
        usuario=request.user,
        titulo="Documento removido do checklist",
        descricao=(
            f"O documento '{nome}' foi removido "
            f"da documentação necessária."
        ),
    )

    return redirect(
        "cases:detail",
        pk=legal_case.pk,
    )