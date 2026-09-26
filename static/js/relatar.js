// =========================
// MAPA
// =========================

const mapaRelato = L.map("mapa-relato")
    .setView([-20.4711, -55.7874], 13);

L.tileLayer(
    "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png?key=cb1_3vy9_1_0c9d8d43e5e259404039d999",
    {
        attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
        subdomains: "abcd"
    }
).addTo(mapaRelato);


// =========================
// MARCADORES COLORIDOS
// =========================

function criarMarcador(cor) {

    return L.divIcon({

        className: "",

        html: `
            <div
                class="marcador-cor"
                style="border-color: ${cor};">
            </div>
        `,

        iconSize: [20, 20],

        iconAnchor: [10, 10]

    });

}


const vermelho = criarMarcador("#D9534F");
const amarelo = criarMarcador("#E8B94A");
const verde = criarMarcador("#4CAF7D");
const azul = criarMarcador("#5581C9");


// =========================
// MARCADOR DO NOVO RELATO
// =========================

let marcador = null;


// =========================
// RELATOS EXISTENTES
// =========================

fetch("/api/relatos")

    .then(function (resposta) {

        return resposta.json();

    })

    .then(function (relatos) {

        relatos.forEach(function (relato) {

            let icone;

            if (relato.status === "Em análise") {

                icone = amarelo;

            }

            else if (
                relato.status === "Concluído" ||
                relato.status === "Concluída"
            ) {

                icone = verde;

            }

            else {

                icone = vermelho;

            }


            const marcadorRelato = L.marker(

                [
                    parseFloat(relato.latitude),
                    parseFloat(relato.longitude)
                ],

                {
                    icon: icone
                }

            ).addTo(mapaRelato);


            // =========================
            // FOTOS DO RELATO
            // =========================

            let imagens = "";

            if (
                relato.fotos &&
                relato.fotos.length > 0
            ) {

                relato.fotos.forEach(function (foto) {

                    imagens += `

                        <img
                            src="/static/uploads/${foto}"
                            alt="Foto do problema"
                            style="
                                width: 100%;
                                max-width: 220px;
                                margin-top: 10px;
                                border-radius: 8px;
                                display: block;
                            "
                        >

                    `;

                });

            }


            // =========================
            // POPUP
            // =========================

            marcadorRelato.bindPopup(`

                <strong>
                    ${relato.tipo}
                </strong>

                <br><br>

                ${relato.descricao}

                <br><br>

                <strong>
                    Status:
                </strong>

                ${relato.status}

                <br>

                <strong>
                    Registrado em:
                </strong>

                ${relato.data}

                ${imagens}

            `);

        });

    })

    .catch(function (erro) {

        console.error(
            "Erro ao carregar os relatos:",
            erro
        );

    });


// =========================
// OBRAS EXISTENTES
// =========================

fetch("/api/obras")

    .then(function (resposta) {

        return resposta.json();

    })

    .then(function (obras) {

        obras.forEach(function (obra) {

            let icone;


            // =========================
            // COR DA OBRA
            // =========================

            if (obra.status === "Em andamento") {

                icone = azul;

            }

            else if (obra.status === "Concluída") {

                icone = verde;

            }

            else if (obra.status === "Em análise") {

                icone = amarelo;

            }

            else {

                icone = azul;

            }


            // =========================
            // MARCADOR DA OBRA
            // =========================

            const marcadorObra = L.marker(

                [
                    parseFloat(obra.latitude),
                    parseFloat(obra.longitude)
                ],

                {
                    icon: icone
                }

            ).addTo(mapaRelato);


            // =========================
            // POPUP DA OBRA
            // =========================

            let popup = `

                <strong>
                    ${obra.titulo}
                </strong>

                <br><br>

                <strong>
                    Local:
                </strong>

                ${obra.localizacao}

                <br><br>

                <strong>
                    Status:
                </strong>

                ${obra.status}

            `;


            if (obra.previsao) {

                popup += `

                    <br>

                    <strong>
                        Previsão:
                    </strong>

                    ${obra.previsao}

                `;

            }


            if (obra.descricao) {

                popup += `

                    <br><br>

                    ${obra.descricao}

                `;

            }


            marcadorObra.bindPopup(popup);

        });

    })

    .catch(function (erro) {

        console.error(
            "Erro ao carregar as obras:",
            erro
        );

    });


// =========================
// ESCOLHER LOCAL DO NOVO RELATO
// =========================

mapaRelato.on("click", function (evento) {

    const latitude = evento.latlng.lat;

    const longitude = evento.latlng.lng;


    // Remove somente o marcador
    // do novo relato

    if (marcador !== null) {

        mapaRelato.removeLayer(marcador);

    }


    marcador = L.marker(
        [latitude, longitude]
    )

        .addTo(mapaRelato)

        .bindPopup(
            "Local do problema"
        )

        .openPopup();

});


// =========================
// TIPOS
// =========================

const buscaTipo =
    document.getElementById("busca-tipo");

const opcoesTipo =
    document.querySelectorAll(".tipo-opcao");

const tipoSelecionado =
    document.getElementById("tipo-selecionado");

let tipoAtual = "";


// =========================
// SELECIONAR TIPO
// =========================

opcoesTipo.forEach(function (opcao) {

    opcao.addEventListener(
        "click",
        function () {

            opcoesTipo.forEach(
                function (item) {

                    item.classList.remove(
                        "selecionado"
                    );

                }
            );


            opcao.classList.add(
                "selecionado"
            );


            tipoAtual =
                opcao.dataset.valor;


            tipoSelecionado.textContent =
                "Tipo selecionado: " + tipoAtual;

        }
    );

});


// =========================
// BUSCAR TIPO
// =========================

buscaTipo.addEventListener(
    "input",
    function () {

        const pesquisa =
            buscaTipo.value
                .toLowerCase()
                .trim();


        opcoesTipo.forEach(
            function (opcao) {

                const texto =
                    opcao.dataset.valor
                        .toLowerCase();


                if (
                    texto.includes(pesquisa)
                ) {

                    opcao.style.display =
                        "block";

                }

                else {

                    opcao.style.display =
                        "none";

                }

            }
        );

    }
);


// =========================
// FOTOS
// =========================

const campoFotos =
    document.getElementById("fotos");

const previewFotos =
    document.getElementById("preview-fotos");

let fotosSelecionadas = [];


// =========================
// SELECIONAR FOTOS
// =========================

campoFotos.addEventListener(
    "change",
    function () {

        const novasFotos =
            Array.from(campoFotos.files);


        if (
            fotosSelecionadas.length +
            novasFotos.length > 3
        ) {

            alert(
                "Você pode adicionar no máximo 3 fotos."
            );

            return;

        }


        novasFotos.forEach(
            function (foto) {

                fotosSelecionadas.push(
                    foto
                );

            }
        );


        mostrarFotos();

        campoFotos.value = "";

    }
);


// =========================
// MOSTRAR FOTOS
// =========================

function mostrarFotos() {

    previewFotos.innerHTML = "";


    fotosSelecionadas.forEach(
        function (foto, indice) {

            const container =
                document.createElement(
                    "div"
                );


            container.classList.add(
                "foto-preview"
            );


            const imagem =
                document.createElement(
                    "img"
                );


            imagem.src =
                URL.createObjectURL(foto);


            const botao =
                document.createElement(
                    "button"
                );


            botao.type = "button";

            botao.textContent = "×";


            botao.addEventListener(
                "click",
                function () {

                    fotosSelecionadas.splice(
                        indice,
                        1
                    );


                    mostrarFotos();

                }
            );


            container.appendChild(
                imagem
            );

            container.appendChild(
                botao
            );

            previewFotos.appendChild(
                container
            );

        }
    );

}


// =========================
// ENVIAR RELATO + FOTOS
// =========================

const botaoEnviar =
    document.getElementById(
        "enviar-relato"
    );


botaoEnviar.addEventListener(
    "click",
    async function () {


        // =========================
        // VERIFICAR TIPO
        // =========================

        if (tipoAtual === "") {

            alert(
                "Selecione o tipo do problema."
            );

            return;

        }


        // =========================
        // VERIFICAR DESCRIÇÃO
        // =========================

        const descricao =
            document
                .getElementById("descricao")
                .value
                .trim();


        if (descricao === "") {

            alert(
                "Descreva o problema."
            );

            return;

        }


        // =========================
        // VERIFICAR LOCALIZAÇÃO
        // =========================

        if (marcador === null) {

            alert(
                "Clique no mapa para selecionar o local."
            );

            return;

        }


        // =========================
        // PEGAR LOCALIZAÇÃO
        // =========================

        const posicao =
            marcador.getLatLng();


        // =========================
        // FORM DATA
        // =========================

        const dados =
            new FormData();


        dados.append(
            "tipo",
            tipoAtual
        );


        dados.append(
            "descricao",
            descricao
        );


        dados.append(
            "latitude",
            posicao.lat
        );


        dados.append(
            "longitude",
            posicao.lng
        );


        // =========================
        // ADICIONAR FOTOS
        // =========================

        fotosSelecionadas.forEach(
            function (foto) {

                dados.append(
                    "fotos",
                    foto
                );

            }
        );


        // =========================
        // ENVIAR PARA FLASK
        // =========================

        const resposta =
            await fetch(
                "/enviar-relato",
                {
                    method: "POST",
                    body: dados
                }
            );


        const resultado =
            await resposta.json();


        // =========================
        // RESULTADO
        // =========================

        if (resultado.sucesso) {

            alert(
                resultado.mensagem
            );


            // Limpar descrição

            document
                .getElementById("descricao")
                .value = "";


            // Limpar tipo

            opcoesTipo.forEach(
                function (opcao) {

                    opcao.classList.remove(
                        "selecionado"
                    );

                }
            );


            tipoAtual = "";


            tipoSelecionado.textContent =
                "Nenhum tipo selecionado.";


            // Remover marcador
            // do novo relato

            if (marcador !== null) {

                mapaRelato.removeLayer(
                    marcador
                );

                marcador = null;

            }


            // Limpar fotos

            fotosSelecionadas = [];

            previewFotos.innerHTML = "";

        }

    }
);