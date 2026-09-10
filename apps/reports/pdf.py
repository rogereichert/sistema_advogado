from io import BytesIO
from html import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


PAGE_WIDTH, PAGE_HEIGHT = A4


class ClientDossierPDF:

    def __init__(self, data):
        self.data = data
        self.client = data["client"]
        self.cases = data["cases"]

        self.buffer = BytesIO()

        self.styles = getSampleStyleSheet()
        self._configure_styles()

    def _configure_styles(self):
        self.title_style = ParagraphStyle(
            "DossierTitle",
            parent=self.styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=12,
        )

        self.subtitle_style = ParagraphStyle(
            "DossierSubtitle",
            parent=self.styles["Normal"],
            fontName="Helvetica",
            fontSize=11,
            leading=16,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#64748b"),
        )

        self.section_style = ParagraphStyle(
            "SectionTitle",
            parent=self.styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=20,
            textColor=colors.HexColor("#0f172a"),
            spaceBefore=8,
            spaceAfter=10,
        )

        self.subsection_style = ParagraphStyle(
            "SubsectionTitle",
            parent=self.styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=15,
            textColor=colors.HexColor("#334155"),
            spaceBefore=8,
            spaceAfter=6,
        )

        self.body_style = ParagraphStyle(
            "Body",
            parent=self.styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor("#334155"),
            spaceAfter=6,
        )

        self.small_style = ParagraphStyle(
            "Small",
            parent=self.styles["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#64748b"),
        )

        self.table_header_style = ParagraphStyle(
            "TableHeader",
            parent=self.styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.white,
        )

        self.table_body_style = ParagraphStyle(
            "TableBody",
            parent=self.styles["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#334155"),
        )

    def _footer(self, canvas, document):
        canvas.saveState()

        canvas.setStrokeColor(
            colors.HexColor("#e2e8f0")
        )

        canvas.line(
            18 * mm,
            15 * mm,
            PAGE_WIDTH - 18 * mm,
            15 * mm,
        )

        canvas.setFont(
            "Helvetica",
            7.5,
        )

        canvas.setFillColor(
            colors.HexColor("#64748b")
        )

        canvas.drawString(
            18 * mm,
            9 * mm,
            "Documento gerado pelo escritório",
        )

        canvas.drawRightString(
            PAGE_WIDTH - 18 * mm,
            9 * mm,
            f"Página {document.page}",
        )

        canvas.restoreState()

    def _escape_text(self, value):
        if value is None:
            return ""

        value = str(value)

        return escape(
            value
        ).replace(
            "\n",
            "<br/>",
        )

    def _paragraph(
        self,
        value,
        style=None,
    ):
        if style is None:
            style = self.body_style

        text = self._escape_text(
            value
        )

        return Paragraph(
            text,
            style,
        )

    def _dossier_type_label(
        self,
        dossier_type,
    ):
        labels = {
            "complete": "Dossiê completo",
            "client": "Relatório para cliente",
            "summary": "Resumo do caso",
        }

        return labels.get(
            dossier_type,
            "Dossiê jurídico",
        )

    def _add_cover(
        self,
        story,
        dossier_type="complete",
    ):
        story.append(
            Spacer(
                1,
                42 * mm,
            )
        )

        story.append(
            Paragraph(
                "DOSSIÊ JURÍDICO",
                self.title_style,
            )
        )

        story.append(
            Paragraph(
                self._dossier_type_label(
                    dossier_type
                ),
                self.subtitle_style,
            )
        )

        story.append(
            Spacer(
                1,
                25 * mm,
            )
        )

        client_box = Table(
            [
                [
                    Paragraph(
                        "CLIENTE",
                        self.table_header_style,
                    )
                ],
                [
                    Paragraph(
                        self._escape_text(
                            self.client.nome_completo
                        ),
                        ParagraphStyle(
                            "ClientName",
                            parent=self.body_style,
                            fontName="Helvetica-Bold",
                            fontSize=14,
                            leading=18,
                            alignment=TA_CENTER,
                            textColor=colors.HexColor(
                                "#0f172a"
                            ),
                        ),
                    )
                ],
            ],
            colWidths=[
                150 * mm
            ],
        )

        client_box.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor(
                            "#b45309"
                        ),
                    ),
                    (
                        "BACKGROUND",
                        (0, 1),
                        (-1, 1),
                        colors.HexColor(
                            "#f8fafc"
                        ),
                    ),
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.8,
                        colors.HexColor(
                            "#cbd5e1"
                        ),
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        12,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        12,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        10,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        10,
                    ),
                ]
            )
        )

        story.append(
            client_box
        )

        story.append(
            Spacer(
                1,
                18 * mm,
            )
        )

        story.append(
            Paragraph(
                f"Quantidade de casos: {self.cases.count()}",
                self.subtitle_style,
            )
        )

        story.append(
            Spacer(
                1,
                6 * mm,
            )
        )

        story.append(
            Paragraph(
                "Documento elaborado a partir das informações "
                "cadastradas no sistema do escritório.",
                self.small_style,
            )
        )

        story.append(
            PageBreak()
        )

    def _add_client_section(
        self,
        story,
    ):
        story.append(
            Paragraph(
                "1. Dados do cliente",
                self.section_style,
            )
        )

        rows = [
            [
                "Nome completo",
                self.client.nome_completo,
            ],
            [
                "CPF",
                self.client.cpf
                or "Não informado",
            ],
            [
                "RG",
                self.client.rg
                or "Não informado",
            ],
            [
                "Carteira de trabalho",
                self.client.carteira_trabalho
                or "Não informado",
            ],
            [
                "Título de eleitor",
                self.client.titulo_eleitor
                or "Não informado",
            ],
            [
                "Estado civil",
                self.client.estado_civil
                or "Não informado",
            ],
            [
                "Telefone",
                self.client.telefone
                or "Não informado",
            ],
            [
                "E-mail",
                self.client.email
                or "Não informado",
            ],
        ]

        table = self._two_column_table(
            rows
        )

        if table:
            story.append(
                table
            )

        story.append(
            Spacer(
                1,
                8,
            )
        )

        story.append(
            Paragraph(
                "Endereço",
                self.subsection_style,
            )
        )

        address = self._client_address()

        story.append(
            self._paragraph(
                address,
                self.body_style,
            )
        )

    def _client_address(self):
        parts = [
            self.client.logradouro,
            self.client.numero,
            self.client.complemento,
            self.client.bairro,
            self.client.cidade,
            self.client.uf,
            self.client.cep,
        ]

        parts = [
            str(part)
            for part in parts
            if part
        ]

        return (
            ", ".join(parts)
            if parts
            else "Endereço não informado."
        )

    def _add_cases_section(
        self,
        story,
    ):
        story.append(
            Paragraph(
                "2. Casos e processos",
                self.section_style,
            )
        )

        if not self.cases.exists():
            story.append(
                Paragraph(
                    "Nenhum caso selecionado.",
                    self.small_style,
                )
            )

            return

        for index, case in enumerate(
            self.cases,
            start=1,
        ):
            story.append(
                Paragraph(
                    self._escape_text(
                        f"{index}. {case.titulo}"
                    ),
                    self.subsection_style,
                )
            )

            rows = [
                [
                    "Status",
                    case.status.nome,
                ],
                [
                    "Área jurídica",
                    case.area_juridica
                    or "Não informado",
                ],
                [
                    "Número do processo",
                    case.numero_processo
                    or "Não informado",
                ],
                [
                    "Vara",
                    case.vara
                    or "Não informado",
                ],
                [
                    "Comarca",
                    case.comarca
                    or "Não informado",
                ],
                [
                    "Data de abertura",
                    (
                        case.data_abertura.strftime(
                            "%d/%m/%Y"
                        )
                        if case.data_abertura
                        else "Não informado"
                    ),
                ],
                [
                    "Data de encerramento",
                    (
                        case.data_encerramento.strftime(
                            "%d/%m/%Y"
                        )
                        if case.data_encerramento
                        else "Em andamento"
                    ),
                ],
            ]

            table = self._two_column_table(
                rows
            )

            if table:
                story.append(
                    table
                )

            if case.descricao:
                story.append(
                    Spacer(
                        1,
                        5,
                    )
                )

                story.append(
                    Paragraph(
                        "<b>Descrição</b>",
                        self.subsection_style,
                    )
                )

                story.append(
                    self._paragraph(
                        case.descricao,
                        self.body_style,
                    )
                )

            options = self.data.get(
                "options",
                {},
            )

            dossier_type = options.get(
                "dossier_type",
                "complete",
            )

            if (
                dossier_type != "client"
                and case.observacoes
            ):
                story.append(
                    Paragraph(
                        "<b>Observações internas</b>",
                        self.subsection_style,
                    )
                )

                story.append(
                    self._paragraph(
                        case.observacoes,
                        self.body_style,
                    )
                )

            if (
                index < self.cases.count()
            ):
                story.append(
                    Spacer(
                        1,
                        8,
                    )
                )

    def _add_history_section(
        self,
        story,
    ):
        story.append(
            Paragraph(
                "3. Histórico",
                self.section_style,
            )
        )

        has_history = False

        for case in self.cases:
            history = case.historico.all()

            if not history:
                continue

            has_history = True

            story.append(
                Paragraph(
                    self._escape_text(
                        case.titulo
                    ),
                    self.subsection_style,
                )
            )

            rows = [
                [
                    Paragraph(
                        "Data",
                        self.table_header_style,
                    ),
                    Paragraph(
                        "Título",
                        self.table_header_style,
                    ),
                    Paragraph(
                        "Descrição",
                        self.table_header_style,
                    ),
                ]
            ]

            for item in history:
                rows.append(
                    [
                        self._paragraph(
                            item.criado_em.strftime(
                                "%d/%m/%Y %H:%M"
                            ),
                            self.table_body_style,
                        ),
                        self._paragraph(
                            item.titulo or "-",
                            self.table_body_style,
                        ),
                        self._paragraph(
                            item.descricao or "-",
                            self.table_body_style,
                        ),
                    ]
                )

            story.append(
                self._data_table(
                    rows,
                    widths=[
                        30 * mm,
                        45 * mm,
                        75 * mm,
                    ],
                )
            )

            story.append(
                Spacer(
                    1,
                    7,
                )
            )

        if not has_history:
            story.append(
                Paragraph(
                    "Nenhum histórico cadastrado "
                    "para os casos selecionados.",
                    self.small_style,
                )
            )

    def _add_movements_section(
        self,
        story,
    ):
        story.append(
            Paragraph(
                "4. Movimentações",
                self.section_style,
            )
        )

        has_movements = False

        for case in self.cases:
            movements = case.movimentacoes.all()

            if not movements:
                continue

            has_movements = True

            story.append(
                Paragraph(
                    self._escape_text(
                        case.titulo
                    ),
                    self.subsection_style,
                )
            )

            rows = [
                [
                    Paragraph(
                        "Data",
                        self.table_header_style,
                    ),
                    Paragraph(
                        "Título",
                        self.table_header_style,
                    ),
                    Paragraph(
                        "Descrição",
                        self.table_header_style,
                    ),
                ]
            ]

            for item in movements:
                rows.append(
                    [
                        self._paragraph(
                            item.criado_em.strftime(
                                "%d/%m/%Y %H:%M"
                            ),
                            self.table_body_style,
                        ),
                        self._paragraph(
                            item.titulo or "-",
                            self.table_body_style,
                        ),
                        self._paragraph(
                            item.descricao or "-",
                            self.table_body_style,
                        ),
                    ]
                )

            story.append(
                self._data_table(
                    rows,
                    widths=[
                        30 * mm,
                        45 * mm,
                        75 * mm,
                    ],
                )
            )

            story.append(
                Spacer(
                    1,
                    7,
                )
            )

        if not has_movements:
            story.append(
                Paragraph(
                    "Nenhuma movimentação cadastrada "
                    "para os casos selecionados.",
                    self.small_style,
                )
            )

    def _add_documents_section(
        self,
        story,
    ):
        story.append(
            Paragraph(
                "5. Documentação",
                self.section_style,
            )
        )

        for case in self.cases:
            documents = case.documentos.all()
            required = case.documentos_necessarios.all()

            story.append(
                Paragraph(
                    self._escape_text(
                        case.titulo
                    ),
                    self.subsection_style,
                )
            )

            if required:
                rows = [
                    [
                        Paragraph(
                            "Documento necessário",
                            self.table_header_style,
                        ),
                        Paragraph(
                            "Situação",
                            self.table_header_style,
                        ),
                    ]
                ]

                for item in required:
                    status = (
                        "Recebido"
                        if item.recebido
                        else "Pendente"
                    )

                    rows.append(
                        [
                            self._paragraph(
                                item.nome,
                                self.table_body_style,
                            ),
                            self._paragraph(
                                status,
                                self.table_body_style,
                            ),
                        ]
                    )

                story.append(
                    self._data_table(
                        rows,
                        widths=[
                            110 * mm,
                            40 * mm,
                        ],
                    )
                )

            story.append(
                Spacer(
                    1,
                    5,
                )
            )

            if documents:
                story.append(
                    Paragraph(
                        "Documentos cadastrados",
                        self.subsection_style,
                    )
                )

                for document in documents:
                    story.append(
                        self._paragraph(
                            f"• {document.nome_original}",
                            self.body_style,
                        )
                    )
            else:
                story.append(
                    Paragraph(
                        "Nenhum documento cadastrado.",
                        self.small_style,
                    )
                )

    def _add_agenda_section(
        self,
        story,
    ):
        story.append(
            Paragraph(
                "6. Agenda",
                self.section_style,
            )
        )

        has_events = False

        for case in self.cases:
            events = case.eventos.all()

            if not events:
                continue

            has_events = True

            story.append(
                Paragraph(
                    self._escape_text(
                        case.titulo
                    ),
                    self.subsection_style,
                )
            )

            rows = [
                [
                    Paragraph(
                        "Data",
                        self.table_header_style,
                    ),
                    Paragraph(
                        "Tipo",
                        self.table_header_style,
                    ),
                    Paragraph(
                        "Título",
                        self.table_header_style,
                    ),
                    Paragraph(
                        "Local",
                        self.table_header_style,
                    ),
                ]
            ]

            for event in events:
                event_date = event.data.strftime(
                    "%d/%m/%Y"
                )

                if event.hora:
                    event_date += (
                        f" {event.hora.strftime('%H:%M')}"
                    )

                rows.append(
                    [
                        self._paragraph(
                            event_date,
                            self.table_body_style,
                        ),
                        self._paragraph(
                            event.get_tipo_display(),
                            self.table_body_style,
                        ),
                        self._paragraph(
                            event.titulo,
                            self.table_body_style,
                        ),
                        self._paragraph(
                            event.local or "-",
                            self.table_body_style,
                        ),
                    ]
                )

            story.append(
                self._data_table(
                    rows,
                    widths=[
                        32 * mm,
                        30 * mm,
                        55 * mm,
                        33 * mm,
                    ],
                )
            )

            story.append(
                Spacer(
                    1,
                    7,
                )
            )

        if not has_events:
            story.append(
                Paragraph(
                    "Nenhum evento de agenda cadastrado "
                    "para os casos selecionados.",
                    self.small_style,
                )
            )

    def _two_column_table(
        self,
        rows,
    ):
        formatted_rows = []

        for row in rows:
            if not row or len(row) != 2:
                continue

            label, value = row

            formatted_rows.append(
                [
                    self._paragraph(
                        label,
                        ParagraphStyle(
                            "Label",
                            parent=self.table_body_style,
                            fontName="Helvetica-Bold",
                        ),
                    ),
                    self._paragraph(
                        value,
                        self.table_body_style,
                    ),
                ]
            )

        if not formatted_rows:
            return None

        return self._data_table(
            formatted_rows,
            widths=[
                50 * mm,
                100 * mm,
            ],
            header=False,
        )

    def _data_table(
        self,
        rows,
        widths,
        header=True,
    ):
        if not rows:
            return None

        table = Table(
            rows,
            colWidths=widths,
            repeatRows=1 if (
                header and len(rows) > 1
            ) else 0,
            hAlign="LEFT",
        )

        style_commands = [
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.35,
                colors.HexColor(
                    "#cbd5e1"
                ),
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP",
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                7,
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                7,
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                6,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                6,
            ),
        ]

        if header:
            style_commands.append(
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor(
                        "#334155"
                    ),
                )
            )

        else:
            style_commands.extend(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (0, -1),
                        colors.HexColor(
                            "#f8fafc"
                        ),
                    ),
                    (
                        "BACKGROUND",
                        (1, 0),
                        (-1, -1),
                        colors.white,
                    ),
                ]
            )

        table.setStyle(
            TableStyle(
                style_commands
            )
        )

        return table

    def _add_summary_intro(
        self,
        story,
    ):
        story.append(
            Paragraph(
                "Resumo executivo",
                self.subsection_style,
            )
        )

        total_cases = self.cases.count()

        story.append(
            self._paragraph(
                (
                    f"Este documento apresenta um resumo "
                    f"objetivo das informações cadastradas "
                    f"para o cliente, contemplando "
                    f"{total_cases} caso(s) selecionado(s)."
                ),
                self.body_style,
            )
        )

    def build(self):
        document = SimpleDocTemplate(
            self.buffer,
            pagesize=A4,
            rightMargin=18 * mm,
            leftMargin=18 * mm,
            topMargin=18 * mm,
            bottomMargin=22 * mm,
            title=(
                f"Dossiê - "
                f"{self.client.nome_completo}"
            ),
            author="Escritório",
        )

        story = []

        options = self.data.get(
            "options",
            {},
        )

        dossier_type = options.get(
            "dossier_type",
            "complete",
        )

        sections = set(
            options.get(
                "sections",
                [],
            )
        )

        # ---------------------------------------------------------
        # CAPA
        # ---------------------------------------------------------

        self._add_cover(
            story,
            dossier_type=dossier_type,
        )

        # ---------------------------------------------------------
        # RESUMO
        # ---------------------------------------------------------

        if dossier_type == "summary":
            self._add_summary_intro(
                story
            )

        # ---------------------------------------------------------
        # DADOS DO CLIENTE
        # ---------------------------------------------------------

        if "client" in sections:
            self._add_client_section(
                story
            )

        # ---------------------------------------------------------
        # PROCESSOS / CASOS
        # ---------------------------------------------------------

        if "cases" in sections:
            self._add_cases_section(
                story
            )

        # ---------------------------------------------------------
        # HISTÓRICO
        # ---------------------------------------------------------

        if "history" in sections:
            self._add_history_section(
                story
            )

        # ---------------------------------------------------------
        # MOVIMENTAÇÕES
        # ---------------------------------------------------------

        if "movements" in sections:
            self._add_movements_section(
                story
            )

        # ---------------------------------------------------------
        # DOCUMENTAÇÃO
        # ---------------------------------------------------------

        if "documents" in sections:
            self._add_documents_section(
                story
            )

        # ---------------------------------------------------------
        # AGENDA
        # ---------------------------------------------------------

        if "agenda" in sections:
            self._add_agenda_section(
                story
            )

        # ---------------------------------------------------------
        # GERAÇÃO DO PDF
        # ---------------------------------------------------------

        document.build(
            story,
            onFirstPage=self._footer,
            onLaterPages=self._footer,
        )

        self.buffer.seek(0)

        return self.buffer.getvalue()