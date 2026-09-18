(() => {
    "use strict";

    const modal = document.getElementById("movement-modal");

    if (!modal) {
        return;
    }

    const modalBody = document.getElementById("movement-modal-body");
    const modalPanel = modal.querySelector(
        "[data-movement-modal-panel]"
    );
    const backdrop = modal.querySelector(
        "[data-movement-modal-backdrop]"
    );

    let triggerElement = null;
    let movementUrl = "";
    let isSubmitting = false;

    const loadingTemplate = `
        <div
            data-movement-modal-loading
            class="flex min-h-64 items-center justify-center"
        >
            <div class="text-center">
                <svg
                    class="mx-auto h-6 w-6 animate-spin text-brand-700"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                >
                    <circle
                        class="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        stroke-width="4"
                    ></circle>

                    <path
                        class="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 0 1 8-8V0C5.373 0 0 5.373 0 12h4Z"
                    ></path>
                </svg>

                <p class="mt-3 text-sm font-medium text-slate-500">
                    Carregando formulário...
                </p>
            </div>
        </div>
    `;

    const errorTemplate = `
        <div
            class="flex min-h-64 items-center justify-center"
            data-movement-modal-error
        >
            <div class="max-w-sm text-center">
                <div
                    class="mx-auto flex h-11 w-11 items-center justify-center rounded-full bg-red-50 text-red-600"
                >
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke-width="1.8"
                        stroke="currentColor"
                        class="h-5 w-5"
                        aria-hidden="true"
                    >
                        <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            d="M12 9v3.75m9-1.5a9 9 0 1 1-18 0 9 9 0 0 1 18 0ZM12 15.75h.008v.008H12v-.008Z"
                        />
                    </svg>
                </div>

                <h3 class="mt-3 text-sm font-semibold text-brand-950">
                    Não foi possível carregar o formulário
                </h3>

                <p class="mt-1 text-xs leading-5 text-slate-500">
                    Tente novamente. Se o problema persistir,
                    recarregue a página.
                </p>

                <button
                    type="button"
                    data-movement-modal-retry
                    class="mt-4 inline-flex min-h-10 items-center justify-center rounded-xl bg-brand-950 px-4 text-sm font-semibold text-white transition hover:bg-brand-800 focus:outline-none focus:ring-4 focus:ring-brand-100"
                >
                    Tentar novamente
                </button>
            </div>
        </div>
    `;


    // =========================================================
    // UTILITÁRIOS
    // =========================================================

    function setBodyContent(html) {
        if (!modalBody) {
            return;
        }

        modalBody.innerHTML = html;
    }


    function showLoading() {
        setBodyContent(loadingTemplate);
    }


    function showError() {
        setBodyContent(errorTemplate);
    }


    function focusFirstField() {
        if (!modalBody) {
            return;
        }

        const field = modalBody.querySelector(
            "input:not([type='hidden']):not([disabled]), " +
            "textarea:not([disabled]), " +
            "select:not([disabled])"
        );

        if (field) {
            window.requestAnimationFrame(() => {
                field.focus();
            });
        }
    }


    function getFocusableElements() {
        if (!modalPanel) {
            return [];
        }

        return Array.from(
            modalPanel.querySelectorAll(
                [
                    "a[href]",
                    "button:not([disabled])",
                    "input:not([disabled]):not([type='hidden'])",
                    "textarea:not([disabled])",
                    "select:not([disabled])",
                    "[tabindex]:not([tabindex='-1'])",
                ].join(",")
            )
        ).filter((element) => {
            return element.offsetParent !== null;
        });
    }


    // =========================================================
    // ABERTURA / FECHAMENTO
    // =========================================================

    function openModal(url, trigger = null) {
        if (!url) {
            return;
        }

        movementUrl = url;
        triggerElement = trigger;

        modal.classList.remove("hidden");
        modal.setAttribute("aria-hidden", "false");

        document.documentElement.classList.add("overflow-hidden");
        document.body.classList.add("overflow-hidden");

        showLoading();
        loadForm();
    }


    function closeModal() {
        if (isSubmitting) {
            return;
        }

        modal.classList.add("hidden");
        modal.setAttribute("aria-hidden", "true");

        document.documentElement.classList.remove("overflow-hidden");
        document.body.classList.remove("overflow-hidden");

        movementUrl = "";

        showLoading();

        if (
            triggerElement &&
            typeof triggerElement.focus === "function"
        ) {
            triggerElement.focus();
        }

        triggerElement = null;
    }


    // =========================================================
    // CARREGAMENTO AJAX
    // =========================================================

    async function loadForm() {
        if (!movementUrl) {
            return;
        }

        showLoading();

        try {
            const response = await fetch(movementUrl, {
                method: "GET",
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                },
                credentials: "same-origin",
            });

            if (!response.ok) {
                throw new Error(
                    `Erro ao carregar formulário: ${response.status}`
                );
            }

            const html = await response.text();

            setBodyContent(html);
            focusFirstField();
        } catch (error) {
            console.error(
                "Erro ao carregar movimentação:",
                error
            );

            showError();
        }
    }


    // =========================================================
    // ENVIO AJAX
    // =========================================================

    async function submitForm(form) {
        if (isSubmitting) {
            return;
        }

        isSubmitting = true;

        const submitButton = form.querySelector(
            "button[type='submit']"
        );

        const submitLabel = form.querySelector(
            "[data-movement-submit-label]"
        );

        const originalLabel = submitLabel
            ? submitLabel.textContent
            : "";

        if (submitButton) {
            submitButton.disabled = true;
            submitButton.classList.add(
                "cursor-not-allowed",
                "opacity-70"
            );
        }

        if (submitLabel) {
            submitLabel.textContent = "Registrando...";
        }

        try {
            const formData = new FormData(form);

            const response = await fetch(
                form.action || movementUrl,
                {
                    method: "POST",
                    body: formData,
                    headers: {
                        "X-Requested-With": "XMLHttpRequest",
                    },
                    credentials: "same-origin",
                }
            );

            const contentType =
                response.headers.get("content-type") || "";

            if (
                response.ok &&
                contentType.includes("application/json")
            ) {
                const data = await response.json();

                if (data.success) {
                    window.location.reload();
                    return;
                }
            }

            /*
             * Quando o formulário é inválido, o backend devolve
             * novamente o HTML do formulário com status 400.
             */

            if (
                response.status === 400 ||
                contentType.includes("text/html")
            ) {
                const html = await response.text();

                setBodyContent(html);

                const firstErrorField =
                    modalBody.querySelector(
                        ".text-red-600"
                    );

                if (firstErrorField) {
                    firstErrorField.scrollIntoView({
                        behavior: "smooth",
                        block: "center",
                    });
                } else {
                    focusFirstField();
                }

                return;
            }

            throw new Error(
                `Erro ao registrar movimentação: ${response.status}`
            );
        } catch (error) {
            console.error(
                "Erro ao registrar movimentação:",
                error
            );

            showError();
        } finally {
            isSubmitting = false;

            /*
             * Só restaura o botão se o formulário original ainda
             * estiver no DOM. Em erro de validação ele já foi
             * substituído pelo HTML devolvido pelo backend.
             */

            if (document.body.contains(form)) {
                if (submitButton) {
                    submitButton.disabled = false;
                    submitButton.classList.remove(
                        "cursor-not-allowed",
                        "opacity-70"
                    );
                }

                if (submitLabel) {
                    submitLabel.textContent =
                        originalLabel.trim() ||
                        "Registrar movimentação";
                }
            }
        }
    }


    // =========================================================
    // EVENTOS POR DELEGAÇÃO
    // =========================================================

    document.addEventListener("click", (event) => {
        const trigger = event.target.closest(
            "[data-movement-modal-open]"
        );

        if (trigger) {
            const url =
                trigger.dataset.movementUrl ||
                trigger.getAttribute("href");

            if (!url) {
                return;
            }

            event.preventDefault();

            openModal(
                url,
                trigger
            );

            return;
        }


        const closeButton = event.target.closest(
            "[data-movement-modal-close]"
        );

        if (
            closeButton &&
            !modal.classList.contains("hidden")
        ) {
            event.preventDefault();

            closeModal();

            return;
        }


        const retryButton = event.target.closest(
            "[data-movement-modal-retry]"
        );

        if (
            retryButton &&
            !modal.classList.contains("hidden")
        ) {
            event.preventDefault();

            loadForm();
        }
    });


    document.addEventListener("submit", (event) => {
        const form = event.target.closest(
            "#movement-form"
        );

        if (
            !form ||
            modal.classList.contains("hidden") ||
            !modal.contains(form)
        ) {
            return;
        }

        event.preventDefault();

        submitForm(form);
    });


    // =========================================================
    // CLIQUE NO BACKDROP
    // =========================================================

    if (backdrop) {
        backdrop.addEventListener("click", () => {
            closeModal();
        });
    }


    // =========================================================
    // TECLADO
    // =========================================================

    document.addEventListener("keydown", (event) => {
        if (modal.classList.contains("hidden")) {
            return;
        }

        if (event.key === "Escape") {
            event.preventDefault();

            closeModal();

            return;
        }


        /*
         * Mantém o foco dentro do modal.
         */

        if (event.key === "Tab") {
            const focusableElements =
                getFocusableElements();

            if (!focusableElements.length) {
                event.preventDefault();
                return;
            }

            const firstElement =
                focusableElements[0];

            const lastElement =
                focusableElements[
                    focusableElements.length - 1
                ];

            if (
                event.shiftKey &&
                document.activeElement === firstElement
            ) {
                event.preventDefault();
                lastElement.focus();

                return;
            }

            if (
                !event.shiftKey &&
                document.activeElement === lastElement
            ) {
                event.preventDefault();
                firstElement.focus();
            }
        }
    });


    // =========================================================
    // SEGURANÇA PARA CACHE DO NAVEGADOR
    // =========================================================

    window.addEventListener("pageshow", () => {
        if (!modal.classList.contains("hidden")) {
            modal.classList.add("hidden");
            modal.setAttribute(
                "aria-hidden",
                "true"
            );
        }

        document.documentElement.classList.remove(
            "overflow-hidden"
        );

        document.body.classList.remove(
            "overflow-hidden"
        );

        isSubmitting = false;
    });
})();