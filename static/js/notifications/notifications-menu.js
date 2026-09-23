document.addEventListener("DOMContentLoaded", () => {
    const csrfToken = document.querySelector(
        "[name=csrfmiddlewaretoken]"
    )?.value;

    // =========================================================
    // UTILITÁRIOS
    // =========================================================

    const postRequest = async (url) => {
        const response = await fetch(url, {
            method: "POST",
            headers: {
                "X-CSRFToken": csrfToken,
                "X-Requested-With": "XMLHttpRequest",
            },
        });

        if (!response.ok) {
            throw new Error(
                "Não foi possível concluir a operação."
            );
        }

        return response.json();
    };


    // =========================================================
    // INTERFACE GLOBAL DO SINO
    // =========================================================

    const updateUnreadInterface = (count) => {
        const badge = document.getElementById(
            "notifications-unread-badge"
        );

        const summary = document.getElementById(
            "notifications-unread-summary"
        );

        const dropdownMarkAllButton = document.getElementById(
            "notifications-mark-all"
        );

        if (badge) {
            if (count > 0) {
                badge.textContent = count > 99 ? "99+" : count;
                badge.classList.remove("hidden");
            } else {
                badge.textContent = "";
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

        if (dropdownMarkAllButton) {
            dropdownMarkAllButton.disabled = count === 0;

            dropdownMarkAllButton.classList.toggle(
                "opacity-40",
                count === 0
            );

            dropdownMarkAllButton.classList.toggle(
                "cursor-not-allowed",
                count === 0
            );
        }
    };


    // =========================================================
    // DROPDOWN DO SINO
    // =========================================================

    const menu = document.getElementById(
        "notifications-menu"
    );

    const trigger = document.getElementById(
        "notifications-trigger"
    );

    const dropdown = document.getElementById(
        "notifications-dropdown"
    );

    const dropdownMarkAllButton = document.getElementById(
        "notifications-mark-all"
    );


    const setDropdownNotificationAsRead = (
        notificationElement
    ) => {
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


    if (menu && trigger && dropdown) {
        const openDropdown = () => {
            dropdown.classList.remove("hidden");
            trigger.setAttribute(
                "aria-expanded",
                "true"
            );
        };

        const closeDropdown = () => {
            dropdown.classList.add("hidden");
            trigger.setAttribute(
                "aria-expanded",
                "false"
            );
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


        // =====================================================
        // DROPDOWN — MARCAR UMA COMO LIDA
        // =====================================================

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

                        /*
                         * Notificação já lida:
                         * deixa o comportamento normal do link seguir.
                         */
                        if (!unread || !readUrl) {
                            return;
                        }

                        event.preventDefault();

                        try {
                            const data = await postRequest(
                                readUrl
                            );

                            setDropdownNotificationAsRead(
                                notificationElement
                            );

                            updateUnreadInterface(
                                data.unread_count
                            );

                            if (
                                destination
                                && destination !== "#"
                            ) {
                                window.location.href =
                                    destination;
                            }
                        } catch (error) {
                            console.error(error);

                            /*
                             * Uma falha ao marcar como lida
                             * não pode impedir a navegação.
                             */
                            if (
                                destination
                                && destination !== "#"
                            ) {
                                window.location.href =
                                    destination;
                            }
                        }
                    }
                );
            });


        // =====================================================
        // DROPDOWN — MARCAR TODAS COMO LIDAS
        // =====================================================

        if (dropdownMarkAllButton) {
            dropdownMarkAllButton.addEventListener(
                "click",
                async () => {
                    if (dropdownMarkAllButton.disabled) {
                        return;
                    }

                    const markAllUrl =
                        dropdownMarkAllButton.dataset.markAllUrl;

                    if (!markAllUrl) {
                        return;
                    }

                    dropdownMarkAllButton.disabled = true;

                    try {
                        const data = await postRequest(
                            markAllUrl
                        );

                        document
                            .querySelectorAll(
                                '[data-notification-item][data-unread="true"]'
                            )
                            .forEach(
                                (notificationElement) => {
                                    setDropdownNotificationAsRead(
                                        notificationElement
                                    );
                                }
                            );

                        updateUnreadInterface(
                            data.unread_count
                        );
                    } catch (error) {
                        console.error(error);

                        dropdownMarkAllButton.disabled =
                            false;
                    }
                }
            );
        }
    }


    // =========================================================
    // CENTRAL DE NOTIFICAÇÕES
    // =========================================================

    const centralItems = document.querySelectorAll(
        ".notification-list-item"
    );

    const centralMarkAllButton = document.getElementById(
        "notification-list-mark-all-read"
    );


    const getCentralUnreadCount = () => {
        return document.querySelectorAll(
            ".notification-list-item[data-unread='true']"
        ).length;
    };


    const updateCentralCounters = (count) => {
        const unreadCounter = document.getElementById(
            "notification-list-unread-count"
        );

        const unreadTabCounter = document.getElementById(
            "notification-list-unread-tab-count"
        );

        if (unreadCounter) {
            unreadCounter.textContent = count;
        }

        if (unreadTabCounter) {
            unreadTabCounter.textContent = count;

            if (count === 0) {
                unreadTabCounter.classList.add(
                    "hidden"
                );
            } else {
                unreadTabCounter.classList.remove(
                    "hidden"
                );
            }
        }

        if (centralMarkAllButton) {
            if (count === 0) {
                centralMarkAllButton.remove();
            }
        }
    };


    const setCentralNotificationAsRead = (
        notificationElement
    ) => {
        notificationElement.dataset.unread = "false";

        notificationElement.classList.remove(
            "bg-brand-50/40"
        );

        notificationElement.classList.add(
            "bg-white"
        );

        const unreadLabel =
            notificationElement.querySelector(
                ".notification-unread-label"
            );

        if (unreadLabel) {
            unreadLabel.remove();
        }

        const title = notificationElement.querySelector(
            "h2"
        );

        if (title) {
            title.classList.remove(
                "font-bold"
            );

            title.classList.add(
                "font-semibold"
            );
        }

        const markReadButton =
            notificationElement.querySelector(
                ".notification-mark-read"
            );

        if (markReadButton) {
            markReadButton.remove();
        }
    };


    // =========================================================
    // CENTRAL — MARCAR UMA COMO LIDA
    // =========================================================

    document
        .querySelectorAll(".notification-mark-read")
        .forEach((button) => {
            button.addEventListener(
                "click",
                async () => {
                    const notificationId =
                        button.dataset.notificationId;

                    const notificationElement =
                        button.closest(
                            ".notification-list-item"
                        );

                    if (
                        !notificationId
                        || !notificationElement
                    ) {
                        return;
                    }

                    button.disabled = true;

                    try {
                        const readUrl =
                            button.dataset.readUrl;

                        const data = await postRequest(
                            readUrl
                        );

                        setCentralNotificationAsRead(
                            notificationElement
                        );

                        updateUnreadInterface(
                            data.unread_count
                        );

                        updateCentralCounters(
                            data.unread_count
                        );
                    } catch (error) {
                        console.error(error);
                        button.disabled = false;
                    }
                }
            );
        });


    // =========================================================
    // CENTRAL — ABRIR NOTIFICAÇÃO
    // =========================================================

    document
        .querySelectorAll(".notification-open-link")
        .forEach((link) => {
            link.addEventListener(
                "click",
                async (event) => {
                    const notificationId =
                        link.dataset.notificationId;

                    const notificationElement =
                        link.closest(
                            ".notification-list-item"
                        );

                    const destination =
                        link.getAttribute("href");

                    if (
                        !notificationId
                        || !notificationElement
                        || notificationElement.dataset.unread
                            !== "true"
                    ) {
                        return;
                    }

                    event.preventDefault();

                    try {
                        const readUrl =
                            button.dataset.readUrl;

                        await postRequest(
                            readUrl
                        );
                    } catch (error) {
                        console.error(error);
                    }

                    /*
                     * Mesmo que a marcação como lida falhe,
                     * o usuário continua para o destino.
                     */
                    window.location.href = destination;
                }
            );
        });


    // =========================================================
    // CENTRAL — MARCAR TODAS COMO LIDAS
    // =========================================================

    if (centralMarkAllButton) {
        centralMarkAllButton.addEventListener(
            "click",
            async () => {
                const markAllUrl =
                    centralMarkAllButton.dataset.markAllUrl;

                if (!markAllUrl) {
                    return;
                }

                centralMarkAllButton.disabled = true;

                try {
                    const data = await postRequest(
                        markAllUrl
                    );

                    centralItems.forEach(
                        (notificationElement) => {
                            if (
                                notificationElement.dataset.unread
                                === "true"
                            ) {
                                setCentralNotificationAsRead(
                                    notificationElement
                                );
                            }
                        }
                    );

                    updateUnreadInterface(
                        data.unread_count
                    );

                    updateCentralCounters(
                        data.unread_count
                    );
                } catch (error) {
                    console.error(error);

                    centralMarkAllButton.disabled =
                        false;
                }
            }
        );
    }


    // =========================================================
    // ESTADO INICIAL DA CENTRAL
    // =========================================================

    if (centralItems.length) {
        updateCentralCounters(
            getCentralUnreadCount()
        );
    }
});