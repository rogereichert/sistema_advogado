"use strict";


/* =============================================================
   CLIENT LIST
   -------------------------------------------------------------
   Responsável exclusivamente pela experiência da busca
   da listagem de clientes.

   A pesquisa dos registros NÃO é mais realizada no navegador.

   O backend é responsável por:

   - pesquisar em todos os clientes
   - calcular o total de resultados
   - paginar os resultados
   - entregar 10 clientes por página

   Este arquivo cuida somente de:

   - envio da pesquisa
   - limpeza da pesquisa
   - tecla Escape
   - botão de limpar
   - prevenção de envio duplicado

   O modal de cliente NÃO pertence a este arquivo.
============================================================= */

(function () {

    /* =========================================================
       ELEMENTOS
    ========================================================== */

    const searchForm = document.getElementById(
        "client-search-form"
    );

    const searchInput = document.getElementById(
        "client-search"
    );

    const inlineClearButton = document.getElementById(
        "client-search-clear-inline"
    );


    /* =========================================================
       GUARD
       ---------------------------------------------------------
       Caso o arquivo seja carregado acidentalmente fora da
       listagem de clientes, encerramos sem gerar erros.
    ========================================================== */

    if (!searchForm || !searchInput) {
        return;
    }


    /* =========================================================
       ESTADO
    ========================================================== */

    let submitting = false;


    /* =========================================================
       NORMALIZA VALOR DA PESQUISA
       ---------------------------------------------------------
       Remove espaços extras no início e no final antes de
       enviar a pesquisa ao backend.
    ========================================================== */

    function normalizeSearchValue() {

        return String(
            searchInput.value || ""
        ).trim();

    }


    /* =========================================================
       EXECUTA PESQUISA
       ---------------------------------------------------------
       A pesquisa é enviada via GET.

       Exemplo:

       /clientes/?q=Rodrigo

       A paginação sempre volta para a primeira página quando
       uma nova pesquisa é realizada, pois o formulário não
       envia o parâmetro "page".
    ========================================================== */

    function submitSearch() {

        if (submitting) {
            return;
        }


        const value = normalizeSearchValue();


        /*
         * Evita gerar:
         *
         * /clientes/?q=
         *
         * Se o campo estiver vazio, voltamos para a listagem
         * limpa.
         */

        if (!value) {

            window.location.href = searchForm.action;

            return;
        }


        searchInput.value = value;

        submitting = true;

        searchForm.submit();

    }


    /* =========================================================
       LIMPA PESQUISA
       ---------------------------------------------------------
       Como a pesquisa agora pertence ao backend, limpar
       significa voltar para a URL principal da listagem.
    ========================================================== */

    function clearSearch() {

        searchInput.value = "";

        window.location.href = searchForm.action;

    }


    /* =========================================================
       SUBMIT DO FORMULÁRIO
       ---------------------------------------------------------
       Enter no campo dispara naturalmente este evento.
    ========================================================== */

    searchForm.addEventListener(
        "submit",
        function (event) {

            event.preventDefault();

            submitSearch();

        }
    );


    /* =========================================================
       BOTÃO X
       ---------------------------------------------------------
       No novo template o botão de limpar é um link.

       Mantemos o comportamento também via JavaScript para
       garantir que o campo seja limpo antes da navegação.
    ========================================================== */

    if (inlineClearButton) {

        inlineClearButton.addEventListener(
            "click",
            function (event) {

                event.preventDefault();

                clearSearch();

            }
        );

    }


    /* =========================================================
       TECLA ESCAPE
       ---------------------------------------------------------
       Se houver algum conteúdo no campo, Escape limpa a busca.

       Não interferimos com Escape quando o campo já estiver
       vazio, evitando conflitos com outros componentes.
    ========================================================== */

    searchInput.addEventListener(
        "keydown",
        function (event) {

            if (
                event.key !== "Escape"
                || !searchInput.value
            ) {
                return;
            }


            event.preventDefault();

            clearSearch();

        }
    );


    /* =========================================================
       BOTÃO NATIVO DE INPUT SEARCH
       ---------------------------------------------------------
       Alguns navegadores exibem um "X" próprio em campos
       type="search".

       Quando ele é utilizado, o navegador dispara o evento
       "search".

       Se o campo ficar vazio, voltamos para a listagem
       completa.
    ========================================================== */

    searchInput.addEventListener(
        "search",
        function () {

            if (!normalizeSearchValue()) {
                clearSearch();
            }

        }
    );


    /* =========================================================
       RESTAURA ESTADO APÓS VOLTAR PELO NAVEGADOR
       ---------------------------------------------------------
       Caso o navegador restaure esta página pelo cache de
       navegação, liberamos novamente o formulário.
    ========================================================== */

    window.addEventListener(
        "pageshow",
        function () {

            submitting = false;

        }
    );

})();