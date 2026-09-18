(() => {
    "use strict";

    const form = document.getElementById("case-filter-form");

    if (!form) {
        return;
    }

    const searchInput = document.getElementById("case-search");
    const statusSelect = document.getElementById("case-status");
    const areaInput = document.getElementById("case-area");

    const submitButton = form.querySelector('button[type="submit"]');

    let isSubmitting = false;


    // ============================================================
    // NORMALIZAÇÃO
    // ============================================================

    function normalizeValue(value) {
        return String(value || "")
            .replace(/\s+/g, " ")
            .trim();
    }


    function normalizeFields() {
        if (searchInput) {
            searchInput.value = normalizeValue(searchInput.value);
        }

        if (areaInput) {
            areaInput.value = normalizeValue(areaInput.value);
        }
    }


    // ============================================================
    // ESTADO DO BOTÃO
    // ============================================================

    function setSubmittingState() {
        if (!submitButton) {
            return;
        }

        submitButton.disabled = true;
        submitButton.setAttribute("aria-busy", "true");
        submitButton.classList.add("cursor-wait", "opacity-75");

        const label = submitButton.querySelector(
            "[data-submit-label]"
        );

        if (label) {
            label.textContent = "Filtrando...";
        }
    }


    // ============================================================
    // SUBMISSÃO
    // ============================================================

    form.addEventListener("submit", (event) => {
        if (isSubmitting) {
            event.preventDefault();
            return;
        }

        normalizeFields();

        isSubmitting = true;
        setSubmittingState();
    });


    // ============================================================
    // ENTER NOS CAMPOS DE TEXTO
    // ============================================================

    [searchInput, areaInput].forEach((input) => {
        if (!input) {
            return;
        }

        input.addEventListener("keydown", (event) => {
            if (event.key !== "Enter") {
                return;
            }

            event.preventDefault();

            normalizeFields();

            if (typeof form.requestSubmit === "function") {
                form.requestSubmit();
                return;
            }

            form.submit();
        });
    });


    // ============================================================
    // ESC LIMPA O CAMPO DE BUSCA EM FOCO
    // ============================================================

    [searchInput, areaInput].forEach((input) => {
        if (!input) {
            return;
        }

        input.addEventListener("keydown", (event) => {
            if (event.key !== "Escape") {
                return;
            }

            if (!input.value) {
                return;
            }

            event.preventDefault();

            input.value = "";
            input.focus();
        });
    });


    // ============================================================
    // ATALHO DE FOCO NA BUSCA
    //
    // "/" posiciona o cursor na busca quando o usuário não estiver
    // digitando em outro campo.
    // ============================================================

    document.addEventListener("keydown", (event) => {
        if (
            event.key !== "/" ||
            event.ctrlKey ||
            event.metaKey ||
            event.altKey
        ) {
            return;
        }

        const target = event.target;

        const isTyping =
            target instanceof HTMLInputElement ||
            target instanceof HTMLTextAreaElement ||
            target instanceof HTMLSelectElement ||
            target?.isContentEditable;

        if (isTyping || !searchInput) {
            return;
        }

        event.preventDefault();

        searchInput.focus();
        searchInput.select();
    });


    // ============================================================
    // STATUS
    //
    // Mantemos a aplicação manual pelo botão "Aplicar filtros".
    // Isso evita requisições inesperadas enquanto o usuário ainda
    // está preenchendo os demais critérios.
    // ============================================================

    if (statusSelect) {
        statusSelect.addEventListener("change", () => {
            statusSelect.dataset.changed = "true";
        });
    }


    // ============================================================
    // RESTAURA ESTADO
    //
    // Útil quando o navegador retorna para a página usando cache
    // de navegação (back/forward cache).
    // ============================================================

    window.addEventListener("pageshow", () => {
        isSubmitting = false;

        if (!submitButton) {
            return;
        }

        submitButton.disabled = false;
        submitButton.removeAttribute("aria-busy");
        submitButton.classList.remove(
            "cursor-wait",
            "opacity-75"
        );

        const label = submitButton.querySelector(
            "[data-submit-label]"
        );

        if (label) {
            label.textContent = "Aplicar filtros";
        }
    });
})();