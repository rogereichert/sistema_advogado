document.addEventListener("DOMContentLoaded", () => {
    const menu = document.getElementById("notifications-menu");
    const trigger = document.getElementById("notifications-trigger");
    const dropdown = document.getElementById("notifications-dropdown");
    const markAllButton = document.getElementById("notifications-mark-all");

    if (!menu || !trigger || !dropdown) {
        return;
    }

    const csrfToken = document.querySelector(
        "[name=csrfmiddlewaretoken]"
    )?.value;

    // =========================================================
    // DROPDOWN
    // =========================================================

    const openDropdown = () => {
        dropdown.classList.remove("hidden");
        trigger.setAttribute("aria-expanded", "true");
    };

    const closeDropdown = () => {
        dropdown.classList.add("hidden");
        trigger.setAttribute("aria-expanded", "false");
    };

    const toggleDropdown = () => {
        if (dropdown.classList.contains("hidden")) {
            openDropdown();
            return;
        }

        closeDropdown();
    };

    trigger.addEventListener("click", (event) => {
        event.stopPropagation();
        toggleDropdown();
    });

    dropdown.addEventListener("click", (event) => {
        event.stopPropagation();
    });

    document.addEventListener("click", (event) => {
        if (!menu.contains(event.target)) {
            closeDropdown();
        }
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            closeDropdown();
            trigger.focus();
        }
    });

    // =========================================================
    // INTERFACE
    // =========================================================

    const updateUnreadInterface = (count) => {
        const badge = document.getElementById(
            "notifications-unread-badge"
        );

        const summary = document.getElementById(
            "notifications-unread-summary"
        );

        if (badge) {
            if (count > 0) {
                badge.textContent = count > 99 ? "99+" : count;
                badge.classList.remove("hidden");
            } else {
                badge.classList.add("hidden");
            }
        }

        if (summary) {
            if (count === 0) {
                summary.textContent = "Nenhuma notificação nova";
            } else if (count === 1) {
                summary.textContent = "1 não lida";
            } else {
                summary.textContent = `${count} não lidas`;
            }
        }

        if (markAllButton) {
            markAllButton.disabled = count === 0;

            markAllButton.classList.toggle(
                "opacity-40",
                count === 0
            );

            markAllButton.classList.toggle(
                "cursor-not-allowed",
                count === 0
            );
        }
    };

    const setNotificationAsRead = (notificationElement) => {
        notificationElement.dataset.unread = "false";

        notificationElement.classList.remove(
            "bg-brand-50/40"
        );

        const title = notificationElement.querySelector(
            "[data-notification-title]"
        );

        if (title) {
            title.classList.remove(
                "font-semibold",
                "text-slate-900"
            );

            title.classList.add(
                "font-medium",
                "text-slate-700"
            );
        }

        const unreadDot = notificationElement.querySelector(
            "[data-unread-dot]"
        );

        if (unreadDot) {
            unreadDot.remove();
        }
    };

    // =========================================================
    // MARCAR UMA COMO LIDA
    // =========================================================

    document
        .querySelectorAll("[data-notification-item]")
        .forEach((notificationElement) => {
            notificationElement.addEventListener(
                "click",
                async (event) => {
                    const destination =
                        notificationElement.dataset.destination || "";

                    const readUrl =
                        notificationElement.dataset.readUrl;

                    const unread =
                        notificationElement.dataset.unread === "true";

                    if (!unread || !readUrl) {
                        return;
                    }

                    event.preventDefault();

                    try {
                        const response = await fetch(readUrl, {
                            method: "POST",
                            headers: {
                                "X-CSRFToken": csrfToken,
                                "X-Requested-With": "XMLHttpRequest",
                            },
                        });

                        if (!response.ok) {
                            throw new Error(
                                "Não foi possível marcar a notificação como lida."
                            );
                        }

                        const data = await response.json();

                        setNotificationAsRead(
                            notificationElement
                        );

                        updateUnreadInterface(
                            data.unread_count
                        );

                        if (destination && destination !== "#") {
                            window.location.href = destination;
                        }
                    } catch (error) {
                        console.error(error);

                        /*
                         * A falha ao marcar como lida não deve impedir
                         * o usuário de acessar o destino da notificação.
                         */
                        if (destination && destination !== "#") {
                            window.location.href = destination;
                        }
                    }
                }
            );
        });

    // =========================================================
    // MARCAR TODAS COMO LIDAS
    // =========================================================

    if (markAllButton) {
        markAllButton.addEventListener("click", async () => {
            if (markAllButton.disabled) {
                return;
            }

            const markAllUrl =
                markAllButton.dataset.markAllUrl;

            if (!markAllUrl) {
                return;
            }

            markAllButton.disabled = true;

            try {
                const response = await fetch(markAllUrl, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": csrfToken,
                        "X-Requested-With": "XMLHttpRequest",
                    },
                });

                if (!response.ok) {
                    throw new Error(
                        "Não foi possível marcar todas as notificações como lidas."
                    );
                }

                const data = await response.json();

                document
                    .querySelectorAll(
                        '[data-notification-item][data-unread="true"]'
                    )
                    .forEach((notificationElement) => {
                        setNotificationAsRead(
                            notificationElement
                        );
                    });

                updateUnreadInterface(
                    data.unread_count
                );
            } catch (error) {
                console.error(error);
                markAllButton.disabled = false;
            }
        });
    }
});