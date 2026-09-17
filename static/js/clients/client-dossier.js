(() => {
    "use strict";

    // =========================================================
    // ELEMENTOS PRINCIPAIS
    // =========================================================

    const modal = document.getElementById("dossier-modal");
    const modalBackdrop = document.getElementById(
        "dossier-modal-backdrop"
    );
    const modalPanel = document.getElementById(
        "dossier-modal-panel"
    );

    const openButton = document.getElementById(
        "open-dossier-modal"
    );
    const closeButton = document.getElementById(
        "close-dossier-modal"
    );
    const cancelButton = document.getElementById(
        "cancel-dossier-modal"
    );

    const form = document.getElementById("dossier-form");
    const errorBox = document.getElementById(
        "dossier-error"
    );

    const toggleCasesButton = document.getElementById(
        "toggle-dossier-cases"
    );
    const toggleSectionsButton = document.getElementById(
        "toggle-dossier-sections"
    );

    const generateButton = document.getElementById(
        "generate-dossier-button"
    );

    if (
        !modal ||
        !openButton ||
        !closeButton ||
        !form
    ) {
        return;
    }


    // =========================================================
    // ESTADO
    // =========================================================

    let lastFocusedElement = null;


    // =========================================================
    // HELPERS
    // =========================================================

    function getCaseCheckboxes() {
        return Array.from(
            form.querySelectorAll(".dossier-case")
        );
    }


    function getSectionCheckboxes() {
        return Array.from(
            form.querySelectorAll(".dossier-section")
        );
    }


    function getCheckedCases() {
        return getCaseCheckboxes().filter(
            (checkbox) => checkbox.checked
        );
    }


    function getCheckedSections() {
        return getSectionCheckboxes().filter(
            (checkbox) => checkbox.checked
        );
    }


    function areAllChecked(checkboxes) {
        return (
            checkboxes.length > 0 &&
            checkboxes.every(
                (checkbox) => checkbox.checked
            )
        );
    }


    // =========================================================
    // ERRO
    // =========================================================

    function showError(message) {
        if (!errorBox) {
            return;
        }

        errorBox.textContent = message;
        errorBox.classList.remove("hidden");

        errorBox.scrollIntoView({
            behavior: "smooth",
            block: "nearest",
        });
    }


    function clearError() {
        if (!errorBox) {
            return;
        }

        errorBox.textContent = "";
        errorBox.classList.add("hidden");
    }


    // =========================================================
    // ESTADO DOS BOTÕES "TODOS"
    // =========================================================

    function updateCasesToggleButton() {
        if (!toggleCasesButton) {
            return;
        }

        const checkboxes = getCaseCheckboxes();

        if (!checkboxes.length) {
            toggleCasesButton.hidden = true;
            return;
        }

        toggleCasesButton.hidden = false;

        toggleCasesButton.textContent = areAllChecked(
            checkboxes
        )
            ? "Desmarcar todos"
            : "Marcar todos";
    }


    function updateSectionsToggleButton() {
        if (!toggleSectionsButton) {
            return;
        }

        const checkboxes = getSectionCheckboxes();

        toggleSectionsButton.textContent = areAllChecked(
            checkboxes
        )
            ? "Desmarcar todas"
            : "Marcar todas";
    }


    // =========================================================
    // ESTADO DO BOTÃO GERAR
    // =========================================================

    function updateGenerateButton() {
        if (!generateButton) {
            return;
        }

        const cases = getCaseCheckboxes();

        /*
         * O template já deixa o botão desabilitado quando
         * o cliente não possui nenhum caso.
         *
         * Aqui reforçamos essa regra no JavaScript.
         */
        generateButton.disabled = cases.length === 0;
    }


    // =========================================================
    // SINCRONIZAÇÃO
    // =========================================================

    function syncState() {
        updateCasesToggleButton();
        updateSectionsToggleButton();
        updateGenerateButton();
    }


    // =========================================================
    // ABRIR MODAL
    // =========================================================

    function openModal() {
        lastFocusedElement = document.activeElement;

        clearError();
        syncState();

        modal.classList.remove("hidden");
        modal.setAttribute("aria-hidden", "false");

        document.body.classList.add("overflow-hidden");

        window.requestAnimationFrame(() => {
            modalPanel?.focus();
        });
    }


    // =========================================================
    // FECHAR MODAL
    // =========================================================

    function closeModal() {
        if (modal.classList.contains("hidden")) {
            return;
        }

        modal.classList.add("hidden");
        modal.setAttribute("aria-hidden", "true");

        document.body.classList.remove("overflow-hidden");

        clearError();

        if (
            lastFocusedElement &&
            typeof lastFocusedElement.focus === "function"
        ) {
            lastFocusedElement.focus();
        }

        lastFocusedElement = null;
    }


    // =========================================================
    // MARCAR / DESMARCAR TODOS OS CASOS
    // =========================================================

    function toggleAllCases() {
        const checkboxes = getCaseCheckboxes();

        if (!checkboxes.length) {
            return;
        }

        const shouldCheck = !areAllChecked(checkboxes);

        checkboxes.forEach((checkbox) => {
            checkbox.checked = shouldCheck;
        });

        clearError();
        syncState();
    }


    // =========================================================
    // MARCAR / DESMARCAR TODAS AS SEÇÕES
    // =========================================================

    function toggleAllSections() {
        const checkboxes = getSectionCheckboxes();

        if (!checkboxes.length) {
            return;
        }

        const shouldCheck = !areAllChecked(checkboxes);

        checkboxes.forEach((checkbox) => {
            checkbox.checked = shouldCheck;
        });

        clearError();
        syncState();
    }


    // =========================================================
    // ALTERAÇÃO INDIVIDUAL — CASOS
    // =========================================================

    function handleCaseChange() {
        clearError();
        updateCasesToggleButton();
        updateGenerateButton();
    }


    // =========================================================
    // ALTERAÇÃO INDIVIDUAL — SEÇÕES
    // =========================================================

    function handleSectionChange() {
        clearError();
        updateSectionsToggleButton();
    }


    // =========================================================
    // VALIDAÇÃO
    // =========================================================

    function validateForm() {
        clearError();

        const caseCheckboxes = getCaseCheckboxes();
        const sectionCheckboxes =
            getSectionCheckboxes();

        const checkedCases = getCheckedCases();
        const checkedSections =
            getCheckedSections();


        // -----------------------------------------------------
        // CLIENTE SEM CASOS
        // -----------------------------------------------------

        if (!caseCheckboxes.length) {
            showError(
                "Este cliente não possui casos disponíveis para gerar o dossiê."
            );

            return false;
        }


        // -----------------------------------------------------
        // NENHUM CASO SELECIONADO
        // -----------------------------------------------------

        if (!checkedCases.length) {
            showError(
                "Selecione pelo menos um caso para incluir no dossiê."
            );

            return false;
        }


        // -----------------------------------------------------
        // NENHUMA SEÇÃO DISPONÍVEL
        // -----------------------------------------------------

        if (!sectionCheckboxes.length) {
            showError(
                "Nenhuma seção está disponível para gerar o dossiê."
            );

            return false;
        }


        // -----------------------------------------------------
        // NENHUMA SEÇÃO SELECIONADA
        // -----------------------------------------------------

        if (!checkedSections.length) {
            showError(
                "Selecione pelo menos uma seção para incluir no dossiê."
            );

            return false;
        }


        // -----------------------------------------------------
        // TIPO DO DOSSIÊ
        // -----------------------------------------------------

        const dossierType = form.querySelector(
            'input[name="dossier_type"]:checked'
        );

        if (!dossierType) {
            showError(
                "Selecione o tipo de dossiê que deseja gerar."
            );

            return false;
        }

        return true;
    }


    // =========================================================
    // SUBMIT
    // =========================================================

    function handleSubmit(event) {
        /*
         * IMPORTANTE:
         *
         * Não usamos fetch aqui.
         *
         * O form possui target="_blank", então queremos deixar
         * o navegador realizar o POST normalmente para que o
         * backend gere o PDF e ele seja aberto em uma nova aba.
         */

        if (!validateForm()) {
            event.preventDefault();
            return;
        }

        /*
         * O submit continua normalmente.
         *
         * Como o target é _blank, a página atual permanece
         * aberta e o PDF é carregado em outra aba.
         */

        window.setTimeout(() => {
            closeModal();
        }, 150);
    }


    // =========================================================
    // EVENTOS — ABERTURA / FECHAMENTO
    // =========================================================

    openButton.addEventListener(
        "click",
        openModal
    );


    closeButton.addEventListener(
        "click",
        closeModal
    );


    cancelButton?.addEventListener(
        "click",
        closeModal
    );


    modalBackdrop?.addEventListener(
        "click",
        closeModal
    );


    // =========================================================
    // EVENTOS — TOGGLES
    // =========================================================

    toggleCasesButton?.addEventListener(
        "click",
        toggleAllCases
    );


    toggleSectionsButton?.addEventListener(
        "click",
        toggleAllSections
    );


    // =========================================================
    // EVENTOS — CHECKBOXES
    // =========================================================

    getCaseCheckboxes().forEach((checkbox) => {
        checkbox.addEventListener(
            "change",
            handleCaseChange
        );
    });


    getSectionCheckboxes().forEach((checkbox) => {
        checkbox.addEventListener(
            "change",
            handleSectionChange
        );
    });


    // =========================================================
    // EVENTO — SUBMIT
    // =========================================================

    form.addEventListener(
        "submit",
        handleSubmit
    );


    // =========================================================
    // ESCAPE
    // =========================================================

    document.addEventListener("keydown", (event) => {
        if (
            event.key !== "Escape" ||
            modal.classList.contains("hidden")
        ) {
            return;
        }

        closeModal();
    });


    // =========================================================
    // ESTADO INICIAL
    // =========================================================

    syncState();


    // =========================================================
    // API PÚBLICA
    // =========================================================

    window.ClientDossier = {
        open: openModal,
        close: closeModal,
        validate: validateForm,
        sync: syncState,
    };
})();