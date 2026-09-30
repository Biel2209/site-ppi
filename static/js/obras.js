const botoesFiltro = document.querySelectorAll(".filtro");

const obras = document.querySelectorAll(".card-obra");

botoesFiltro.forEach(function (botao) {

    botao.addEventListener("click", function () {

        botoesFiltro.forEach(function (item) {
            item.classList.remove("ativo");
        });

        botao.classList.add("ativo");

        const filtro = botao.textContent.trim();

        obras.forEach(function (obra) {

            const status = obra.dataset.status.trim();

            if (filtro === "Todas") {

                obra.style.display = "block";

            } else if (
                filtro === "Em andamento" &&
                status === "andamento"
            ) {

                obra.style.display = "block";

            } else if (
                filtro === "Concluídas" &&
                status === "concluida"
            ) {

                obra.style.display = "block";

            } else if (
                filtro === "Em análise" &&
                status === "analise"
            ) {

                obra.style.display = "block";

            } else {

                obra.style.display = "none";

            }

        });

    });

});