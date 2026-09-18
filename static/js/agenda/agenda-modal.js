(() => {
    "use strict";

    const modal = document.getElementById("agenda-modal");

    if (!modal) {
        return;
    }

    const modalBody = document.getElementById(
        "agenda-modal-body"
    );

    const modalPanel = modal.querySelector(
        "[data-agenda-modal-panel]"
    );

    const backdrop = modal.querySelector(
        "[data-agenda-modal-backdrop]"
    );

    let triggerElement = null;
    let agendaUrl = "";
    let isSubmitting = false;


    // =========================================================
    // TEMPLATES
    // =========================================================

    const loadingTemplate = `
        <div
            data-agenda-modal-loading
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

                <p
                    class="mt-3 text-sm font-medium text-slate-500"
                >
                    Carregando compromisso...
                </p>

            </div>
        </div>
    `;


    const errorTemplate = `
        <div
            data-agenda-modal-error
            class="flex min-h-64 items-center justify-center"
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

                <h3
                    class="mt-3 text-sm font-semibold text-brand-950"
                >
                    Não foi possível carregar o compromisso
                </h3>

                <p
                    class="mt-1 text-xs leading-5 text-slate-500"
                >
                    Tente novamente. Se o problema persistir,
                    recarregue a página.
                </p>

                <button
                    type="button"
                    data-agenda-modal-retry
                    class="mt-4 inline-flex min-h-10 items-center justify-center rounded-xl bg-brand-950 px-4 text-sm font-semibold text-white transition hover:bg-brand-800 focus:outline-none focus:ring-4 focus:ring-brand-100"
                >
                    Tentar novamente
                </button>

            </div>
        </div>
    `;


    // =========================================================
    // CONTEÚDO
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


    // =========================================================
    // FOCO
    // =========================================================

    function focusFirstField() {
        if (!modalBody) {
            return;
        }

        const field = modalBody.querySelector(
            "input:not([type='hidden']):not([disabled]), " +
            "textarea:not([disabled]), " +
            "select:not([disabled])"
        );

        if (!field) {
            return;
        }

        window.requestAnimationFrame(() => {
            field.focus();
        });
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
    // ABRIR
    // =========================================================

    function openModal(url, trigger = null) {
        if (!url) {
            return;
        }

        agendaUrl = url;
        triggerElement = trigger;

        modal.classList.remove("hidden");

        modal.setAttribute(
            "aria-hidden",
            "false"
        );

        document.documentElement.classList.add(
            "overflow-hidden"
        );

        document.body.classList.add(
            "overflow-hidden"
        );

        showLoading();

        loadForm();
    }


    // =========================================================
    // FECHAR
    // =========================================================

    function closeModal() {
        if (isSubmitting) {
            return;
        }

        modal.classList.add("hidden");

        modal.setAttribute(
            "aria-hidden",
            "true"
        );

        document.documentElement.classList.remove(
            "overflow-hidden"
        );

        document.body.classList.remove(
            "overflow-hidden"
        );

        agendaUrl = "";

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
    // CARREGAR FORMULÁRIO
    // =========================================================

    async function loadForm() {
        if (!agendaUrl) {
            return;
        }

        showLoading();

        try {
            const response = await fetch(
                agendaUrl,
                {
                    method: "GET",

                    headers: {
                        "X-Requested-With": "XMLHttpRequest",
                    },

                    credentials: "same-origin",
                }
            );

            if (!response.ok) {
                throw new Error(
                    `Erro ao carregar compromisso: ${response.status}`
                );
            }

            const html = await response.text();

            setBodyContent(html);

            focusFirstField();

        } catch (error) {
            console.error(
                "Erro ao carregar formulário da agenda:",
                error
            );

            showError();
        }
    }


    // =========================================================
    // ENVIAR FORMULÁRIO
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
            "[data-agenda-submit-label]"
        );

        const originalLabel = submitLabel
            ? submitLabel.textContent.trim()
            : "Agendar compromisso";


        // -----------------------------------------------------
        // ESTADO DE ENVIO
        // -----------------------------------------------------

        if (submitButton) {
            submitButton.disabled = true;

            submitButton.classList.add(
                "cursor-not-allowed",
                "opacity-70"
            );
        }

        if (submitLabel) {
            submitLabel.textContent = "Agendando...";
        }


        try {
            const formData = new FormData(form);

            const response = await fetch(
                form.action || agendaUrl,
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


            // =================================================
            // SUCESSO
            // =================================================

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


            // =================================================
            // ERROS DE VALIDAÇÃO
            // =================================================

            if (
                response.status === 400 ||
                contentType.includes("text/html")
            ) {
                const html = await response.text();

                setBodyContent(html);

                const firstError = modalBody.querySelector(
                    "[role='alert']"
                );

                if (firstError) {
                    firstError.scrollIntoView({
                        behavior: "smooth",
                        block: "center",
                    });
                }

                const firstInvalidField =
                    modalBody.querySelector(
                        "[aria-invalid='true']"
                    );

                if (firstInvalidField) {
                    firstInvalidField.focus();
                } else {
                    focusFirstField();
                }

                return;
            }


            throw new Error(
                `Erro ao agendar compromisso: ${response.status}`
            );

        } catch (error) {
            console.error(
                "Erro ao agendar compromisso:",
                error
            );

            showError();

        } finally {
            isSubmitting = false;

            /*
             * Em erro de validação o backend substitui o
             * formulário pelo novo HTML. Portanto, só restauramos
             * este botão se o formulário original ainda existir.
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
                        originalLabel;
                }
            }
        }
    }


    // =========================================================
    // CLIQUES
    // =========================================================

    document.addEventListener(
        "click",
        (event) => {

            // -------------------------------------------------
            // ABRIR
            // -------------------------------------------------

            const trigger = event.target.closest(
                "[data-agenda-modal-open]"
            );

            if (trigger) {
                const url =
                    trigger.dataset.agendaUrl ||
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


            // -------------------------------------------------
            // FECHAR
            // -------------------------------------------------

            const closeButton = event.target.closest(
                "[data-agenda-modal-close]"
            );

            if (
                closeButton &&
                !modal.classList.contains("hidden")
            ) {
                event.preventDefault();

                closeModal();

                return;
            }


            // -------------------------------------------------
            // TENTAR NOVAMENTE
            // -------------------------------------------------

            const retryButton = event.target.closest(
                "[data-agenda-modal-retry]"
            );

            if (
                retryButton &&
                !modal.classList.contains("hidden")
            ) {
                event.preventDefault();

                loadForm();
            }
        }
    );


    // =========================================================
    // SUBMIT
    // =========================================================

    document.addEventListener(
        "submit",
        (event) => {

            const form = event.target.closest(
                "#agenda-create-form"
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
        }
    );


    // =========================================================
    // BACKDROP
    // =========================================================

    if (backdrop) {
        backdrop.addEventListener(
            "click",
            () => {
                closeModal();
            }
        );
    }


    // =========================================================
    // TECLADO
    // =========================================================

    document.addEventListener(
        "keydown",
        (event) => {

            if (modal.classList.contains("hidden")) {
                return;
            }


            // -------------------------------------------------
            // ESC
            // -------------------------------------------------

            if (event.key === "Escape") {
                event.preventDefault();

                closeModal();

                return;
            }


            // -------------------------------------------------
            // TRAP DE FOCO
            // -------------------------------------------------

            if (event.key !== "Tab") {
                return;
            }

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
    );


    // =========================================================
    // CACHE / VOLTAR DO NAVEGADOR
    // =========================================================

    window.addEventListener(
        "pageshow",
        () => {

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

            agendaUrl = "";
            triggerElement = null;
            isSubmitting = false;
        }
    );
})();