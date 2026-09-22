document.addEventListener("DOMContentLoaded", () => {
    const modal = document.getElementById(
        "agenda-complete-modal"
    );

    if (!modal) {
        return;
    }

    const $ = (id) => document.getElementById(id);

    const form = $("agenda-complete-form");
    const result = $("agenda-complete-result");
    const errorBox = $("agenda-complete-error");
    const submit = $("agenda-complete-submit");
    const submitLabel = $("agenda-complete-submit-label");

    let actionUrl = "";
    let outcome = "complete";
    let submitting = false;
    let currentIsDeadline = false;

    function getCsrfToken() {
        const cookie = document.cookie
            .split("; ")
            .find((row) => row.startsWith("csrftoken="));

        return cookie
            ? decodeURIComponent(cookie.split("=")[1])
            : "";
    }

    function showError(message) {
        if (!errorBox) {
            return;
        }

        errorBox.textContent = message;
        errorBox.classList.remove("hidden");
    }

    function clearError() {
        if (!errorBox) {
            return;
        }

        errorBox.textContent = "";
        errorBox.classList.add("hidden");
    }

    function setMode(mode) {
        outcome = mode;

        const notCompleted = (
            mode === "not_completed"
        );

        if (currentIsDeadline) {
            $("agenda-outcome-eyebrow").textContent =
                "Desfecho do prazo";

            $("agenda-complete-modal-title").textContent =
                notCompleted
                    ? "Registrar prazo não cumprido"
                    : "Registrar prazo cumprido";

            $("agenda-outcome-description").textContent =
                notCompleted
                    ? "Registre por que este prazo não foi cumprido."
                    : "Registre o cumprimento deste prazo no LexControl.";

            $("agenda-outcome-result-label").textContent =
                notCompleted
                    ? "Motivo / observação *"
                    : "Resultado / observação";

            $("agenda-outcome-result-help").textContent =
                notCompleted
                    ? (
                        "O motivo é obrigatório para registrar "
                        + "o prazo como não cumprido."
                    )
                    : (
                        "Informe o resultado, providência adotada "
                        + "ou qualquer observação relevante sobre "
                        + "o cumprimento do prazo."
                    );

            $("agenda-outcome-info-text").textContent =
                notCompleted
                    ? (
                        "O desfecho será registrado no histórico "
                        + "do caso. O evento continuará normalmente "
                        + "no Google Agenda."
                    )
                    : (
                        "O cumprimento será registrado no histórico "
                        + "do caso. O evento continuará normalmente "
                        + "no Google Agenda."
                    );

            result.placeholder = notCompleted
                ? "Ex.: Prazo não cumprido. Informe o motivo."
                : "Ex.: Petição protocolada dentro do prazo.";

            submitLabel.textContent = notCompleted
                ? "Confirmar não cumprimento"
                : "Confirmar cumprimento";

        } else {
            $("agenda-outcome-eyebrow").textContent =
                notCompleted
                    ? "Desfecho do compromisso"
                    : "Realização do compromisso";

            $("agenda-complete-modal-title").textContent =
                notCompleted
                    ? "Marcar como não realizado"
                    : "Concluir compromisso";

            $("agenda-outcome-description").textContent =
                notCompleted
                    ? (
                        "Registre por que este compromisso "
                        + "não foi realizado."
                    )
                    : (
                        "Registre a realização deste compromisso "
                        + "no LexControl."
                    );

            $("agenda-outcome-result-label").textContent =
                notCompleted
                    ? "Motivo / observação *"
                    : "Resultado / observação";

            $("agenda-outcome-result-help").textContent =
                notCompleted
                    ? (
                        "O motivo é obrigatório para registrar "
                        + "o compromisso como não realizado."
                    )
                    : (
                        "Informe o resultado, providência adotada "
                        + "ou qualquer observação relevante sobre "
                        + "o compromisso."
                    );

            $("agenda-outcome-info-text").textContent =
                notCompleted
                    ? (
                        "O desfecho será registrado no histórico "
                        + "do caso. O compromisso continuará "
                        + "normalmente no Google Agenda."
                    )
                    : (
                        "A conclusão será registrada no histórico "
                        + "do caso. O compromisso continuará "
                        + "normalmente no Google Agenda."
                    );

            result.placeholder = notCompleted
                ? (
                    "Ex.: Audiência redesignada pelo juízo; "
                    + "parte não compareceu."
                )
                : (
                    "Ex.: Audiência realizada. "
                    + "Conciliação não obtida."
                );

            submitLabel.textContent = notCompleted
                ? "Confirmar não realizado"
                : "Confirmar conclusão";
        }

        result.required = notCompleted;

        const completeIcon = $(
            "agenda-outcome-complete-icon"
        );

        const notCompletedIcon = $(
            "agenda-outcome-not-completed-icon"
        );

        if (completeIcon) {
            completeIcon.classList.toggle(
                "hidden",
                notCompleted
            );
        }

        if (notCompletedIcon) {
            notCompletedIcon.classList.toggle(
                "hidden",
                !notCompleted
            );
        }

        const iconBox = $("agenda-outcome-icon-box");

        if (iconBox) {
            iconBox.className = notCompleted
                ? (
                    "flex h-10 w-10 shrink-0 items-center "
                    + "justify-center rounded-xl bg-red-50 "
                    + "text-red-700 ring-1 ring-inset "
                    + "ring-red-200"
                )
                : (
                    "flex h-10 w-10 shrink-0 items-center "
                    + "justify-center rounded-xl bg-emerald-50 "
                    + "text-emerald-700 ring-1 ring-inset "
                    + "ring-emerald-200"
                );
        }

        submit.className = notCompleted
            ? (
                "inline-flex min-h-10 items-center justify-center "
                + "rounded-xl bg-red-700 px-4 text-sm "
                + "font-semibold text-white shadow-sm "
                + "hover:bg-red-800 disabled:opacity-60"
            )
            : (
                "inline-flex min-h-10 items-center justify-center "
                + "rounded-xl bg-brand-950 px-4 text-sm "
                + "font-semibold text-white shadow-sm "
                + "hover:bg-brand-900 disabled:opacity-60"
            );
    }

    function openModal(button) {
        actionUrl = button.dataset.actionUrl || "";

        const eventType = (
            button.dataset.eventType || ""
        );

        currentIsDeadline = (
            eventType.trim().toLowerCase() === "prazo"
        );

        setMode(
            button.dataset.outcome || "complete"
        );

        const typeElement = $(
            "agenda-complete-event-type"
        );

        if (typeElement) {
            typeElement.textContent = eventType;
        }

        const titleElement = $(
            "agenda-complete-event-title"
        );

        if (titleElement) {
            titleElement.textContent = (
                button.dataset.eventTitle
                || "Compromisso"
            );
        }

        const dateElement = $(
            "agenda-complete-event-date"
        );

        if (dateElement) {
            dateElement.textContent = (
                button.dataset.eventDate || ""
            );
        }

        const timeElement = $(
            "agenda-complete-event-time"
        );

        if (timeElement) {
            timeElement.textContent = (
                button.dataset.eventTime || ""
            );
        }

        result.value = "";
        clearError();

        modal.classList.remove("hidden");

        window.setTimeout(() => {
            result.focus();
        }, 100);
    }

    function closeModal() {
        if (submitting) {
            return;
        }

        modal.classList.add("hidden");
        clearError();
        result.value = "";
        actionUrl = "";
        currentIsDeadline = false;
    }

    document.addEventListener("click", (event) => {
        const trigger = event.target.closest(
            "[data-agenda-outcome]"
        );

        if (trigger) {
            event.preventDefault();
            openModal(trigger);
            return;
        }

        const closeButton = event.target.closest(
            "[data-agenda-complete-close]"
        );

        if (closeButton) {
            event.preventDefault();
            closeModal();
        }
    });

    document.addEventListener("keydown", (event) => {
        if (
            event.key === "Escape"
            && !modal.classList.contains("hidden")
        ) {
            closeModal();
        }
    });

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        if (submitting || !actionUrl) {
            return;
        }

        const resultValue = result.value.trim();

        if (
            outcome === "not_completed"
            && !resultValue
        ) {
            showError(
                currentIsDeadline
                    ? (
                        "Informe o motivo ou uma observação "
                        + "para registrar o prazo como "
                        + "não cumprido."
                    )
                    : (
                        "Informe o motivo ou uma observação "
                        + "para registrar o compromisso "
                        + "como não realizado."
                    )
            );

            result.focus();
            return;
        }

        submitting = true;
        clearError();

        submit.disabled = true;
        submitLabel.textContent = "Salvando...";

        const body = new URLSearchParams();
        body.set("resultado", resultValue);

        try {
            const response = await fetch(
                actionUrl,
                {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": getCsrfToken(),
                        "X-Requested-With": "XMLHttpRequest",
                        "Content-Type": (
                            "application/x-www-form-urlencoded"
                        ),
                    },
                    body: body.toString(),
                }
            );

            let data = {};

            try {
                data = await response.json();
            } catch (jsonError) {
                data = {};
            }

            if (!response.ok || !data.success) {
                throw new Error(
                    data.message
                    || "Não foi possível registrar o desfecho."
                );
            }

            window.location.reload();

        } catch (error) {
            showError(
                error.message
                || "Não foi possível registrar o desfecho."
            );

            submitting = false;
            submit.disabled = false;

            submitLabel.textContent = currentIsDeadline
                ? (
                    outcome === "not_completed"
                        ? "Confirmar não cumprimento"
                        : "Confirmar cumprimento"
                )
                : (
                    outcome === "not_completed"
                        ? "Confirmar não realizado"
                        : "Confirmar conclusão"
                );
        }
    });
});