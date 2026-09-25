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

    .then(function (resposta) {
        return resposta.json();
    })

    .then(function (resultado) {

        if (resultado.sucesso) {

            window.location.reload();

        } else {

            alert(resultado.mensagem);

        }

    })

    .catch(function (erro) {

        console.error("Erro ao cancelar:", erro);

    });

});