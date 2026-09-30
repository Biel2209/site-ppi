const botoesCancelar = document.querySelectorAll(".botao-cancelar");

const modal = document.getElementById("modal-cancelamento");

const fecharModal = document.getElementById("fechar-modal");

const confirmarCancelamento =
    document.getElementById("confirmar-cancelamento");

let relatoSelecionado = null;


botoesCancelar.forEach(function (botao) {

    botao.addEventListener("click", function () {

        relatoSelecionado = botao.dataset.id;

        modal.classList.add("aberto");

    });

});


fecharModal.addEventListener("click", function () {

    modal.classList.remove("aberto");

    relatoSelecionado = null;

});


confirmarCancelamento.addEventListener("click", function () {

    if (!relatoSelecionado) {
        return;
    }

    fetch("/cancelar-relato/" + relatoSelecionado, {
        method: "POST"
    })

    .then(async function (resposta) {
        const tipoConteudo = resposta.headers.get("content-type") || "";
        if (!tipoConteudo.includes("application/json")) {
            throw new Error("A resposta do servidor não contém JSON válido.");
        }

        const resultado = await resposta.json();
        if (
            !resultado ||
            typeof resultado !== "object" ||
            Array.isArray(resultado) ||
            typeof resultado.sucesso !== "boolean" ||
            typeof resultado.mensagem !== "string"
        ) {
            throw new Error("Resposta inesperada ao cancelar a solicitacao.");
        }

        if (!resposta.ok) {
            alert(resultado.mensagem || "Não foi possível cancelar a solicitação.");
            return null;
        }
        return resultado;
    })

    .then(function (resultado) {

        if (!resultado) {
            return;
        }

        if (resultado.sucesso) {

            window.location.reload();

        } else {

            alert(resultado.mensagem || "Não foi possível cancelar a solicitação.");

        }

    })

    .catch(function (erro) {

        console.error("Erro ao cancelar:", erro);
        alert("Ocorreu um erro ao cancelar. Tente novamente.");

    });

});
