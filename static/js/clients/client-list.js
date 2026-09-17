"use strict";


/* =============================================================
   CLIENT LIST
   -------------------------------------------------------------
   Responsável exclusivamente pela listagem de clientes:

   - pesquisa
   - normalização do texto
   - filtro desktop
   - filtro mobile
   - contador de resultados
   - estado "nenhum resultado"
   - limpeza da pesquisa

   O modal de cliente NÃO pertence a este arquivo.
============================================================= */

(function () {

    /* =========================================================
       ELEMENTOS
    ========================================================== */

    const searchInput = document.getElementById("client-search");
    const visibleCount = document.getElementById("visible-client-count");
    const countLabel = document.getElementById("client-count-label");

    const tableContainer = document.getElementById(
        "client-table-container"
    );

    const mobileContainer = document.getElementById(
        "client-mobile-container"
    );

    const searchEmpty = document.getElementById(
        "client-search-empty"
    );

    const searchTerm = document.getElementById(
        "client-search-term"
    );

    const clearSearchButton = document.getElementById(
        "client-search-clear"
    );

    const inlineClearButton = document.getElementById(
        "client-search-clear-inline"
    );


    /* =========================================================
       A PÁGINA PODE NÃO SER A LISTAGEM DE CLIENTES
       ---------------------------------------------------------
       Como este JS é carregado somente em client_list.html,
       normalmente searchInput existirá.

       Ainda assim, este guard evita erros caso o arquivo seja
       reutilizado ou carregado acidentalmente em outra página.
    ========================================================== */

    if (!searchInput) {
        return;
    }


    /* =========================================================
       REGISTROS
    ========================================================== */

    const desktopRows = Array.from(
        document.querySelectorAll(".client-row")
    );

    const mobileItems = Array.from(
        document.querySelectorAll(".client-mobile-item")
    );


    /* =========================================================
       NORMALIZAÇÃO
       ---------------------------------------------------------
       Permite que:

       "João" seja encontrado digitando "joao"
       "José" seja encontrado digitando "jose"

       Também normaliza espaços e caixa.
    ========================================================== */

    function normalizeText(value) {

        return String(value || "")
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .toLowerCase()
            .replace(/\s+/g, " ")
            .trim();

    }


    /* =========================================================
       NORMALIZAÇÃO NUMÉRICA
       ---------------------------------------------------------
       Mantemos também uma versão contendo somente números.

       Isso melhora buscas como:

       CPF salvo:
       123.456.789-00

       Usuário pesquisa:
       12345678900

       Ou o contrário.
    ========================================================== */

    function normalizeDigits(value) {

        return String(value || "")
            .replace(/\D/g, "");

    }


    /* =========================================================
       TERMO DE PESQUISA
    ========================================================== */

    function getSearchQuery() {

        const raw = searchInput.value || "";

        return {
            raw: raw.trim(),
            text: normalizeText(raw),
            digits: normalizeDigits(raw),
        };

    }


    /* =========================================================
       TEXTO PESQUISÁVEL DE UM REGISTRO
    ========================================================== */

    function getItemSearchText(element) {

        return element.dataset.searchText || "";

    }


    /* =========================================================
       VERIFICA SE UM REGISTRO CORRESPONDE À PESQUISA
    ========================================================== */

    function itemMatches(element, query) {

        if (!query.text) {
            return true;
        }


        const searchableValue = getItemSearchText(element);

        const searchableText = normalizeText(
            searchableValue
        );


        /* -----------------------------------------------------
           Pesquisa textual
        ------------------------------------------------------ */

        if (searchableText.includes(query.text)) {
            return true;
        }


        /* -----------------------------------------------------
           Pesquisa numérica

           Só executamos quando o usuário digitou ao menos
           um número.
        ------------------------------------------------------ */

        if (query.digits) {

            const searchableDigits = normalizeDigits(
                searchableValue
            );

            if (
                searchableDigits.includes(query.digits)
            ) {
                return true;
            }

        }


        return false;

    }


    /* =========================================================
       ALTERA VISIBILIDADE
    ========================================================== */

    function setItemVisibility(element, visible) {

        element.classList.toggle(
            "hidden",
            !visible
        );

    }


    /* =========================================================
       FILTRA UMA COLEÇÃO
    ========================================================== */

    function filterItems(items, query) {

        let matches = 0;


        items.forEach(function (item) {

            const visible = itemMatches(
                item,
                query
            );

            setItemVisibility(
                item,
                visible
            );

            if (visible) {
                matches += 1;
            }

        });


        return matches;

    }


    /* =========================================================
       ATUALIZA CONTADOR
    ========================================================== */

    function updateCounter(count) {

        if (visibleCount) {
            visibleCount.textContent = String(count);
        }


        if (countLabel) {

            countLabel.textContent = (
                count === 1
                    ? "cliente"
                    : "clientes"
            );

        }

    }


    /* =========================================================
       ATUALIZA BOTÃO "X" DO CAMPO
    ========================================================== */

    function updateInlineClearButton(query) {

        if (!inlineClearButton) {
            return;
        }


        const hasSearch = Boolean(query.raw);


        inlineClearButton.classList.toggle(
            "hidden",
            !hasSearch
        );

        inlineClearButton.classList.toggle(
            "flex",
            hasSearch
        );

    }


    /* =========================================================
       ATUALIZA TEXTO DO ESTADO VAZIO
    ========================================================== */

    function updateSearchTerm(query) {

        if (!searchTerm) {
            return;
        }


        if (!query.raw) {
            searchTerm.textContent = "";
            return;
        }


        searchTerm.textContent = `“${query.raw}”`;

    }


    /* =========================================================
       MOSTRA / ESCONDE LISTAGEM
    ========================================================== */

    function updateListVisibility(
        hasSearch,
        hasResults
    ) {

        /*
         * Sem pesquisa:
         *
         * mostramos normalmente desktop e mobile.
         */

        if (!hasSearch) {

            if (tableContainer) {
                tableContainer.classList.remove("hidden");
                tableContainer.classList.add("lg:block");
            }


            if (mobileContainer) {
                mobileContainer.classList.remove("hidden");
                mobileContainer.classList.add("lg:hidden");
            }


            if (searchEmpty) {
                searchEmpty.classList.add("hidden");
            }


            return;

        }


        /*
         * Pesquisa com resultados.
         */

        if (hasResults) {

            if (tableContainer) {
                tableContainer.classList.remove("hidden");
                tableContainer.classList.add("lg:block");
            }


            if (mobileContainer) {
                mobileContainer.classList.remove("hidden");
                mobileContainer.classList.add("lg:hidden");
            }


            if (searchEmpty) {
                searchEmpty.classList.add("hidden");
            }


            return;

        }


        /*
         * Pesquisa sem resultados.
         *
         * Escondemos as duas representações da listagem e
         * mostramos apenas o estado vazio da pesquisa.
         */

        if (tableContainer) {
            tableContainer.classList.add("hidden");
        }


        if (mobileContainer) {
            mobileContainer.classList.add("hidden");
        }


        if (searchEmpty) {
            searchEmpty.classList.remove("hidden");
        }

    }


    /* =========================================================
       APLICA PESQUISA
    ========================================================== */

    function applySearch() {

        const query = getSearchQuery();


        /* -----------------------------------------------------
           Desktop
        ------------------------------------------------------ */

        const desktopMatches = filterItems(
            desktopRows,
            query
        );


        /* -----------------------------------------------------
           Mobile
        ------------------------------------------------------ */

        const mobileMatches = filterItems(
            mobileItems,
            query
        );


        /*
         * Desktop e mobile representam os mesmos clientes.
         *
         * Não podemos somar os dois valores, senão:
         *
         * 10 clientes desktop
         * +
         * 10 clientes mobile
         * =
         * contador incorreto de 20.
         *
         * Preferimos desktop e usamos mobile como fallback.
         */

        const resultCount = desktopRows.length
            ? desktopMatches
            : mobileMatches;


        const hasSearch = Boolean(
            query.raw
        );

        const hasResults = (
            resultCount > 0
        );


        updateCounter(
            resultCount
        );

        updateInlineClearButton(
            query
        );

        updateSearchTerm(
            query
        );

        updateListVisibility(
            hasSearch,
            hasResults
        );

    }


    /* =========================================================
       LIMPA PESQUISA
    ========================================================== */

    function clearSearch() {

        searchInput.value = "";

        applySearch();

        searchInput.focus();

    }


    /* =========================================================
       EVENTOS
    ========================================================== */

    searchInput.addEventListener(
        "input",
        applySearch
    );


    /*
     * Alguns navegadores exibem um botão nativo de limpar em
     * inputs type="search".
     *
     * O evento "search" garante atualização também nesse caso.
     */

    searchInput.addEventListener(
        "search",
        applySearch
    );


    if (clearSearchButton) {

        clearSearchButton.addEventListener(
            "click",
            clearSearch
        );

    }


    if (inlineClearButton) {

        inlineClearButton.addEventListener(
            "click",
            clearSearch
        );

    }


    /* =========================================================
       ESC PARA LIMPAR A PESQUISA
       ---------------------------------------------------------
       Só interceptamos Escape quando o campo de pesquisa
       estiver focado e houver algum valor digitado.

       Isso evita conflito futuro com o Escape do modal.
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
       ESTADO INICIAL
    ========================================================== */

    applySearch();

})();