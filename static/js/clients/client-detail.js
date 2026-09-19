(() => {
    "use strict";

    const config = document.getElementById("client-detail-config");

    const modal = document.getElementById("edit-client-modal");
    const modalBackdrop = document.getElementById(
        "edit-client-modal-backdrop"
    );
    const modalPanel = document.getElementById(
        "edit-client-modal-panel"
    );
    const modalContent = document.getElementById(
        "edit-client-modal-content"
    );

    const openButton = document.getElementById(
        "open-edit-client-modal"
    );
    const closeButton = document.getElementById(
        "close-edit-client-modal"
    );

    if (
        !config ||
        !modal ||
        !modalContent ||
        !openButton ||
        !closeButton
    ) {
        return;
    }

    const editUrl = config.dataset.editUrl;

    let lastFocusedElement = null;
    let requestController = null;


    // =========================================================
    // ESTADOS VISUAIS
    // =========================================================

    function renderLoading() {
        modalContent.innerHTML = `
            <div
                id="edit-client-modal-loading"
                class="flex min-h-[300px] items-center justify-center px-6 py-16"
            >
                <div class="text-center">

                    <div
                        class="relative mx-auto h-10 w-10"
                        aria-hidden="true"
                    >
                        <div
                            class="absolute inset-0 rounded-full border-[3px] border-brand-100"
                        ></div>

                        <div
                            class="absolute inset-0 animate-spin rounded-full border-[3px] border-transparent border-t-brand-700"
                        ></div>
                    </div>

                    <p
                        class="mt-4 text-sm font-semibold text-brand-950"
                    >
                        Carregando cadastro
                    </p>

                    <p
                        class="mt-1 text-xs text-slate-500"
                    >
                        Aguarde enquanto preparamos os dados do cliente.
                    </p>

                </div>
            </div>
        `;
    }


    function renderError(
        message = "Não foi possível carregar o cadastro."
    ) {
        modalContent.innerHTML = `
            <div
                class="flex min-h-[300px] items-center justify-center px-6 py-16"
            >
                <div class="max-w-md text-center">

                    <div
                        class="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl border border-red-100 bg-red-50 text-red-600"
                        aria-hidden="true"
                    >
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke-width="1.8"
                            stroke="currentColor"
                            class="h-5 w-5"
                        >
                            <path
                                stroke-linecap="round"
                                stroke-linejoin="round"
                                d="M12 9v3.75m9.303 3.376c.866 1.5-.217 3.374-1.948 3.374H4.645c-1.73 0-2.813-1.874-1.948-3.374L10.052 3.38c.865-1.5 3.03-1.5 3.896 0l7.355 12.746ZM12 16.5h.008v.008H12V16.5Z"
                            />
                        </svg>
                    </div>

                    <p
                        class="mt-4 text-sm font-semibold text-brand-950"
                    >
                        ${message}
                    </p>

                    <button
                        type="button"
                        data-retry-edit-client
                        class="mt-4 inline-flex min-h-10 cursor-pointer items-center justify-center rounded-xl bg-brand-900 px-4 text-sm font-semibold text-white transition hover:bg-brand-800 focus:outline-none focus:ring-4 focus:ring-brand-200"
                    >
                        Tentar novamente
                    </button>

                </div>
            </div>
        `;

        const retryButton = modalContent.querySelector(
            "[data-retry-edit-client]"
        );

        retryButton?.addEventListener("click", loadForm);
    }


    // =========================================================
    // ABRIR / FECHAR
    // =========================================================

    function openModal() {
        lastFocusedElement = document.activeElement;

        modal.classList.remove("hidden");
        modal.setAttribute("aria-hidden", "false");

        document.body.classList.add("overflow-hidden");

        renderLoading();

        window.requestAnimationFrame(() => {
            modalPanel?.focus();
        });

        loadForm();
    }


    function closeModal() {
        if (modal.classList.contains("hidden")) {
            return;
        }

        if (requestController) {
            requestController.abort();
            requestController = null;
        }

        modal.classList.add("hidden");
        modal.setAttribute("aria-hidden", "true");

        document.body.classList.remove("overflow-hidden");

        if (
            lastFocusedElement &&
            typeof lastFocusedElement.focus === "function"
        ) {
            lastFocusedElement.focus();
        }

        lastFocusedElement = null;
    }


    // =========================================================
    // CARREGAR FORMULÁRIO
    // =========================================================

    async function loadForm() {
        if (!editUrl) {
            renderError("A URL de edição não foi encontrada.");
            return;
        }

        if (requestController) {
            requestController.abort();
        }

        requestController = new AbortController();

        renderLoading();

        try {
            const response = await fetch(editUrl, {
                method: "GET",

                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                },

                credentials: "same-origin",

                signal: requestController.signal,
            });

            if (!response.ok) {
                throw new Error(
                    `Erro HTTP ${response.status}`
                );
            }

            const html = await response.text();

            modalContent.innerHTML = html;

            initializeLoadedForm();

        } catch (error) {
            if (error.name === "AbortError") {
                return;
            }

            console.error(
                "Erro ao carregar formulário do cliente:",
                error
            );

            renderError();

        } finally {
            requestController = null;
        }
    }


    // =========================================================
    // FORMULÁRIO CARREGADO
    // =========================================================

    function initializeLoadedForm() {
        const form =
            modalContent.querySelector("[data-client-form]") ||
            modalContent.querySelector("#client-form") ||
            modalContent.querySelector("form");

        if (!form) {
            renderError(
                "O formulário de edição não foi encontrado."
            );
            return;
        }


        // -----------------------------------------------------
        // Inicializa comportamentos específicos do formulário
        // -----------------------------------------------------

        if (
            window.ClientForm &&
            typeof window.ClientForm.init === "function"
        ) {
            window.ClientForm.init(form);
        }


        // -----------------------------------------------------
        // Botões de cancelamento internos
        // -----------------------------------------------------

        form
            .querySelectorAll(
                '[data-client-form-cancel], [data-cancel-client-form]'
            )
            .forEach((button) => {
                button.addEventListener(
                    "click",
                    closeModal
                );
            });


        // -----------------------------------------------------
        // Foco inicial
        // -----------------------------------------------------

        const autofocusElement =
            form.querySelector("[autofocus]") ||
            form.querySelector(
                "input:not([type='hidden']):not([disabled]), select:not([disabled]), textarea:not([disabled])"
            );

        window.requestAnimationFrame(() => {
            autofocusElement?.focus();
        });


        // -----------------------------------------------------
        // POST AJAX
        // -----------------------------------------------------

        form.addEventListener("submit", submitForm);
    }


    // =========================================================
    // ENVIAR FORMULÁRIO
    // =========================================================

    async function submitForm(event) {
        event.preventDefault();

        const form = event.currentTarget;

        if (requestController) {
            requestController.abort();
        }

        requestController = new AbortController();

        const submitButton = form.querySelector(
            'button[type="submit"], input[type="submit"]'
        );

        const originalButtonHTML =
            submitButton?.innerHTML ?? null;

        if (submitButton) {
            submitButton.disabled = true;

            if (submitButton.tagName === "BUTTON") {
                submitButton.innerHTML = `
                    <span
                        class="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white"
                        aria-hidden="true"
                    ></span>

                    <span>Salvando...</span>
                `;
            }
        }

        try {
            const response = await fetch(
                editUrl,
                {
                    method: "POST",

                    body: new FormData(form),

                    headers: {
                        "X-Requested-With":
                            "XMLHttpRequest",
                    },

                    credentials: "same-origin",

                    signal: requestController.signal,
                }
            );


            // -------------------------------------------------
            // SUCESSO
            // -------------------------------------------------

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


            // -------------------------------------------------
            // ERROS DE VALIDAÇÃO
            // -------------------------------------------------

            const html = await response.text();

            modalContent.innerHTML = html;

            initializeLoadedForm();

            const firstError =
                modalContent.querySelector(
                    "[aria-invalid='true']"
                ) ||
                modalContent.querySelector(
                    ".errorlist"
                ) ||
                modalContent.querySelector(
                    ".text-red-600"
                );

            firstError?.scrollIntoView({
                behavior: "smooth",
                block: "center",
            });

        } catch (error) {
            if (error.name === "AbortError") {
                return;
            }

            console.error(
                "Erro ao salvar cliente:",
                error
            );

            renderError(
                "Não foi possível salvar as alterações."
            );

        } finally {
            requestController = null;

            if (
                submitButton &&
                document.body.contains(submitButton)
            ) {
                submitButton.disabled = false;

                if (
                    submitButton.tagName === "BUTTON" &&
                    originalButtonHTML !== null
                ) {
                    submitButton.innerHTML =
                        originalButtonHTML;
                }
            }
        }
    }


    // =========================================================
    // EVENTOS
    // =========================================================

    openButton.addEventListener(
        "click",
        openModal
    );


    closeButton.addEventListener(
        "click",
        closeModal
    );


    modalBackdrop?.addEventListener(
        "click",
        closeModal
    );


    modal.addEventListener(
        "client-form:cancel",
        closeModal
    );


    document.addEventListener("keydown", (event) => {
        if (
            event.key === "Escape" &&
            !modal.classList.contains("hidden")
        ) {
            closeModal();
        }
    });


    // =========================================================
    // API PÚBLICA
    // =========================================================

    window.ClientDetail = {
        openEditModal: openModal,
        closeEditModal: closeModal,
        reloadEditForm: loadForm,
    };
})();