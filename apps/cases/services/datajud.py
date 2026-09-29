"""
Serviço de integração com a API Pública do DataJud/CNJ.

Responsabilidades:
- normalizar número processual CNJ;
- interpretar a estrutura do número CNJ;
- identificar o tribunal/endpoint quando suportado;
- consultar a API Pública do DataJud;
- tratar falhas de comunicação de forma controlada;
- devolver resultado estruturado.

Este serviço não salva dados no banco de dados.
"""

import re

import requests
from django.conf import settings


DATAJUD_BASE_URL = "https://api-publica.datajud.cnj.jus.br"
REQUEST_TIMEOUT = 30


class DataJudError(Exception):
    """Erro base da integração com o DataJud."""

    codigo = "ERRO_DATAJUD"

    def __init__(
        self,
        mensagem,
        *,
        status_code=None,
        retry_after=None,
    ):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status_code = status_code
        self.retry_after = retry_after

    def __str__(self):
        return self.mensagem


class DataJudConfigurationError(DataJudError):
    """Configuração/autenticação necessária está ausente ou inválida."""

    codigo = "ERRO_CONFIGURACAO"


class DataJudRateLimitError(DataJudError):
    """O DataJud limitou temporariamente novas consultas."""

    codigo = "LIMITE_CONSULTAS"


class DataJudUnavailableError(DataJudError):
    """O serviço externo está temporariamente indisponível."""

    codigo = "SERVICO_INDISPONIVEL"


class DataJudTimeoutError(DataJudError):
    """A consulta excedeu o tempo limite."""

    codigo = "TIMEOUT"


class DataJudConnectionError(DataJudError):
    """Não foi possível estabelecer comunicação com o DataJud."""

    codigo = "ERRO_CONEXAO"


class DataJudInvalidResponseError(DataJudError):
    """O DataJud respondeu em formato inesperado."""

    codigo = "RESPOSTA_INVALIDA"


class DataJudTribunalNaoSuportadoError(DataJudError):
    """O tribunal identificado ainda não possui roteamento implementado."""

    codigo = "TRIBUNAL_NAO_SUPORTADO"


def normalizar_numero_processo(numero_processo):
    """
    Remove máscara e qualquer caractere não numérico.

    Exemplo:
        0000832-35.2018.4.01.3202
        ->
        00008323520184013202
    """
    return re.sub(r"\D", "", str(numero_processo or ""))


def interpretar_numero_cnj(numero_processo):
    """
    Interpreta os campos estruturais de um número CNJ.

    Estrutura:
        NNNNNNN-DD.AAAA.J.TR.OOOO
    """
    numero = normalizar_numero_processo(numero_processo)

    if len(numero) != 20:
        return None

    return {
        "numero": numero,
        "sequencial": numero[0:7],
        "digito_verificador": numero[7:9],
        "ano": numero[9:13],
        "segmento": numero[13],
        "tribunal": numero[14:16],
        "origem": numero[16:20],
    }

TRIBUNAIS_ESTADUAIS = {
    "01": ("TJAC", "tjac", "Acre"),
    "02": ("TJAL", "tjal", "Alagoas"),
    "03": ("TJAP", "tjap", "Amapá"),
    "04": ("TJAM", "tjam", "Amazonas"),
    "05": ("TJBA", "tjba", "Bahia"),
    "06": ("TJCE", "tjce", "Ceará"),
    "07": ("TJDFT", "tjdft", "Distrito Federal e Territórios"),
    "08": ("TJES", "tjes", "Espírito Santo"),
    "09": ("TJGO", "tjgo", "Goiás"),
    "10": ("TJMA", "tjma", "Maranhão"),
    "11": ("TJMT", "tjmt", "Mato Grosso"),
    "12": ("TJMS", "tjms", "Mato Grosso do Sul"),
    "13": ("TJMG", "tjmg", "Minas Gerais"),
    "14": ("TJPA", "tjpa", "Pará"),
    "15": ("TJPB", "tjpb", "Paraíba"),
    "16": ("TJPR", "tjpr", "Paraná"),
    "17": ("TJPE", "tjpe", "Pernambuco"),
    "18": ("TJPI", "tjpi", "Piauí"),
    "19": ("TJRJ", "tjrj", "Rio de Janeiro"),
    "20": ("TJRN", "tjrn", "Rio Grande do Norte"),
    "21": ("TJRS", "tjrs", "Rio Grande do Sul"),
    "22": ("TJRO", "tjro", "Rondônia"),
    "23": ("TJRR", "tjrr", "Roraima"),
    "24": ("TJSC", "tjsc", "Santa Catarina"),
    "25": ("TJSE", "tjse", "Sergipe"),
    "26": ("TJSP", "tjsp", "São Paulo"),
    "27": ("TJTO", "tjto", "Tocantins"),
}


def identificar_tribunal(numero_processo):
    """
    Identifica o tribunal e o endpoint do DataJud a partir do número CNJ.

    Segmentos implementados:
    - Justiça Federal (J = 4)
    - Justiça do Trabalho (J = 5)
    - Justiça Estadual e Distrito Federal (J = 8)
    """
    partes = interpretar_numero_cnj(numero_processo)

    if not partes:
        return None

    segmento = partes["segmento"]
    codigo_tribunal = partes["tribunal"]

    # Justiça Federal
    if segmento == "4":
        try:
            regiao = int(codigo_tribunal)
        except ValueError:
            regiao = 0

        if 1 <= regiao <= 6:
            alias = f"trf{regiao}"

            return {
                "segmento_codigo": segmento,
                "segmento_nome": "Justiça Federal",
                "tribunal_codigo": codigo_tribunal,
                "tribunal_nome": f"TRF{regiao}",
                "alias": alias,
                "endpoint": (
                    f"{DATAJUD_BASE_URL}/"
                    f"api_publica_{alias}/_search"
                ),
            }

    # Justiça do Trabalho
    if segmento == "5":
        try:
            regiao = int(codigo_tribunal)
        except ValueError:
            regiao = 0

        if 1 <= regiao <= 24:
            alias = f"trt{regiao}"

            return {
                "segmento_codigo": segmento,
                "segmento_nome": "Justiça do Trabalho",
                "tribunal_codigo": codigo_tribunal,
                "tribunal_nome": f"TRT{regiao}",
                "alias": alias,
                "endpoint": (
                    f"{DATAJUD_BASE_URL}/"
                    f"api_publica_{alias}/_search"
                ),
            }

    # Justiça Estadual e Distrito Federal
    if segmento == "8":
        tribunal_estadual = TRIBUNAIS_ESTADUAIS.get(codigo_tribunal)

        if tribunal_estadual:
            sigla, alias, unidade_federativa = tribunal_estadual

            return {
                "segmento_codigo": segmento,
                "segmento_nome": "Justiça Estadual",
                "tribunal_codigo": codigo_tribunal,
                "tribunal_nome": sigla,
                "unidade_federativa": unidade_federativa,
                "alias": alias,
                "endpoint": (
                    f"{DATAJUD_BASE_URL}/"
                    f"api_publica_{alias}/_search"
                ),
            }

    raise DataJudTribunalNaoSuportadoError(
        "O tribunal identificado pelo número CNJ ainda não "
        "possui roteamento implementado no LexControl."
    )


def _obter_api_key():
    """
    Obtém e valida a configuração básica da chave pública do DataJud.
    """
    api_key = getattr(settings, "DATAJUD_API_KEY", None)

    if not api_key:
        raise DataJudConfigurationError(
            "A chave de acesso ao DataJud não está configurada."
        )

    api_key = str(api_key).strip()

    if not api_key:
        raise DataJudConfigurationError(
            "A chave de acesso ao DataJud não está configurada."
        )

    return api_key


def _tratar_resposta_http(response):
    """
    Converte respostas HTTP de erro em exceções específicas do domínio.

    Nenhuma tentativa automática é feita aqui.
    """
    status_code = response.status_code

    if 200 <= status_code < 300:
        return

    if status_code in (401, 403):
        raise DataJudConfigurationError(
            "O DataJud recusou a autenticação da aplicação.",
            status_code=status_code,
        )

    if status_code == 429:
        retry_after = response.headers.get("Retry-After")

        raise DataJudRateLimitError(
            (
                "O limite temporário de consultas ao DataJud "
                "foi atingido. Aguarde alguns instantes e tente novamente."
            ),
            status_code=status_code,
            retry_after=retry_after,
        )

    if 500 <= status_code <= 599:
        raise DataJudUnavailableError(
            (
                "O DataJud está temporariamente indisponível. "
                "Tente novamente mais tarde."
            ),
            status_code=status_code,
        )

    raise DataJudUnavailableError(
        f"O DataJud não conseguiu concluir a consulta (HTTP {status_code}).",
        status_code=status_code,
    )

def mapear_dados_processo(dados):
    """
    Converte a resposta bruta de um processo no DataJud
    para uma estrutura padronizada utilizada pelo LexControl.

    Nenhum dado é salvo no banco nesta etapa.
    """
    if not isinstance(dados, dict):
        return None

    classe = dados.get("classe") or {}
    sistema = dados.get("sistema") or {}
    orgao_julgador = dados.get("orgaoJulgador") or {}

    assuntos_brutos = dados.get("assuntos") or []
    movimentos_brutos = dados.get("movimentos") or []

    assuntos = []

    for assunto in assuntos_brutos:
        if not isinstance(assunto, dict):
            continue

        assuntos.append(
            {
                "codigo": assunto.get("codigo"),
                "nome": assunto.get("nome"),
            }
        )

    movimentos = []

    for movimento in movimentos_brutos:
        if not isinstance(movimento, dict):
            continue

        movimentos.append(
            {
                "codigo": movimento.get("codigo"),
                "nome": movimento.get("nome"),
                "data_hora": movimento.get("dataHora"),
            }
        )

    # O DataJud pode retornar muitos movimentos.
    # Não presumimos que a ordem recebida seja cronológica.
    movimentos_com_data = [
        movimento
        for movimento in movimentos
        if movimento.get("data_hora")
    ]

    ultimo_movimento = None

    if movimentos_com_data:
        ultimo_movimento = max(
            movimentos_com_data,
            key=lambda movimento: movimento["data_hora"],
        )

    return {
        "numero_processo": dados.get("numeroProcesso"),
        "tribunal": dados.get("tribunal"),
        "grau": dados.get("grau"),
        "data_ajuizamento": dados.get("dataAjuizamento"),

        "classe": {
            "codigo": classe.get("codigo"),
            "nome": classe.get("nome"),
        },

        "sistema": {
            "codigo": sistema.get("codigo"),
            "nome": sistema.get("nome"),
        },

        "orgao_julgador": {
            "codigo": orgao_julgador.get("codigo"),
            "nome": orgao_julgador.get("nome"),
        },

        "assuntos": assuntos,

        "ultimo_movimento": ultimo_movimento,

        "quantidade_movimentos": len(movimentos),

        # Mantemos todos normalizados para uso futuro,
        # mas isso não significa que serão salvos no LegalCase.
        "movimentos": movimentos,
    }

def consultar_processo(numero_processo):
    """
    Consulta automaticamente o processo no endpoint correspondente.

    O tribunal é identificado a partir do próprio número CNJ.

    Esta função:
    - não salva dados;
    - não altera models;
    - não cria movimentações;
    - não realiza retries automáticos.
    """

    numero_normalizado = normalizar_numero_processo(numero_processo)

    if len(numero_normalizado) != 20:
        return {
            "sucesso": False,
            "status": "NUMERO_INVALIDO",
            "mensagem": (
                "O número do processo deve possuir 20 dígitos "
                "no padrão CNJ."
            ),
            "numero_processo": numero_normalizado,
            "tribunal": None,
            "dados": None,
        }

    tribunal = identificar_tribunal(numero_normalizado)
    api_key = _obter_api_key()

    headers = {
        "Authorization": f"APIKey {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "_source": [
            "numeroProcesso",
            "tribunal",
            "grau",
            "dataAjuizamento",
            "classe",
            "sistema",
            "orgaoJulgador",
        ],
        "query": {
            "match": {
                "numeroProcesso": numero_normalizado,
            }
        },
        "size": 1,
    }

    try:
        response = requests.post(
            tribunal["endpoint"],
            headers=headers,
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )

    except requests.Timeout as exc:
        raise DataJudTimeoutError(
            "A consulta ao DataJud excedeu o tempo limite."
        ) from exc

    except requests.ConnectionError as exc:
        raise DataJudConnectionError(
            "Não foi possível estabelecer comunicação com o DataJud."
        ) from exc

    except requests.RequestException as exc:
        raise DataJudConnectionError(
            "Ocorreu uma falha de comunicação com o DataJud."
        ) from exc

    _tratar_resposta_http(response)

    try:
        resposta = response.json()
    except ValueError as exc:
        raise DataJudInvalidResponseError(
            "O DataJud retornou uma resposta em formato inesperado.",
            status_code=response.status_code,
        ) from exc

    hits = resposta.get("hits", {}).get("hits", [])

    if not hits:
        return {
            "sucesso": True,
            "status": "PROCESSO_NAO_ENCONTRADO",
            "mensagem": "Nenhum processo foi encontrado no DataJud.",
            "numero_processo": numero_normalizado,
            "tribunal": tribunal,
            "dados": None,
        }

    processo_bruto = hits[0].get("_source", {})

    processo_mapeado = mapear_dados_processo(processo_bruto)

    return {
        "sucesso": True,
        "status": "PROCESSO_ENCONTRADO",
        "mensagem": "Processo encontrado no DataJud.",
        "numero_processo": numero_normalizado,
        "tribunal": tribunal,
        "dados": processo_mapeado,
    }


def consultar_processo_trf1(numero_processo):
    """
    Compatibilidade temporária com a POC inicial.

    Novas implementações devem utilizar consultar_processo().
    """
    return consultar_processo(numero_processo)