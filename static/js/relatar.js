// =========================
// MAPA
// =========================

const mapaRelato = L.map("mapa-relato").setView([-20.4711, -55.7874], 13);

L.tileLayer("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png?key=cb1_3vy9_1_0c9d8d43e5e259404039d999", {
    attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
    subdomains: "abcd"
}).addTo(mapaRelato);


// =========================
// MARCADOR
// =========================

let marcador = null;

mapaRelato.on("click", function (evento) {

    const latitude = evento.latlng.lat;
    const longitude = evento.latlng.lng;

    if (marcador !== null) {
        mapaRelato.removeLayer(marcador);
    }

    marcador = L.marker([latitude, longitude])
        .addTo(mapaRelato)
        .bindPopup("Local do problema")
        .openPopup();
});


// =========================
// TIPOS
// =========================

const buscaTipo = document.getElementById("busca-tipo");
const opcoesTipo = document.querySelectorAll(".tipo-opcao");
const tipoSelecionado = document.getElementById("tipo-selecionado");

let tipoAtual = "";


// =========================
// SELECIONAR TIPO
// =========================

opcoesTipo.forEach(function (opcao) {

    opcao.addEventListener("click", function () {

        opcoesTipo.forEach(function (item) {
            item.classList.remove("selecionado");
        });

        opcao.classList.add("selecionado");

        tipoAtual = opcao.dataset.valor;

        tipoSelecionado.textContent =
            "Tipo selecionado: " + tipoAtual;
    });

});


// =========================
// BUSCAR TIPO
// =========================

buscaTipo.addEventListener("input", function () {

    const pesquisa = buscaTipo.value.toLowerCase().trim();

    opcoesTipo.forEach(function (opcao) {

        const texto = opcao.dataset.valor.toLowerCase();

        if (texto.includes(pesquisa)) {
            opcao.style.display = "block";
        } else {
            opcao.style.display = "none";
        }

    });

});


// =========================
// FOTOS
// =========================

const campoFotos = document.getElementById("fotos");
const previewFotos = document.getElementById("preview-fotos");

let fotosSelecionadas = [];

campoFotos.addEventListener("change", function () {

    const novasFotos = Array.from(campoFotos.files);

    if (fotosSelecionadas.length + novasFotos.length > 3) {

        alert("Você pode adicionar no máximo 3 fotos.");

        return;
    }

    novasFotos.forEach(function (foto) {

        fotosSelecionadas.push(foto);

    });

    mostrarFotos();

    campoFotos.value = "";
});


function mostrarFotos() {

    previewFotos.innerHTML = "";

    fotosSelecionadas.forEach(function (foto, indice) {

        const container = document.createElement("div");

        container.classList.add("foto-preview");


        const imagem = document.createElement("img");

        imagem.src = URL.createObjectURL(foto);


        const botao = document.createElement("button");

        botao.type = "button";

        botao.textContent = "×";


        botao.addEventListener("click", function () {

            fotosSelecionadas.splice(indice, 1);

            mostrarFotos();

        });


        container.appendChild(imagem);

        container.appendChild(botao);

        previewFotos.appendChild(container);

    });

}


// =========================
// ENVIAR RELATO + FOTOS
// =========================

const botaoEnviar = document.getElementById("enviar-relato");

botaoEnviar.addEventListener("click", async function () {

    // Verificar tipo

    if (tipoAtual === "") {

        alert("Selecione o tipo do problema.");

        return;
    }


    // Verificar descrição

    const descricao =
        document.getElementById("descricao").value.trim();

    if (descricao === "") {

        alert("Descreva o problema.");

        return;
    }


    // Verificar localização

    if (marcador === null) {

        alert("Clique no mapa para selecionar o local.");

        return;
    }


    // Pegar localização

    const posicao = marcador.getLatLng();


    // Criar FormData

    const dados = new FormData();


    // Dados do relato

    dados.append("tipo", tipoAtual);

    dados.append("descricao", descricao);

    dados.append("latitude", posicao.lat);

    dados.append("longitude", posicao.lng);


    // Adicionar fotos

    fotosSelecionadas.forEach(function (foto) {

        dados.append("fotos", foto);

    });


    // Enviar para Flask

    const resposta = await fetch("/enviar-relato", {

        method: "POST",

        body: dados

    });


    const resultado = await resposta.json();


    // Resultado

    if (resultado.sucesso) {

        alert(resultado.mensagem);


        // Limpar descrição

        document.getElementById("descricao").value = "";


        // Limpar tipo

        opcoesTipo.forEach(function (opcao) {

            opcao.classList.remove("selecionado");

        });

        tipoAtual = "";

        tipoSelecionado.textContent =
            "Nenhum tipo selecionado.";


        // Remover marcador

        if (marcador !== null) {

            mapaRelato.removeLayer(marcador);

            marcador = null;

        }


        // Limpar fotos

        fotosSelecionadas = [];

        previewFotos.innerHTML = "";

    }

});