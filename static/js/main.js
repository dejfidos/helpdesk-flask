document.addEventListener("DOMContentLoaded", () => {

    console.log("main.js načten");

    const deleteForms = document.querySelectorAll(".confirm-delete");

    deleteForms.forEach(form => {

        form.addEventListener("submit", event => {

            const message =
                form.dataset.confirmMessage
                || "Opravdu chceš tuto položku smazat?";

            if (!confirm(message)) {
                event.preventDefault();
            }

        });

    });

});

