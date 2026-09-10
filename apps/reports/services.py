from apps.clients.models import Client


class ClientDossierService:

    def __init__(self, client):
        self.client = client

    def get_cases(self, case_ids=None):
        cases = (
            self.client.casos
            .select_related("status")
            .prefetch_related(
                "historico",
                "movimentacoes",
                "documentos",
                "documentos_necessarios",
                "eventos",
            )
        )

        if case_ids:
            cases = cases.filter(
                pk__in=case_ids
            )

        return cases.all()

    def get_data(
        self,
        case_ids=None,
        sections=None,
        dossier_type="complete",
    ):
        cases = self.get_cases(
            case_ids=case_ids,
        )

        return {
            "client": self.client,
            "cases": cases,
            "options": {
                "case_ids": case_ids or [],
                "sections": sections or [],
                "dossier_type": dossier_type,
            },
        }