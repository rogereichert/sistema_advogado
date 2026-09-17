"use strict";


/* =============================================================
   CLIENT MODAL
   -------------------------------------------------------------
   Responsável por:

   - abrir modal
   - fechar modal
   - carregar formulário via AJAX
   - criar cliente
   - editar cliente
   - enviar formulário via AJAX
   - renderizar erros de validação
   - reinicializar comportamento do formulário
   - controlar scroll da página
   - controlar foco e acessibilidade
============================================================= */

(function () {

    /* =========================================================
       ELEMENTOS PRINCIPAIS
    ========================================================== */

    const modal = document.getElementById("client-modal");
    const backdrop = document.getElementById("client-modal-backdrop");
    const modalScroll = document.getElementById("client-modal-scroll");
    const modalPanel = document.getElementById("client-modal-panel");
    const modalContent = document.getElementById("client-modal-content");
    const modalTitle = document.getElementById("client-modal-title");
    const closeButton = document.getElementById("close-client-modal");

    const createButton = document.getElementById(
        "open-create-client-modal"
    );

    const config = document.getElementById(
        "client-list-config"
    );


    /* =========================================================
       GUARD
       ---------------------------------------------------------
       Se este arquivo for carregado acidentalmente em outra
       página, não deve gerar erros.
    ========================================================== */

    if (
        !modal
        || !modalContent
        || !modalTitle
        || !config
    ) {
        return;
    }


    /* =========================================================
       CONFIGURAÇÃO
    ========================================================== */

    const createUrl = config.dataset.createUrl || "";

    const editUrlTemplate = (
        config.dataset.editUrlTemplate || ""
    );

    const editUrlSentinel = "999999999";


    /* =========================================================
       ESTADO
    ========================================================== */

    let currentUrl = null;

    let lastFocusedElement = null;

    let requestController = null;

    let isSubmitting = false;

    let bodyScrollY = 0;


    /* =========================================================
       UTILITÁRIOS
    ========================================================== */

    function isModalOpen() {

        return !modal.classList.contains("hidden");

    }


    function getEditUrl(clientId) {

        if (!editUrlTemplate) {
            return "";
        }

        return editUrlTemplate.replace(
            editUrlSentinel,
            String(clientId)
        );

    }


    function escapeHtml(value) {

        return String(value || "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");

    }


    /* =========================================================
       SCROLL DA PÁGINA
       ---------------------------------------------------------
       O modal possui sua própria camada rolável.

       Enquanto ele estiver aberto, travamos a página que está
       ao fundo sem perder a posição atual do usuário.
    ========================================================== */

    function lockBodyScroll() {

        bodyScrollY = window.scrollY;

        document.body.style.position = "fixed";
        document.body.style.top = `-${bodyScrollY}px`;
        document.body.style.left = "0";
        document.body.style.right = "0";
        document.body.style.width = "100%";

    }


    function unlockBodyScroll() {

        document.body.style.position = "";
        document.body.style.top = "";
        document.body.style.left = "";
        document.body.style.right = "";
        document.body.style.width = "";

        window.scrollTo({
            top: bodyScrollY,
            left: 0,
            behavior: "instant",
        });

    }


    /* =========================================================
       LOADING
    ========================================================== */

    function loadingHtml() {

        return `
            <div
                class="flex min-h-[320px] items-center justify-center px-6 py-12"
                role="status"
                aria-live="polite"
            >
                <div class="text-center">

                    <div
                        class="mx-auto flex h-12 w-12 items-center justify-center rounded-xl border border-brand-100 bg-brand-50 text-brand-700"
                    >
                        <svg
                            class="h-5 w-5 animate-spin"
                            xmlns="http://www.w3.org/2000/svg"
                            fill="none"
                            viewBox="0 0 24 24"
                            aria-hidden="true"
                        >
                            <circle
                                class="opacity-25"
                                cx="12"
                                cy="12"
                                r="9"
                                stroke="currentColor"
                                stroke-width="3"
                            ></circle>

                            <path
                                class="opacity-75"
                                fill="currentColor"
                                d="M12 3a9 9 0 0 1 9 9h-3a6 6 0 0 0-6-6V3Z"
                            ></path>
                        </svg>
                    </div>

                    <p
                        class="mt-4 text-sm font-semibold text-brand-950"
                    >
                        Carregando cadastro...
                    </p>

                    <p
                        class="mt-1 text-xs text-slate-500"
                    >
                        Aguarde um instante.
                    </p>

                </div>
            </div>
        `;

    }


    /* =========================================================
       ERRO DE CARREGAMENTO
    ========================================================== */

    function errorHtml(
        message = "Não foi possível carregar o cadastro."
    ) {

        return `
            <div
                class="flex min-h-[320px] items-center justify-center px-6 py-12"
                role="alert"
            >
                <div class="max-w-md text-center">

                    <div
                        class="mx-auto flex h-12 w-12 items-center justify-center rounded-xl border border-red-100 bg-red-50 text-red-600"
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
                                d="M12 9v4.5m0 3h.008v.008H12v-.008Z"
                            />

                            <path
                                stroke-linecap="round"
                                stroke-linejoin="round"
                                d="M10.03 3.659 1.91 17.75A1.5 1.5 0 0 0 3.21 20h17.58a1.5 1.5 0 0 0 1.3-2.25L13.97 3.659a1.5 1.5 0 0 0-2.94 0Z"
                            />
                        </svg>
                    </div>

                    <h3
                        class="mt-4 text-base font-semibold text-brand-950"
                    >
                        Não foi possível abrir o cadastro
                    </h3>

                    <p
                        class="mt-2 text-sm leading-6 text-slate-500"
                    >
                        ${escapeHtml(message)}
                    </p>

                    <button
                        type="button"
                        data-client-modal-retry
                        class="mt-5 inline-flex min-h-10 cursor-pointer items-center justify-center rounded-xl border border-brand-200 bg-brand-50 px-4 text-sm font-semibold text-brand-800 transition hover:bg-brand-100 focus:outline-none focus:ring-4 focus:ring-brand-100"
                    >
                        Tentar novamente
                    </button>

                </div>
            </div>
        `;

    }


    /* =========================================================
       ABRIR E FECHAR ESTRUTURA DO MODAL
    ========================================================== */

    function showModal() {

        if (isModalOpen()) {
            return;
        }

        lastFocusedElement = document.activeElement;

        lockBodyScroll();

        modal.classList.remove("hidden");

        /*
         * Reiniciamos a posição de scroll do modal sempre que
         * ele é aberto.
         */

        if (modalScroll) {
            modalScroll.scrollTop = 0;
        }

    }


    function closeModal() {

        if (!isModalOpen()) {
            return;
        }


        /*
         * Cancela eventual GET ainda em andamento.
         */

        if (requestController) {
            requestController.abort();
            requestController = null;
        }


        currentUrl = null;
        isSubmitting = false;

        modal.classList.add("hidden");

        /*
         * Limpamos o HTML para impedir IDs duplicados e
         * listeners antigos na próxima abertura.
         */

        modalContent.innerHTML = "";

        unlockBodyScroll();


        /*
         * Devolve o foco ao elemento que abriu o modal.
         */

        if (
            lastFocusedElement
            && typeof lastFocusedElement.focus === "function"
            && document.contains(lastFocusedElement)
        ) {
            lastFocusedElement.focus();
        }

        lastFocusedElement = null;

    }


    /* =========================================================
       INICIALIZA O CLIENT-FORM.JS
       ---------------------------------------------------------
       O formulário entra no DOM dinamicamente.

       Se o client-form.js expuser uma API global, chamamos essa
       API depois de inserir o HTML.

       Isso preserva máscaras, CEP/ViaCEP e demais comportamentos
       que já pertencem ao formulário.
    ========================================================== */

    function initializeClientForm() {

        if (!window.ClientForm) {
            return;
        }


        /*
         * Suportamos as duas assinaturas mais comuns sem
         * duplicar a lógica do formulário neste arquivo.
         */

        if (
            typeof window.ClientForm.init === "function"
        ) {

            window.ClientForm.init(
                modalContent
            );

            return;
        }


        if (
            typeof window.ClientForm.initialize === "function"
        ) {

            window.ClientForm.initialize(
                modalContent
            );

        }

    }


    /* =========================================================
       FOCO INICIAL DO FORMULÁRIO
    ========================================================== */

    function focusFirstFormField() {

        const autofocusElement = modalContent.querySelector(
            "[autofocus]"
        );

        const firstField = modalContent.querySelector(
            "input:not([type='hidden']):not([disabled]), " +
            "select:not([disabled]), " +
            "textarea:not([disabled])"
        );

        const target = (
            autofocusElement
            || firstField
        );


        if (!target) {
            return;
        }


        /*
         * Pequeno atraso para garantir que o navegador terminou
         * de inserir/renderizar o formulário.
         */

        window.requestAnimationFrame(function () {

            target.focus({
                preventScroll: true,
            });

        });

    }


    /* =========================================================
       FOCO NO PRIMEIRO ERRO DE VALIDAÇÃO
    ========================================================== */

    function focusFirstInvalidField() {

        const invalidField = modalContent.querySelector(
            "[aria-invalid='true'], " +
            ".border-red-300, " +
            ".border-red-400, " +
            ".border-red-500"
        );


        if (!invalidField) {
            return;
        }


        window.requestAnimationFrame(function () {

            invalidField.focus({
                preventScroll: true,
            });

            invalidField.scrollIntoView({
                behavior: "smooth",
                block: "center",
            });

        });

    }


    /* =========================================================
       BOTÃO DE SUBMIT
    ========================================================== */

    function setSubmitState(
        form,
        submitting
    ) {

        const submitButton = form.querySelector(
            "[type='submit']"
        );

        const submitLabel = form.querySelector(
            "[data-submit-label]"
        );


        if (!submitButton) {
            return;
        }


        if (submitting) {

            submitButton.disabled = true;

            submitButton.setAttribute(
                "aria-busy",
                "true"
            );


            if (submitLabel) {

                submitLabel.dataset.originalLabel = (
                    submitLabel.textContent.trim()
                );

                submitLabel.textContent = "Salvando...";

            }

            return;

        }


        submitButton.disabled = false;

        submitButton.removeAttribute(
            "aria-busy"
        );


        if (
            submitLabel
            && submitLabel.dataset.originalLabel
        ) {

            submitLabel.textContent = (
                submitLabel.dataset.originalLabel
            );

            delete submitLabel.dataset.originalLabel;

        }

    }


    /* =========================================================
       BIND DO FORMULÁRIO
    ========================================================== */

    function bindClientForm() {

        const form = modalContent.querySelector(
            "#client-form"
        );


        if (!form) {
            return;
        }


        /*
         * Proteção contra bind duplicado.
         */

        if (form.dataset.ajaxBound === "true") {
            return;
        }

        form.dataset.ajaxBound = "true";


        form.addEventListener(
            "submit",
            handleFormSubmit
        );

    }


    /* =========================================================
       HTML DO FORMULÁRIO RECEBIDO DO BACKEND
    ========================================================== */

    function renderFormHtml(
        html,
        options = {}
    ) {

        const {
            focusFirst = false,
            focusError = false,
        } = options;


        modalContent.innerHTML = html;


        /*
         * Primeiro inicializamos os comportamentos internos do
         * formulário; depois adicionamos nosso submit AJAX.
         */

        initializeClientForm();

        bindClientForm();


        if (focusError) {

            focusFirstInvalidField();

            return;

        }


        if (focusFirst) {

            focusFirstFormField();

        }

    }


    /* =========================================================
       SUBMIT AJAX
    ========================================================== */

    async function handleFormSubmit(event) {

        event.preventDefault();


        const form = event.currentTarget;


        if (
            isSubmitting
            || !currentUrl
        ) {
            return;
        }


        isSubmitting = true;

        setSubmitState(
            form,
            true
        );


        try {

            const response = await fetch(
                currentUrl,
                {
                    method: "POST",

                    body: new FormData(form),

                    headers: {
                        "X-Requested-With": "XMLHttpRequest",
                    },

                    credentials: "same-origin",
                }
            );


            /* -------------------------------------------------
               SUCESSO

               Nossa view AJAX retorna JSON quando o formulário
               é salvo corretamente.
            -------------------------------------------------- */

            const contentType = (
                response.headers.get("content-type") || ""
            );


            if (
                response.ok
                && contentType.includes(
                    "application/json"
                )
            ) {

                const data = await response.json();


                if (data.success) {

                    window.location.reload();

                    return;

                }

            }


            /* -------------------------------------------------
               ERRO DE VALIDAÇÃO

               A view devolve novamente o _client_form.html,
               agora contendo os erros do Django.
            -------------------------------------------------- */

            const html = await response.text();


            if (html.trim()) {

                renderFormHtml(
                    html,
                    {
                        focusError: true,
                    }
                );

                return;

            }


            throw new Error(
                "O servidor não retornou uma resposta válida."
            );

        } catch (error) {

            console.error(
                "Erro ao salvar cliente:",
                error
            );


            /*
             * Se o formulário ainda estiver no DOM, mantemos os
             * dados preenchidos e mostramos um aviso acima dele.
             */

            if (document.contains(form)) {

                showFormRequestError(
                    form,
                    "Não foi possível salvar o cliente. Verifique sua conexão e tente novamente."
                );

            } else {

                modalContent.innerHTML = errorHtml(
                    "Não foi possível salvar o cliente."
                );

                bindRetryButton();

            }

        } finally {

            isSubmitting = false;


            /*
             * O backend pode ter substituído o formulário por
             * outro HTML contendo erros.

             * Só restauramos o botão se este formulário original
             * ainda existir no DOM.
             */

            if (document.contains(form)) {

                setSubmitState(
                    form,
                    false
                );

            }

        }

    }


    /* =========================================================
       ERRO DE REQUISIÇÃO DURANTE O SUBMIT
    ========================================================== */

    function showFormRequestError(
        form,
        message
    ) {

        const previousError = form.querySelector(
            "[data-client-request-error]"
        );


        if (previousError) {
            previousError.remove();
        }


        const alert = document.createElement(
            "div"
        );

        alert.dataset.clientRequestError = "true";

        alert.setAttribute(
            "role",
            "alert"
        );

        alert.className = (
            "mx-5 mt-5 rounded-xl border border-red-200 " +
            "bg-red-50 px-4 py-3 text-sm text-red-700 " +
            "sm:mx-6"
        );

        alert.textContent = message;


        form.prepend(
            alert
        );


        alert.scrollIntoView({
            behavior: "smooth",
            block: "center",
        });

    }


    /* =========================================================
       CARREGA FORMULÁRIO
    ========================================================== */

    async function loadForm(
        url,
        title
    ) {

        if (!url) {
            return;
        }


        /*
         * Se houver uma requisição GET anterior ainda em
         * andamento, cancelamos antes de iniciar a nova.
         */

        if (requestController) {
            requestController.abort();
        }


        requestController = new AbortController();

        currentUrl = url;

        modalTitle.textContent = title;

        modalContent.innerHTML = loadingHtml();

        showModal();


        try {

            const response = await fetch(
                url,
                {
                    method: "GET",

                    headers: {
                        "X-Requested-With": "XMLHttpRequest",
                    },

                    credentials: "same-origin",

                    signal: requestController.signal,
                }
            );


            if (!response.ok) {

                throw new Error(
                    `Erro HTTP ${response.status}`
                );

            }


            const html = await response.text();


            if (!html.trim()) {

                throw new Error(
                    "O formulário retornado está vazio."
                );

            }


            /*
             * O usuário pode ter fechado o modal enquanto a
             * requisição estava em andamento.
             */

            if (!isModalOpen()) {
                return;
            }


            renderFormHtml(
                html,
                {
                    focusFirst: true,
                }
            );


        } catch (error) {

            /*
             * AbortError é esperado quando:
             *
             * - o usuário fecha o modal;
             * - outra requisição substitui a anterior.
             */

            if (
                error.name === "AbortError"
            ) {
                return;
            }


            console.error(
                "Erro ao carregar formulário de cliente:",
                error
            );


            if (!isModalOpen()) {
                return;
            }


            modalContent.innerHTML = errorHtml();

            bindRetryButton();

        } finally {

            requestController = null;

        }

    }


    /* =========================================================
       TENTAR NOVAMENTE
    ========================================================== */

    function bindRetryButton() {

        const retryButton = modalContent.querySelector(
            "[data-client-modal-retry]"
        );


        if (
            !retryButton
            || !currentUrl
        ) {
            return;
        }


        retryButton.addEventListener(
            "click",
            function () {

                loadForm(
                    currentUrl,
                    modalTitle.textContent.trim()
                );

            },
            {
                once: true,
            }
        );

    }


    /* =========================================================
       NOVO CLIENTE
    ========================================================== */

    function openCreateModal() {

        loadForm(
            createUrl,
            "Novo cliente"
        );

    }


    /* =========================================================
       EDITAR CLIENTE
    ========================================================== */

    function openEditModal(
        clientId,
        clientName
    ) {

        if (!clientId) {
            return;
        }


        const url = getEditUrl(
            clientId
        );


        const title = clientName
            ? `Editar ${clientName}`
            : "Editar cliente";


        loadForm(
            url,
            title
        );

    }


    /* =========================================================
       EVENTO — BOTÃO PRINCIPAL "NOVO CLIENTE"
    ========================================================== */

    if (createButton) {

        createButton.addEventListener(
            "click",
            openCreateModal
        );

    }


    /* =========================================================
       EVENTO — OUTROS BOTÕES DE CADASTRO
       ---------------------------------------------------------
       Exemplo:
       estado vazio "Cadastrar primeiro cliente".
    ========================================================== */

    document.addEventListener(
        "click",
        function (event) {

            const trigger = event.target.closest(
                "[data-open-create-client]"
            );


            if (!trigger) {
                return;
            }


            event.preventDefault();

            openCreateModal();

        }
    );


    /* =========================================================
       EVENTO — EDITAR CLIENTE
       ---------------------------------------------------------
       Delegação de eventos permite que o mesmo código funcione
       para tabela desktop e listagem mobile.
    ========================================================== */

    document.addEventListener(
        "click",
        function (event) {

            const editButton = event.target.closest(
                ".edit-client-button"
            );


            if (!editButton) {
                return;
            }


            event.preventDefault();


            openEditModal(
                editButton.dataset.clientId,
                editButton.dataset.clientName
            );

        }
    );


    /* =========================================================
       FECHAR PELO BOTÃO X
    ========================================================== */

    if (closeButton) {

        closeButton.addEventListener(
            "click",
            closeModal
        );

    }


    /* =========================================================
       FECHAR PELO BACKDROP
    ========================================================== */

    if (backdrop) {

        backdrop.addEventListener(
            "click",
            closeModal
        );

    }


    /* =========================================================
       CANCELAR PELO _client_form.html
       ---------------------------------------------------------
       O formulário pode disparar:

       client-form:cancel

       Assim o formulário não precisa conhecer a implementação
       interna do modal.
    ========================================================== */

    document.addEventListener(
        "client-form:cancel",
        function () {

            if (isModalOpen()) {
                closeModal();
            }

        }
    );


    /* =========================================================
       ESCAPE
    ========================================================== */

    document.addEventListener(
        "keydown",
        function (event) {

            if (
                event.key !== "Escape"
                || !isModalOpen()
            ) {
                return;
            }


            event.preventDefault();

            closeModal();

        }
    );


    /* =========================================================
       TRAP DE FOCO
       ---------------------------------------------------------
       Enquanto o modal estiver aberto, Tab permanece dentro
       dele.
    ========================================================== */

    document.addEventListener(
        "keydown",
        function (event) {

            if (
                event.key !== "Tab"
                || !isModalOpen()
            ) {
                return;
            }


            const focusableElements = Array.from(
                modal.querySelectorAll(
                    [
                        "a[href]",
                        "button:not([disabled])",
                        "input:not([disabled]):not([type='hidden'])",
                        "select:not([disabled])",
                        "textarea:not([disabled])",
                        "[tabindex]:not([tabindex='-1'])",
                    ].join(",")
                )
            ).filter(function (element) {

                return (
                    element.offsetWidth > 0
                    || element.offsetHeight > 0
                    || element === document.activeElement
                );

            });


            if (!focusableElements.length) {
                return;
            }


            const firstElement = (
                focusableElements[0]
            );

            const lastElement = (
                focusableElements[
                    focusableElements.length - 1
                ]
            );


            if (
                event.shiftKey
                && document.activeElement === firstElement
            ) {

                event.preventDefault();

                lastElement.focus();

                return;

            }


            if (
                !event.shiftKey
                && document.activeElement === lastElement
            ) {

                event.preventDefault();

                firstElement.focus();

            }

        }
    );


    /* =========================================================
       API PÚBLICA
       ---------------------------------------------------------
       Não é necessária para o funcionamento normal da página,
       mas deixa o componente reutilizável por outras partes do
       sistema no futuro.
    ========================================================== */

    window.ClientModal = {

        openCreate: openCreateModal,

        openEdit: openEditModal,

        close: closeModal,

        isOpen: isModalOpen,

    };

})();