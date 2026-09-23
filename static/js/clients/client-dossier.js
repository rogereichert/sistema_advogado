(() => {
    "use strict";

    // ==========================================================
    // ELEMENTOS
    // ==========================================================

    const modal = document.getElementById(
        "dossier-modal"
    );

    const backdrop = document.getElementById(
        "dossier-modal-backdrop"
    );

    const panel = document.getElementById(
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

    const form = document.getElementById(
        "dossier-form"
    );

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


    // ==========================================================
    // VERIFICAÇÃO BÁSICA
    // ==========================================================

    if (
        !modal
        || !openButton
        || !closeButton
        || !form
    ) {
        return;
    }


    // ==========================================================
    // ESTADO
    // ==========================================================

    let lastFocusedElement = null;


    // ==========================================================
    // CHECKBOXES
    // ==========================================================

    function getCaseCheckboxes() {
        return Array.from(
            form.querySelectorAll(
                ".dossier-case"
            )
        );
    }


    function getSectionCheckboxes() {
        return Array.from(
            form.querySelectorAll(
                ".dossier-section"
            )
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


    function getSelectedSectionValues() {
        return getCheckedSections().map(
            (checkbox) => checkbox.value
        );
    }


    function areAllChecked(checkboxes) {
        return (
            checkboxes.length > 0
            && checkboxes.every(
                (checkbox) => checkbox.checked
            )
        );
    }


    // ==========================================================
    // SEÇÕES QUE DEPENDEM DE CASOS
    // ==========================================================

    function selectedSectionsRequireCases() {
        const sectionsThatRequireCases = new Set([
            "cases",
            "history",
            "movements",
            "documents",
            "agenda",
            "internal_notes",
        ]);

        return getSelectedSectionValues().some(
            (value) => (
                sectionsThatRequireCases.has(
                    value
                )
            )
        );
    }


    // ==========================================================
    // ERROS
    // ==========================================================

    function showError(message) {
        if (!errorBox) {
            return;
        }

        errorBox.textContent = message;

        errorBox.classList.remove(
            "hidden"
        );
    }


    function clearError() {
        if (!errorBox) {
            return;
        }

        errorBox.textContent = "";

        errorBox.classList.add(
            "hidden"
        );
    }


    // ==========================================================
    // BOTÃO MARCAR / DESMARCAR CASOS
    // ==========================================================

    function updateCasesToggleButton() {
        if (!toggleCasesButton) {
            return;
        }

        const checkboxes = getCaseCheckboxes();

        if (!checkboxes.length) {
            toggleCasesButton.classList.add(
                "hidden"
            );

            return;
        }

        toggleCasesButton.classList.remove(
            "hidden"
        );

        toggleCasesButton.textContent = (
            areAllChecked(checkboxes)
                ? "Desmarcar todos"
                : "Marcar todos"
        );
    }


    // ==========================================================
    // BOTÃO MARCAR / DESMARCAR SEÇÕES
    // ==========================================================

    function updateSectionsToggleButton() {
        if (!toggleSectionsButton) {
            return;
        }

        const checkboxes = getSectionCheckboxes();

        if (!checkboxes.length) {
            toggleSectionsButton.classList.add(
                "hidden"
            );

            return;
        }

        toggleSectionsButton.classList.remove(
            "hidden"
        );

        toggleSectionsButton.textContent = (
            areAllChecked(checkboxes)
                ? "Desmarcar todas"
                : "Marcar todas"
        );
    }


    // ==========================================================
    // BOTÃO GERAR
    // ==========================================================

    function updateGenerateButton() {
        if (!generateButton) {
            return;
        }

        /*
         * O botão permanece disponível.
         *
         * A validação acontece no submit para que,
         * em caso de combinação inválida, o usuário
         * receba uma mensagem explicando o problema.
         */

        generateButton.disabled = false;
    }


    // ==========================================================
    // SINCRONIZAÇÃO DA INTERFACE
    // ==========================================================

    function syncState() {
        updateCasesToggleButton();
        updateSectionsToggleButton();
        updateGenerateButton();
    }


    // ==========================================================
    // ABRIR MODAL
    // ==========================================================

    function openModal() {
        lastFocusedElement = (
            document.activeElement
        );

        clearError();
        syncState();

        modal.classList.remove(
            "hidden"
        );

        modal.setAttribute(
            "aria-hidden",
            "false"
        );

        document.body.classList.add(
            "overflow-hidden"
        );

        window.requestAnimationFrame(
            () => {
                if (panel) {
                    panel.focus();
                }
            }
        );
    }


    // ==========================================================
    // FECHAR MODAL
    // ==========================================================

    function closeModal() {
        modal.classList.add(
            "hidden"
        );

        modal.setAttribute(
            "aria-hidden",
            "true"
        );

        document.body.classList.remove(
            "overflow-hidden"
        );

        clearError();

        if (
            lastFocusedElement
            && typeof lastFocusedElement.focus === "function"
        ) {
            lastFocusedElement.focus();
        }
    }


    // ==========================================================
    // MARCAR / DESMARCAR TODOS OS CASOS
    // ==========================================================

    function toggleAllCases() {
        const checkboxes = getCaseCheckboxes();

        if (!checkboxes.length) {
            return;
        }

        const shouldCheck = !areAllChecked(
            checkboxes
        );

        checkboxes.forEach(
            (checkbox) => {
                checkbox.checked = shouldCheck;
            }
        );

        clearError();
        syncState();
    }


    // ==========================================================
    // MARCAR / DESMARCAR TODAS AS SEÇÕES
    // ==========================================================

    function toggleAllSections() {
        const checkboxes = getSectionCheckboxes();

        if (!checkboxes.length) {
            return;
        }

        const shouldCheck = !areAllChecked(
            checkboxes
        );

        checkboxes.forEach(
            (checkbox) => {
                checkbox.checked = shouldCheck;
            }
        );

        clearError();
        syncState();
    }


    // ==========================================================
    // ALTERAÇÃO DE CASO
    // ==========================================================

    function handleCaseChange() {
        clearError();
        updateCasesToggleButton();
        updateGenerateButton();
    }


    // ==========================================================
    // ALTERAÇÃO DE SEÇÃO
    // ==========================================================

    function handleSectionChange() {
        clearError();
        updateSectionsToggleButton();
        updateGenerateButton();
    }


    // ==========================================================
    // VALIDAÇÃO
    // ==========================================================

    function validateForm() {
        clearError();

        const sectionCheckboxes = (
            getSectionCheckboxes()
        );

        const checkedSections = (
            getCheckedSections()
        );

        const checkedCases = (
            getCheckedCases()
        );

        // ------------------------------------------------------
        // PRECISA EXISTIR PELO MENOS UMA SEÇÃO DISPONÍVEL
        // ------------------------------------------------------

        if (!sectionCheckboxes.length) {
            showError(
                "Nenhuma seção está disponível para gerar o dossiê."
            );

            return false;
        }

        // ------------------------------------------------------
        // PRECISA EXISTIR PELO MENOS UMA SEÇÃO SELECIONADA
        // ------------------------------------------------------

        if (!checkedSections.length) {
            showError(
                "Selecione pelo menos uma seção para incluir no dossiê."
            );

            return false;
        }

        // ------------------------------------------------------
        // SEÇÃO JURÍDICA EXIGE PELO MENOS UM CASO
        // ------------------------------------------------------

        if (
            selectedSectionsRequireCases()
            && !checkedCases.length
        ) {
            showError(
                "Selecione pelo menos um caso para incluir as informações jurídicas escolhidas no dossiê."
            );

            return false;
        }

        return true;
    }


    // ==========================================================
    // SUBMIT
    // ==========================================================

    function handleSubmit(event) {
        if (!validateForm()) {
            event.preventDefault();

            return;
        }

        /*
         * O formulário utiliza target="_blank".
         *
         * O navegador realiza o POST normalmente
         * e abre o PDF gerado em uma nova aba.
         */

        window.setTimeout(
            () => {
                closeModal();
            },
            150
        );
    }


    // ==========================================================
    // EVENTOS — ABRIR
    // ==========================================================

    openButton.addEventListener(
        "click",
        openModal
    );


    // ==========================================================
    // EVENTOS — FECHAR
    // ==========================================================

    closeButton.addEventListener(
        "click",
        closeModal
    );


    if (cancelButton) {
        cancelButton.addEventListener(
            "click",
            closeModal
        );
    }


    if (backdrop) {
        backdrop.addEventListener(
            "click",
            closeModal
        );
    }


    // ==========================================================
    // EVENTOS — MARCAR / DESMARCAR TODOS
    // ==========================================================

    if (toggleCasesButton) {
        toggleCasesButton.addEventListener(
            "click",
            toggleAllCases
        );
    }


    if (toggleSectionsButton) {
        toggleSectionsButton.addEventListener(
            "click",
            toggleAllSections
        );
    }


    // ==========================================================
    // EVENTOS — CHECKBOXES DE CASOS
    // ==========================================================

    getCaseCheckboxes().forEach(
        (checkbox) => {
            checkbox.addEventListener(
                "change",
                handleCaseChange
            );
        }
    );


    // ==========================================================
    // EVENTOS — CHECKBOXES DE SEÇÕES
    // ==========================================================

    getSectionCheckboxes().forEach(
        (checkbox) => {
            checkbox.addEventListener(
                "change",
                handleSectionChange
            );
        }
    );


    // ==========================================================
    // EVENTO — SUBMIT
    // ==========================================================

    form.addEventListener(
        "submit",
        handleSubmit
    );


    // ==========================================================
    // TECLA ESC
    // ==========================================================

    document.addEventListener(
        "keydown",
        (event) => {
            if (
                event.key === "Escape"
                && !modal.classList.contains(
                    "hidden"
                )
            ) {
                closeModal();
            }
        }
    );


    // ==========================================================
    // ESTADO INICIAL
    // ==========================================================

    syncState();


    // ==========================================================
    // API PÚBLICA
    // ==========================================================

    window.ClientDossier = {
        open: openModal,
        close: closeModal,
        validate: validateForm,
        sync: syncState,
    };
})();