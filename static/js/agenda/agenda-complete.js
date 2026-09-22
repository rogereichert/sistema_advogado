document.addEventListener("DOMContentLoaded", () => {
    const modal = document.getElementById("agenda-complete-modal");

    if (!modal) {
        return;
    }

    const buttons = document.querySelectorAll(
        ".agenda-outcome-button"
    );

    const form = document.getElementById(
        "agenda-complete-form"
    );

    const result = document.getElementById(
        "agenda-complete-result"
    );

    const errorBox = document.getElementById(
        "agenda-complete-error"
    );

    const submit = document.getElementById(
        "agenda-complete-submit"
    );

    const submitLabel = document.getElementById(
        "agenda-complete-submit-label"
    );

    const getElement = (id) => {
        return document.getElementById(id);
    };

    let actionUrl = "";
    let outcome = "complete";
    let submitting = false;


    // =========================================================
    // ERROS
    // =========================================================

    const hideError = () => {
        if (!errorBox) {
            return;
        }

        errorBox.textContent = "";
        errorBox.classList.add("hidden");
    };


    const showError = (message) => {
        if (!errorBox) {
            return;
        }

        errorBox.textContent = message;
        errorBox.classList.remove("hidden");
    };


    // =========================================================
    // CONFIGURAÇÃO DA MODAL
    // =========================================================

    const setMode = (mode) => {
        outcome = mode;

        const isNotCompleted = (
            mode === "not_completed"
        );

        const eyebrow = getElement(
            "agenda-outcome-eyebrow"
        );

        const modalTitle = getElement(
            "agenda-complete-modal-title"
        );

        const description = getElement(
            "agenda-outcome-description"
        );

        const resultLabel = getElement(
            "agenda-outcome-result-label"
        );

        const resultHelp = getElement(
            "agenda-outcome-result-help"
        );

        const infoText = getElement(
            "agenda-outcome-info-text"
        );

        const completeIcon = getElement(
            "agenda-outcome-complete-icon"
        );

        const notCompletedIcon = getElement(
            "agenda-outcome-not-completed-icon"
        );

        const iconBox = getElement(
            "agenda-outcome-icon-box"
        );


        // =====================================================
        // NÃO REALIZADO
        // =====================================================

        if (isNotCompleted) {
            if (eyebrow) {
                eyebrow.textContent = (
                    "Desfecho do compromisso"
                );

                eyebrow.className = (
                    "text-[10px] font-semibold uppercase " +
                    "tracking-[0.14em] text-red-700"
                );
            }

            if (modalTitle) {
                modalTitle.textContent = (
                    "Marcar como não realizado"
                );
            }

            if (description) {
                description.textContent = (
                    "Registre por que este compromisso " +
                    "não foi realizado."
                );
            }

            if (resultLabel) {
                resultLabel.textContent = (
                    "Motivo / observação *"
                );
            }

            if (resultHelp) {
                resultHelp.textContent = (
                    "O motivo é obrigatório para registrar " +
                    "o compromisso como não realizado."
                );
            }

            if (result) {
                result.required = true;

                result.placeholder = (
                    "Ex.: Audiência redesignada pelo juízo; " +
                    "parte não compareceu."
                );
            }

            if (infoText) {
                infoText.textContent = (
                    "O desfecho será registrado no histórico " +
                    "do caso. O compromisso continuará " +
                    "normalmente no Google Agenda."
                );
            }

            if (completeIcon) {
                completeIcon.classList.add(
                    "hidden"
                );
            }

            if (notCompletedIcon) {
                notCompletedIcon.classList.remove(
                    "hidden"
                );
            }

            if (iconBox) {
                iconBox.className = (
                    "flex h-10 w-10 shrink-0 items-center " +
                    "justify-center rounded-xl bg-red-50 " +
                    "text-red-700 ring-1 ring-inset " +
                    "ring-red-200"
                );
            }

            if (submit) {
                submit.className = (
                    "inline-flex min-h-10 items-center " +
                    "justify-center rounded-xl bg-red-700 " +
                    "px-4 text-sm font-semibold text-white " +
                    "shadow-sm transition hover:bg-red-800 " +
                    "focus:outline-none focus:ring-4 " +
                    "focus:ring-red-100 " +
                    "disabled:cursor-not-allowed " +
                    "disabled:opacity-60"
                );
            }

            if (submitLabel) {
                submitLabel.textContent = (
                    "Confirmar não realizado"
                );
            }

            return;
        }


        // =====================================================
        // CONCLUIR
        // =====================================================

        if (eyebrow) {
            eyebrow.textContent = (
                "Realização do compromisso"
            );

            eyebrow.className = (
                "text-[10px] font-semibold uppercase " +
                "tracking-[0.14em] text-emerald-700"
            );
        }

        if (modalTitle) {
            modalTitle.textContent = (
                "Concluir compromisso"
            );
        }

        if (description) {
            description.textContent = (
                "Registre a realização deste compromisso " +
                "no LexControl."
            );
        }

        if (resultLabel) {
            resultLabel.textContent = (
                "Resultado / observação"
            );
        }

        if (resultHelp) {
            resultHelp.textContent = (
                "Informe o resultado, providência adotada " +
                "ou qualquer observação relevante sobre " +
                "o compromisso."
            );
        }

        if (result) {
            result.required = false;

            result.placeholder = (
                "Ex.: Audiência realizada. Conciliação " +
                "não obtida."
            );
        }

        if (infoText) {
            infoText.textContent = (
                "A conclusão será registrada no histórico " +
                "do caso. O compromisso continuará " +
                "normalmente no Google Agenda."
            );
        }

        if (completeIcon) {
            completeIcon.classList.remove(
                "hidden"
            );
        }

        if (notCompletedIcon) {
            notCompletedIcon.classList.add(
                "hidden"
            );
        }

        if (iconBox) {
            iconBox.className = (
                "flex h-10 w-10 shrink-0 items-center " +
                "justify-center rounded-xl bg-emerald-50 " +
                "text-emerald-700 ring-1 ring-inset " +
                "ring-emerald-200"
            );
        }

        if (submit) {
            submit.className = (
                "inline-flex min-h-10 items-center " +
                "justify-center rounded-xl bg-brand-950 " +
                "px-4 text-sm font-semibold text-white " +
                "shadow-sm transition hover:bg-brand-900 " +
                "focus:outline-none focus:ring-4 " +
                "focus:ring-brand-100 " +
                "disabled:cursor-not-allowed " +
                "disabled:opacity-60"
            );
        }

        if (submitLabel) {
            submitLabel.textContent = (
                "Confirmar conclusão"
            );
        }
    };


    // =========================================================
    // ABRIR MODAL
    // =========================================================

    const openModal = (button) => {
        actionUrl = (
            button.dataset.actionUrl || ""
        );

        setMode(
            button.dataset.outcome || "complete"
        );


        const eventType = getElement(
            "agenda-complete-event-type"
        );

        const eventTitle = getElement(
            "agenda-complete-event-title"
        );

        const eventDate = getElement(
            "agenda-complete-event-date"
        );


        if (eventType) {
            eventType.textContent = (
                button.dataset.eventType || ""
            );
        }

        if (eventTitle) {
            eventTitle.textContent = (
                button.dataset.eventTitle || ""
            );
        }


        const date = (
            button.dataset.eventDate || ""
        );

        const time = (
            button.dataset.eventTime || ""
        );


        if (eventDate) {
            eventDate.textContent = time
                ? `${date} às ${time}`
                : date;
        }


        if (result) {
            result.value = "";
        }

        hideError();

        modal.classList.remove(
            "hidden"
        );

        document.body.classList.add(
            "overflow-hidden"
        );


        window.setTimeout(
            () => {
                if (result) {
                    result.focus();
                }
            },
            50
        );
    };


    // =========================================================
    // FECHAR MODAL
    // =========================================================

    const closeModal = () => {
        if (submitting) {
            return;
        }

        modal.classList.add(
            "hidden"
        );

        document.body.classList.remove(
            "overflow-hidden"
        );

        actionUrl = "";

        if (result) {
            result.value = "";
        }

        hideError();
    };


    // =========================================================
    // BOTÕES DE DESFECHO
    // =========================================================

    buttons.forEach(
        (button) => {
            button.addEventListener(
                "click",
                () => {
                    openModal(button);
                }
            );
        }
    );


    // =========================================================
    // FECHAMENTO DA MODAL
    // =========================================================

    const closeButton = getElement(
        "agenda-complete-modal-close"
    );

    const cancelButton = getElement(
        "agenda-complete-cancel"
    );

    const backdrop = getElement(
        "agenda-complete-modal-backdrop"
    );


    if (closeButton) {
        closeButton.addEventListener(
            "click",
            closeModal
        );
    }


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


    // =========================================================
    // ENVIO
    // =========================================================

    if (form) {
        form.addEventListener(
            "submit",
            async (event) => {
                event.preventDefault();

                if (
                    submitting
                    || !actionUrl
                ) {
                    return;
                }


                const resultValue = result
                    ? result.value.trim()
                    : "";


                // =============================================
                // MOTIVO OBRIGATÓRIO PARA NÃO REALIZADO
                // =============================================

                if (
                    outcome === "not_completed"
                    && !resultValue
                ) {
                    showError(
                        "Informe o motivo ou uma observação " +
                        "para registrar o compromisso como " +
                        "não realizado."
                    );

                    if (result) {
                        result.focus();
                    }

                    return;
                }


                hideError();

                submitting = true;

                if (submit) {
                    submit.disabled = true;
                }

                if (submitLabel) {
                    submitLabel.textContent = (
                        "Salvando..."
                    );
                }


                try {
                    const csrfInput = (
                        form.querySelector(
                            "[name=csrfmiddlewaretoken]"
                        )
                    );

                    const formData = new FormData(
                        form
                    );


                    const response = await fetch(
                        actionUrl,
                        {
                            method: "POST",

                            headers: {
                                "X-CSRFToken": (
                                    csrfInput
                                        ? csrfInput.value
                                        : ""
                                ),

                                "X-Requested-With": (
                                    "XMLHttpRequest"
                                ),
                            },

                            credentials: "same-origin",

                            body: formData,
                        }
                    );


                    const data = await response.json();


                    if (
                        !response.ok
                        || !data.success
                    ) {
                        throw new Error(
                            data.message
                            || (
                                "Não foi possível registrar " +
                                "o desfecho do compromisso."
                            )
                        );
                    }


                    if (submitLabel) {
                        submitLabel.textContent = (
                            outcome === "not_completed"
                                ? "Registrado"
                                : "Concluído"
                        );
                    }


                    window.setTimeout(
                        () => {
                            window.location.reload();
                        },
                        500
                    );

                } catch (error) {
                    showError(
                        error.message
                        || (
                            "Não foi possível registrar " +
                            "o desfecho do compromisso."
                        )
                    );


                    submitting = false;


                    if (submit) {
                        submit.disabled = false;
                    }


                    if (submitLabel) {
                        submitLabel.textContent = (
                            outcome === "not_completed"
                                ? "Confirmar não realizado"
                                : "Confirmar conclusão"
                        );
                    }
                }
            }
        );
    }
});