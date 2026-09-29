
(() => {
    "use strict";

    // =========================================================
    // UTILITÁRIOS
    // =========================================================

    function getCookie(name) {
        const cookies = document.cookie
            ? document.cookie.split(";")
            : [];

        for (const cookie of cookies) {
            const item = cookie.trim();

            if (item.startsWith(`${name}=`)) {
                return decodeURIComponent(
                    item.substring(name.length + 1)
                );
            }
        }

        return "";
    }

    function escapeHtml(value) {
        return String(value ?? "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    }

    function normalizeProcessNumber(value) {
        return String(value || "").replace(/\D/g, "");
    }

    function formatProcessNumber(value) {
        const digits = normalizeProcessNumber(value);

        if (digits.length !== 20) {
            return value || "";
        }

        return (
            `${digits.slice(0, 7)}-` +
            `${digits.slice(7, 9)}.` +
            `${digits.slice(9, 13)}.` +
            `${digits.slice(13, 14)}.` +
            `${digits.slice(14, 16)}.` +
            `${digits.slice(16, 20)}`
        );
    }

    // Converte a data do DataJud para o formato
    // esperado pelo input HTML type="date".
    //
    // Evita new Date() para não deslocar a data
    // por causa do fuso horário.

    function toInputDate(value) {
        if (!value) {
            return "";
        }

        const raw = String(value).trim();

        // Formato DataJud: YYYYMMDDHHMMSS ou YYYYMMDD
        if (/^\d{8}(\d{6})?$/.test(raw)) {
            return (
                `${raw.slice(0, 4)}-` +
                `${raw.slice(4, 6)}-` +
                `${raw.slice(6, 8)}`
            );
        }

        // Formato ISO: YYYY-MM-DD...
        const iso = raw.match(
            /^(\d{4})-(\d{2})-(\d{2})/
        );

        if (iso) {
            return `${iso[1]}-${iso[2]}-${iso[3]}`;
        }

        // Formato brasileiro: DD/MM/YYYY
        const br = raw.match(
            /^(\d{2})\/(\d{2})\/(\d{4})$/
        );

        if (br) {
            return `${br[3]}-${br[2]}-${br[1]}`;
        }

        return "";
    }

    function formatDate(value) {
        const date = toInputDate(value);

        if (!date) {
            return "Não informado";
        }

        const [year, month, day] = date.split("-");

        return `${day}/${month}/${year}`;
    }

    function getName(value) {
        if (!value) {
            return "";
        }

        if (typeof value === "object") {
            return String(
                value.nome ||
                value.tribunal_nome ||
                value.tribunal ||
                ""
            );
        }

        return String(value);
    }

    function findFeedback(form) {
        return form.querySelector(
            "[data-datajud-feedback]"
        );
    }

    function showFeedback(feedback, html) {
        if (!feedback) {
            return;
        }

        feedback.innerHTML = html;
        feedback.classList.remove("hidden");
    }

    function clearFeedback(feedback) {
        if (!feedback) {
            return;
        }

        feedback.innerHTML = "";
        feedback.classList.add("hidden");
    }

    // =========================================================
    // CONTROLE DA VINCULAÇÃO
    // =========================================================

    function getApplyInput(form) {
        let input = form.querySelector(
            "input[name='datajud_aplicar']"
        );

        if (!input) {
            input = document.createElement("input");
            input.type = "hidden";
            input.name = "datajud_aplicar";
            input.value = "0";

            form.appendChild(input);
        }

        return input;
    }

    function clearBinding(form) {
        getApplyInput(form).value = "0";

        delete form.dataset.datajudConsultedNumber;
    }

    function markBinding(form, number) {
        getApplyInput(form).value = "1";

        form.dataset.datajudConsultedNumber =
            normalizeProcessNumber(number);
    }

    // =========================================================
    // CAMPOS PROCESSUAIS
    // =========================================================

    const PROCESS_FIELDS = [
        {
            name: "tribunal",
            label: "Tribunal"
        },
        {
            name: "grau",
            label: "Grau"
        },
        {
            name: "classe_processual",
            label: "Classe processual"
        },
        {
            name: "sistema_processual",
            label: "Sistema processual"
        },
        {
            name: "orgao_julgador_nome",
            label: "Órgão julgador"
        },
        {
            name: "data_ajuizamento",
            label: "Data de ajuizamento"
        }
    ];

    function extractProcessData(response) {
        const data = response.dados || {};

        const tribunalMetadata =
            response.tribunal || {};

        return {
            numero_processo:
                data.numero_processo ||
                response.numero_processo ||
                "",

            tribunal:
                getName(data.tribunal) ||
                getName(tribunalMetadata) ||
                "",

            grau:
                data.grau || "",

            classe_processual:
                getName(data.classe) || "",

            sistema_processual:
                getName(data.sistema) || "",

            orgao_julgador_nome:
                getName(data.orgao_julgador) || "",

            data_ajuizamento:
                toInputDate(data.data_ajuizamento)
        };
    }

    function findField(form, name) {
        return form.querySelector(
            `[name="${name}"]`
        );
    }

    function getFieldChanges(form, processData) {
        const changes = [];
        const conflicts = [];

        for (const config of PROCESS_FIELDS) {
            const input = findField(
                form,
                config.name
            );

            const newValue = String(
                processData[config.name] || ""
            ).trim();

            // Não modifica campos ausentes nem substitui
            // informações existentes por valores vazios.
            if (!input || !newValue) {
                continue;
            }

            const currentValue =
                String(input.value || "").trim();

            if (currentValue === newValue) {
                continue;
            }

            const change = {
                input,
                label: config.label,
                oldValue: currentValue,
                newValue
            };

            changes.push(change);

            if (currentValue) {
                conflicts.push(change);
            }
        }

        return {
            changes,
            conflicts
        };
    }

    function populateProcessFields(form, processData) {
        const {
            changes,
            conflicts
        } = getFieldChanges(
            form,
            processData
        );

        // Se existirem valores manuais diferentes,
        // pede autorização antes de substituí-los.
        if (conflicts.length) {
            const names = conflicts
                .map(item => `• ${item.label}`)
                .join("\n");

            const confirmed = window.confirm(
                "Os seguintes campos já possuem " +
                "informações diferentes:\n\n" +
                names +
                "\n\nDeseja substituí-los pelos dados " +
                "retornados pelo DataJud?\n\n" +
                "Cancelar preserva os valores atuais."
            );

            if (!confirmed) {
                // Mesmo cancelando a substituição,
                // preenche somente os campos vazios.
                const safeChanges = changes.filter(
                    item => !item.oldValue
                );

                for (const item of safeChanges) {
                    updateField(item);
                }

                return {
                    updated: safeChanges.length,
                    preserved: conflicts.length
                };
            }
        }

        for (const item of changes) {
            updateField(item);
        }

        return {
            updated: changes.length,
            preserved: 0
        };
    }

    function updateField(change) {
        change.input.value = change.newValue;

        // Notifica outros scripts que acompanham
        // alterações nos campos do formulário.
        change.input.dispatchEvent(
            new Event("input", {
                bubbles: true
            })
        );

        change.input.dispatchEvent(
            new Event("change", {
                bubbles: true
            })
        );
    }

    // =========================================================
    // CARREGAMENTO
    // =========================================================

    function setLoading(button, loading) {
        if (!button) {
            return;
        }

        if (loading) {
            if (!button.dataset.originalHtml) {
                button.dataset.originalHtml =
                    button.innerHTML;
            }

            button.disabled = true;

            button.classList.add(
                "cursor-not-allowed",
                "opacity-70"
            );

            button.innerHTML = `
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
                        d="M4 12a8 8 0 0 1 8-8V0C5.373 0 0 5.373 0 12h4Z"
                    ></path>
                </svg>

                <span>Consultando...</span>
            `;

            return;
        }

        button.disabled = false;

        button.classList.remove(
            "cursor-not-allowed",
            "opacity-70"
        );

        if (button.dataset.originalHtml) {
            button.innerHTML =
                button.dataset.originalHtml;

            delete button.dataset.originalHtml;
        }
    }

    // =========================================================
    // RESULTADOS
    // =========================================================

    function renderDataItem(label, value) {
        return `
            <div class="min-w-0">
                <p class="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                    ${escapeHtml(label)}
                </p>

                <p class="mt-1 break-words text-sm font-semibold text-brand-950">
                    ${escapeHtml(value || "Não informado")}
                </p>
            </div>
        `;
    }

    function renderMessage(
        feedback,
        title,
        message,
        type
    ) {
        const isWarning = type === "warning";

        const styles = isWarning
            ? {
                border: "border-amber-200",
                background: "bg-amber-50",
                title: "text-amber-900",
                body: "text-amber-800"
            }
            : {
                border: "border-red-200",
                background: "bg-red-50",
                title: "text-red-800",
                body: "text-red-700"
            };

        showFeedback(
            feedback,
            `
                <div
                    role="${isWarning ? "status" : "alert"}"
                    class="rounded-2xl border ${styles.border} ${styles.background} p-4"
                >
                    <p class="text-sm font-semibold ${styles.title}">
                        ${escapeHtml(title)}
                    </p>

                    <p class="mt-2 text-sm leading-6 ${styles.body}">
                        ${escapeHtml(message)}
                    </p>

                    <p class="mt-3 text-xs ${styles.body}">
                        Você pode preencher os dados
                        processuais manualmente e
                        continuar o cadastro.
                    </p>
                </div>
            `
        );
    }

    function renderError(feedback, message) {
        renderMessage(
            feedback,
            "Não foi possível consultar o processo",
            message ||
                "Não foi possível realizar a consulta.",
            "error"
        );
    }

    function renderNotFound(feedback, message) {
        renderMessage(
            feedback,
            "Processo não encontrado",
            message ||
                "Nenhum processo foi localizado com esse número.",
            "warning"
        );
    }

    function renderSuccess(
        form,
        feedback,
        response
    ) {
        const data = extractProcessData(
            response
        );

        // Armazena apenas no formulário atual.
        // Não persiste informações no navegador.
        form.datajudResult = data;

        const number = formatProcessNumber(
            data.numero_processo
        );

        showFeedback(
            feedback,
            `
                <div
                    class="overflow-hidden rounded-2xl border border-emerald-200 bg-emerald-50/70"
                    data-datajud-result
                >
                    <div
                        class="flex flex-col gap-3 border-b border-emerald-200 px-4 py-4 sm:flex-row sm:items-center sm:justify-between"
                    >
                        <div class="flex items-start gap-3">
                            <div
                                class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-white text-emerald-700 ring-1 ring-emerald-100"
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
                                        d="m4.5 12.75 6 6 9-13.5"
                                    ></path>
                                </svg>
                            </div>

                            <div class="min-w-0">
                                <p class="text-sm font-semibold text-emerald-900">
                                    Processo encontrado no DataJud
                                </p>

                                <p class="mt-1 break-all text-xs font-medium text-emerald-800">
                                    ${escapeHtml(number)}
                                </p>
                            </div>
                        </div>

                        <span
                            class="inline-flex w-fit items-center rounded-full bg-white px-3 py-1 text-xs font-semibold text-emerald-800 ring-1 ring-emerald-200"
                        >
                            Consulta oficial
                        </span>
                    </div>

                    <div
                        class="grid gap-4 p-4 sm:grid-cols-2 lg:grid-cols-3"
                    >
                        ${renderDataItem(
                            "Tribunal",
                            data.tribunal
                        )}

                        ${renderDataItem(
                            "Grau",
                            data.grau
                        )}

                        ${renderDataItem(
                            "Sistema",
                            data.sistema_processual
                        )}

                        ${renderDataItem(
                            "Classe processual",
                            data.classe_processual
                        )}

                        ${renderDataItem(
                            "Órgão julgador",
                            data.orgao_julgador_nome
                        )}

                        ${renderDataItem(
                            "Data de ajuizamento",
                            formatDate(
                                data.data_ajuizamento
                            )
                        )}
                    </div>

                    <div
                        class="border-t border-emerald-200 bg-white/60 px-4 py-4"
                    >
                        <div
                            class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"
                        >
                            <p
                                class="text-xs leading-5 text-slate-600"
                                data-datajud-binding-message
                            >
                                Confira o resultado e clique
                                para preencher os campos do
                                formulário.
                            </p>

                            <button
                                type="button"
                                data-datajud-vincular
                                data-datajud-numero="${escapeHtml(
                                    data.numero_processo
                                )}"
                                class="inline-flex min-h-10 shrink-0 items-center justify-center gap-2 rounded-xl border border-emerald-300 bg-white px-4 text-sm font-semibold text-emerald-800 shadow-sm transition hover:border-emerald-400 hover:bg-emerald-50 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
                            >
                                <span>
                                    Vincular dados ao caso
                                </span>
                            </button>
                        </div>
                    </div>
                </div>
            `
        );
    }

    // =========================================================
    // VINCULAÇÃO E PREENCHIMENTO
    // =========================================================

    function bindProcessData(button) {
        const form = button.closest("form");

        if (!form || !form.datajudResult) {
            return;
        }

        const processInput = findField(
            form,
            "numero_processo"
        );

        if (!processInput) {
            return;
        }

        const consultedNumber =
            normalizeProcessNumber(
                button.dataset.datajudNumero
            );

        const currentNumber =
            normalizeProcessNumber(
                processInput.value
            );

        if (
            !consultedNumber ||
            !currentNumber ||
            consultedNumber !== currentNumber
        ) {
            clearBinding(form);

            renderError(
                findFeedback(form),
                "O número do processo foi alterado. " +
                "Consulte novamente antes de vincular."
            );

            return;
        }

        const result = populateProcessFields(
            form,
            form.datajudResult
        );

        markBinding(
            form,
            consultedNumber
        );

        button.disabled = true;

        button.classList.add(
            "cursor-default",
            "opacity-80"
        );

        button.innerHTML = `
            <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke-width="1.8"
                stroke="currentColor"
                class="h-4 w-4"
                aria-hidden="true"
            >
                <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="m4.5 12.75 6 6 9-13.5"
                ></path>
            </svg>

            <span>Dados vinculados</span>
        `;

        const card = button.closest(
            "[data-datajud-result]"
        );

        const message = card?.querySelector(
            "[data-datajud-binding-message]"
        );

        if (message) {
            const updatedText =
                result.updated === 1
                    ? "1 campo preenchido."
                    : `${result.updated} campos preenchidos.`;

            const preservedText =
                result.preserved > 0
                    ? ` ${result.preserved} campo(s) manual(is) preservado(s).`
                    : "";

            message.textContent =
                updatedText +
                preservedText +
                " Revise os dados antes de salvar.";

            message.classList.remove(
                "text-slate-600"
            );

            message.classList.add(
                "font-semibold",
                "text-emerald-800"
            );
        }
    }

    // =========================================================
    // CONSULTA AO DATAJUD
    // =========================================================

    async function consultProcess(button) {
        const form = button.closest("form");

        if (!form) {
            return;
        }

        const feedback = findFeedback(
            form
        );

        const url =
            button.dataset.datajudUrl;

        const processInput = findField(
            form,
            "numero_processo"
        );

        if (!url) {
            renderError(
                feedback,
                "A rota de consulta não está disponível."
            );

            return;
        }

        if (!processInput) {
            renderError(
                feedback,
                "O campo de número do processo não foi encontrado."
            );

            return;
        }

        const number =
            processInput.value.trim();

        clearBinding(form);
        clearFeedback(feedback);

        form.datajudResult = null;

        if (!number) {
            renderError(
                feedback,
                "Informe o número do processo antes de consultar."
            );

            processInput.focus();

            return;
        }

        setLoading(
            button,
            true
        );

        try {
            const formData =
                new FormData();

            formData.append(
                "numero_processo",
                number
            );

            const response = await fetch(
                url,
                {
                    method: "POST",
                    body: formData,

                    headers: {
                        "X-CSRFToken":
                            getCookie(
                                "csrftoken"
                            ),

                        "X-Requested-With":
                            "XMLHttpRequest"
                    },

                    credentials: "same-origin"
                }
            );

            const contentType =
                response.headers.get(
                    "content-type"
                ) || "";

            if (
                !contentType.includes(
                    "application/json"
                )
            ) {
                throw new Error(
                    "Resposta inesperada do servidor."
                );
            }

            const data =
                await response.json();

            // Impede que uma resposta antiga
            // seja aplicada se o CNJ mudou
            // durante a consulta.
            if (
                normalizeProcessNumber(
                    processInput.value
                ) !==
                normalizeProcessNumber(
                    number
                )
            ) {
                renderError(
                    feedback,
                    "O número do processo mudou " +
                    "durante a consulta. Consulte novamente."
                );

                return;
            }

            if (
                response.ok &&
                data.success
            ) {
                renderSuccess(
                    form,
                    feedback,
                    data
                );

                return;
            }

            if (
                response.status === 404 ||
                data.status ===
                    "PROCESSO_NAO_ENCONTRADO"
            ) {
                renderNotFound(
                    feedback,
                    data.message
                );

                return;
            }

            renderError(
                feedback,
                data.message ||
                    "Não foi possível consultar o processo."
            );

        } catch (error) {
            console.error(
                "Erro ao consultar o DataJud:",
                error
            );

            renderError(
                feedback,
                "Não foi possível concluir a consulta. " +
                "Tente novamente em instantes."
            );

        } finally {
            setLoading(
                button,
                false
            );
        }
    }

    // =========================================================
    // EVENTOS
    // =========================================================

    // Delegação de eventos:
    // funciona também em modais carregadas por AJAX.

    document.addEventListener(
        "click",
        event => {
            const target = event.target;

            if (!(target instanceof Element)) {
                return;
            }

            const bindButton =
                target.closest(
                    "[data-datajud-vincular]"
                );

            if (bindButton) {
                event.preventDefault();

                bindProcessData(
                    bindButton
                );

                return;
            }

            const consultButton =
                target.closest(
                    "[data-datajud-consultar]"
                );

            if (consultButton) {
                event.preventDefault();

                consultProcess(
                    consultButton
                );
            }
        }
    );

    // Se o CNJ mudar, a vinculação
    // anteriormente confirmada é invalidada.

    document.addEventListener(
        "input",
        event => {
            const target = event.target;

            if (!(target instanceof Element)) {
                return;
            }

            const processInput =
                target.closest(
                    "input[name='numero_processo']"
                );

            if (!processInput) {
                return;
            }

            const form =
                processInput.closest("form");

            if (!form) {
                return;
            }

            const consultedNumber =
                form.dataset.datajudConsultedNumber;

            if (!consultedNumber) {
                return;
            }

            const currentNumber =
                normalizeProcessNumber(
                    processInput.value
                );

            if (
                currentNumber ===
                consultedNumber
            ) {
                return;
            }

            clearBinding(form);

            form.datajudResult = null;

            clearFeedback(
                findFeedback(form)
            );

            // Os campos preenchidos continuam
            // visíveis e editáveis. O usuário
            // decide se deseja apagá-los.
        }
    );

})();
