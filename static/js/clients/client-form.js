/**
 * =============================================================
 * CLIENT FORM
 * =============================================================
 *
 * Comportamentos compartilhados do formulário de clientes:
 *
 * - Máscara visual de CPF
 * - Máscara visual de CEP
 * - Máscara visual de telefone
 * - Normalização da UF
 * - Consulta de endereço pelo ViaCEP
 * - Estado visual da consulta de CEP
 * - Evento de cancelamento
 *
 * O módulo funciona tanto:
 *
 * 1. na página completa de cadastro/edição;
 * 2. em formulários carregados dinamicamente dentro de modais.
 *
 * =============================================================
 */

(() => {
    "use strict";


    /**
     * ---------------------------------------------------------
     * SELETORES
     * ---------------------------------------------------------
     */

    const SELECTORS = {
        form: "[data-client-form]",

        cpf: "#id_cpf",
        cep: "#id_cep",
        telefone: "#id_telefone",
        uf: "#id_uf",

        logradouro: "#id_logradouro",
        numero: "#id_numero",
        bairro: "#id_bairro",
        cidade: "#id_cidade",

        searchCep: "[data-search-cep]",
        cepStatus: "[data-cep-status]",

        cancel: "[data-client-form-cancel]",
    };


    /**
     * ---------------------------------------------------------
     * UTILITÁRIOS
     * ---------------------------------------------------------
     */

    const onlyDigits = (value) => {
        return String(value ?? "")
            .replace(/\D/g, "");
    };


    const normalizeWhitespace = (value) => {
        return String(value ?? "")
            .replace(/\s+/g, " ")
            .trim();
    };


    /**
     * ---------------------------------------------------------
     * CPF
     * ---------------------------------------------------------
     */

    const formatCpf = (value) => {
        const digits = onlyDigits(value)
            .slice(0, 11);

        if (digits.length <= 3) {
            return digits;
        }

        if (digits.length <= 6) {
            return (
                `${digits.slice(0, 3)}.` +
                digits.slice(3)
            );
        }

        if (digits.length <= 9) {
            return (
                `${digits.slice(0, 3)}.` +
                `${digits.slice(3, 6)}.` +
                digits.slice(6)
            );
        }

        return (
            `${digits.slice(0, 3)}.` +
            `${digits.slice(3, 6)}.` +
            `${digits.slice(6, 9)}-` +
            digits.slice(9, 11)
        );
    };


    /**
     * ---------------------------------------------------------
     * CEP
     * ---------------------------------------------------------
     */

    const formatCep = (value) => {
        const digits = onlyDigits(value)
            .slice(0, 8);

        if (digits.length <= 5) {
            return digits;
        }

        return (
            `${digits.slice(0, 5)}-` +
            digits.slice(5)
        );
    };


    /**
     * ---------------------------------------------------------
     * TELEFONE
     * ---------------------------------------------------------
     */

    const formatPhone = (value) => {
        const digits = onlyDigits(value)
            .slice(0, 11);

        if (!digits) {
            return "";
        }

        if (digits.length <= 2) {
            return `(${digits}`;
        }

        if (digits.length <= 6) {
            return (
                `(${digits.slice(0, 2)}) ` +
                digits.slice(2)
            );
        }

        if (digits.length <= 10) {
            return (
                `(${digits.slice(0, 2)}) ` +
                `${digits.slice(2, 6)}-` +
                digits.slice(6)
            );
        }

        return (
            `(${digits.slice(0, 2)}) ` +
            `${digits.slice(2, 7)}-` +
            digits.slice(7)
        );
    };


    /**
     * ---------------------------------------------------------
     * STATUS DO CEP
     * ---------------------------------------------------------
     */

    const setCepStatus = (
        element,
        message,
        type = "neutral"
    ) => {
        if (!element) {
            return;
        }

        element.textContent = message;

        element.classList.remove(
            "hidden",
            "text-slate-500",
            "text-red-600",
            "text-emerald-600"
        );

        if (type === "error") {
            element.classList.add(
                "text-red-600"
            );

            return;
        }

        if (type === "success") {
            element.classList.add(
                "text-emerald-600"
            );

            return;
        }

        element.classList.add(
            "text-slate-500"
        );
    };


    const clearCepStatus = (element) => {
        if (!element) {
            return;
        }

        element.textContent = "";

        element.classList.add(
            "hidden"
        );

        element.classList.remove(
            "text-red-600",
            "text-emerald-600"
        );

        element.classList.add(
            "text-slate-500"
        );
    };


    /**
     * ---------------------------------------------------------
     * INICIALIZA UM FORMULÁRIO
     * ---------------------------------------------------------
     */

    const initializeClientForm = (form) => {
        if (!(form instanceof HTMLFormElement)) {
            return;
        }

        if (form.dataset.clientFormInitialized === "true") {
            return;
        }

        form.dataset.clientFormInitialized = "true";


        /**
         * Campos
         */

        const cpfField =
            form.querySelector(
                SELECTORS.cpf
            );

        const cepField =
            form.querySelector(
                SELECTORS.cep
            );

        const phoneField =
            form.querySelector(
                SELECTORS.telefone
            );

        const ufField =
            form.querySelector(
                SELECTORS.uf
            );

        const streetField =
            form.querySelector(
                SELECTORS.logradouro
            );

        const numberField =
            form.querySelector(
                SELECTORS.numero
            );

        const districtField =
            form.querySelector(
                SELECTORS.bairro
            );

        const cityField =
            form.querySelector(
                SELECTORS.cidade
            );

        const searchCepButton =
            form.querySelector(
                SELECTORS.searchCep
            );

        const cepStatus =
            form.querySelector(
                SELECTORS.cepStatus
            );

        const cancelButton =
            form.querySelector(
                SELECTORS.cancel
            );


        /**
         * -----------------------------------------------------
         * CPF
         * -----------------------------------------------------
         */

        if (cpfField) {
            cpfField.value =
                formatCpf(cpfField.value);

            cpfField.addEventListener(
                "input",
                () => {
                    cpfField.value =
                        formatCpf(
                            cpfField.value
                        );
                }
            );
        }


        /**
         * -----------------------------------------------------
         * CEP
         * -----------------------------------------------------
         */

        if (cepField) {
            cepField.value =
                formatCep(cepField.value);

            cepField.addEventListener(
                "input",
                () => {
                    cepField.value =
                        formatCep(
                            cepField.value
                        );

                    clearCepStatus(
                        cepStatus
                    );
                }
            );
        }


        /**
         * -----------------------------------------------------
         * TELEFONE
         * -----------------------------------------------------
         */

        if (phoneField) {
            phoneField.value =
                formatPhone(
                    phoneField.value
                );

            phoneField.addEventListener(
                "input",
                () => {
                    phoneField.value =
                        formatPhone(
                            phoneField.value
                        );
                }
            );
        }


        /**
         * -----------------------------------------------------
         * UF
         * -----------------------------------------------------
         */

        if (ufField) {
            ufField.value =
                String(
                    ufField.value ?? ""
                )
                    .replace(
                        /[^a-zA-Z]/g,
                        ""
                    )
                    .slice(0, 2)
                    .toUpperCase();

            ufField.addEventListener(
                "input",
                () => {
                    ufField.value =
                        String(
                            ufField.value ?? ""
                        )
                            .replace(
                                /[^a-zA-Z]/g,
                                ""
                            )
                            .slice(0, 2)
                            .toUpperCase();
                }
            );
        }


        /**
         * -----------------------------------------------------
         * CONSULTA CEP
         * -----------------------------------------------------
         */

        const searchCep = async () => {
            if (!cepField) {
                return;
            }

            const cep =
                onlyDigits(
                    cepField.value
                );

            if (cep.length !== 8) {
                setCepStatus(
                    cepStatus,
                    "Informe um CEP com 8 dígitos.",
                    "error"
                );

                cepField.focus();

                return;
            }


            setCepStatus(
                cepStatus,
                "Consultando CEP..."
            );


            const originalButtonContent =
                searchCepButton
                    ? searchCepButton.innerHTML
                    : "";


            if (searchCepButton) {
                searchCepButton.disabled =
                    true;

                searchCepButton.innerHTML = `
                    <svg
                        class="h-4 w-4 animate-spin"
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
                            d="M4 12a8 8 0 0 1 8-8v4a4 4 0 0 0-4 4H4Z"
                        ></path>
                    </svg>

                    <span>
                        Buscando
                    </span>
                `;
            }


            try {
                const response =
                    await fetch(
                        `https://viacep.com.br/ws/${cep}/json/`,
                        {
                            method: "GET",

                            headers: {
                                "Accept":
                                    "application/json"
                            }
                        }
                    );


                if (!response.ok) {
                    throw new Error(
                        `ViaCEP respondeu com HTTP ${response.status}.`
                    );
                }


                const data =
                    await response.json();


                if (data.erro) {
                    setCepStatus(
                        cepStatus,
                        "CEP não encontrado. Confira os números informados.",
                        "error"
                    );

                    return;
                }


                if (
                    streetField &&
                    data.logradouro
                ) {
                    streetField.value =
                        normalizeWhitespace(
                            data.logradouro
                        );
                }


                if (
                    districtField &&
                    data.bairro
                ) {
                    districtField.value =
                        normalizeWhitespace(
                            data.bairro
                        );
                }


                if (
                    cityField &&
                    data.localidade
                ) {
                    cityField.value =
                        normalizeWhitespace(
                            data.localidade
                        );
                }


                if (
                    ufField &&
                    data.uf
                ) {
                    ufField.value =
                        String(data.uf)
                            .slice(0, 2)
                            .toUpperCase();
                }


                setCepStatus(
                    cepStatus,
                    "Endereço localizado e preenchido.",
                    "success"
                );


                if (numberField) {
                    numberField.focus();
                } else if (streetField) {
                    streetField.focus();
                }

            } catch (error) {
                console.error(
                    "[ClientForm] Erro ao consultar CEP:",
                    error
                );

                setCepStatus(
                    cepStatus,
                    "Não foi possível consultar o CEP agora. Preencha o endereço manualmente.",
                    "error"
                );

            } finally {
                if (searchCepButton) {
                    searchCepButton.disabled =
                        false;

                    searchCepButton.innerHTML =
                        originalButtonContent;
                }
            }
        };


        searchCepButton?.addEventListener(
            "click",
            searchCep
        );


        cepField?.addEventListener(
            "keydown",
            (event) => {
                if (event.key !== "Enter") {
                    return;
                }

                event.preventDefault();

                searchCep();
            }
        );


        /**
         * -----------------------------------------------------
         * CANCELAR
         * -----------------------------------------------------
         */

        cancelButton?.addEventListener(
            "click",
            () => {
                form.dispatchEvent(
                    new CustomEvent(
                        "client-form:cancel",
                        {
                            bubbles: true,

                            detail: {
                                form
                            }
                        }
                    )
                );
            }
        );


        /**
         * -----------------------------------------------------
         * EVENTO DE INICIALIZAÇÃO
         * -----------------------------------------------------
         *
         * Pode ser útil para o modal definir foco inicial
         * sem acoplar este módulo ao client_list.html.
         */

        form.dispatchEvent(
            new CustomEvent(
                "client-form:ready",
                {
                    bubbles: true,

                    detail: {
                        form
                    }
                }
            )
        );
    };


    /**
     * ---------------------------------------------------------
     * PROCURA FORMULÁRIOS EM UM ELEMENTO
     * ---------------------------------------------------------
     */

    const initializeWithin = (root) => {
        if (!root) {
            return;
        }


        if (
            root instanceof HTMLFormElement &&
            root.matches(
                SELECTORS.form
            )
        ) {
            initializeClientForm(root);
        }


        if (
            typeof root.querySelectorAll
            !== "function"
        ) {
            return;
        }


        root
            .querySelectorAll(
                SELECTORS.form
            )
            .forEach(
                initializeClientForm
            );
    };


    /**
     * ---------------------------------------------------------
     * FORMULÁRIOS EXISTENTES NA PÁGINA
     * ---------------------------------------------------------
     */

    const initializePage = () => {
        initializeWithin(document);
    };


    if (
        document.readyState === "loading"
    ) {
        document.addEventListener(
            "DOMContentLoaded",
            initializePage
        );
    } else {
        initializePage();
    }


    /**
     * ---------------------------------------------------------
     * FORMULÁRIOS INSERIDOS VIA AJAX
     * ---------------------------------------------------------
     *
     * O cadastro e a edição são carregados no modal através
     * de innerHTML.
     *
     * Scripts existentes dentro desse HTML não devem ser a
     * estratégia de inicialização.
     *
     * O MutationObserver detecta quando o formulário entra no
     * DOM e aplica os comportamentos automaticamente.
     * ---------------------------------------------------------
     */

    const observer =
        new MutationObserver(
            (mutations) => {
                for (
                    const mutation
                    of mutations
                ) {
                    mutation.addedNodes
                        .forEach(
                            (node) => {
                                if (
                                    !(
                                        node instanceof
                                        HTMLElement
                                    )
                                ) {
                                    return;
                                }

                                initializeWithin(
                                    node
                                );
                            }
                        );
                }
            }
        );


    const startObserver = () => {
        if (!document.body) {
            return;
        }

        observer.observe(
            document.body,
            {
                childList: true,
                subtree: true
            }
        );
    };


    if (
        document.readyState === "loading"
    ) {
        document.addEventListener(
            "DOMContentLoaded",
            startObserver
        );
    } else {
        startObserver();
    }


    /**
     * ---------------------------------------------------------
     * API PÚBLICA
     * ---------------------------------------------------------
     *
     * Deixamos uma pequena API disponível porque, no futuro,
     * outros módulos podem abrir um formulário dinamicamente
     * e querer inicializá-lo explicitamente.
     */

    window.ClientForm = {
        initialize:
            initializeClientForm,

        initializeWithin,

        formatCpf,

        formatCep,

        formatPhone,

        onlyDigits
    };

})();