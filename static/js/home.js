// =========================
// CONFIGURAÇÃO DOS MAPAS
// =========================

const centro = [-20.4711, -55.7874];

const zoom = 13;

const urlMapa =
    "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png?key=cb1_3vy9_1_0c9d8d43e5e259404039d999";


// =========================
// CRIAR MARCADORES
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
// ESCOLHER COR DO RELATO
// =========================

function escolherIcone(relato) {

    if (relato.status === "Em análise") {

        return amarelo;

    }

    if (
        relato.status === "Concluído" ||
        relato.status === "Concluída"
    ) {

        return verde;

    }

    return vermelho;

}


// =========================
// ESCOLHER COR DA OBRA
// =========================

function escolherIconeObra(obra) {

    if (obra.status === "Em andamento") {

        return azul;

    }

    if (obra.status === "Concluída") {

        return verde;

    }

    if (obra.status === "Em análise") {

        return amarelo;

    }

    return azul;

}


// =========================
// CRIAR POPUP DO RELATO
// =========================

function criarPopup(relato) {

    let fotos = "";

    if (relato.fotos && relato.fotos.length > 0) {

        relato.fotos.forEach(function (foto) {

            fotos += `

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


    return `

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

        ${fotos}

    `;

}


// =========================
// CRIAR POPUP DA OBRA
// =========================

function criarPopupObra(obra) {

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


    return popup;

}


// =========================
// CARREGAR RELATOS
// =========================

function carregarRelatos(mapa) {

    fetch("/api/relatos")

        .then(function (resposta) {

            if (!resposta.ok) {

                throw new Error(
                    "Erro HTTP: " + resposta.status
                );

            }

            return resposta.json();

        })

        .then(function (relatos) {

            console.log(
                "Relatos carregados no mapa:",
                relatos
            );


            relatos.forEach(function (relato) {

                const latitude =
                    parseFloat(relato.latitude);

                const longitude =
                    parseFloat(relato.longitude);


                if (
                    isNaN(latitude) ||
                    isNaN(longitude)
                ) {

                    return;

                }


                const marcador = L.marker(

                    [
                        latitude,
                        longitude
                    ],

                    {
                        icon: escolherIcone(relato)
                    }

                ).addTo(mapa);


                marcador.bindPopup(
                    criarPopup(relato)
                );

            });

        })

        .catch(function (erro) {

            console.error(
                "Erro ao carregar relatos:",
                erro
            );

        });

}


// =========================
// CARREGAR OBRAS
// =========================

function carregarObras(mapa) {

    fetch("/api/obras")

        .then(function (resposta) {

            if (!resposta.ok) {

                throw new Error(
                    "Erro HTTP: " + resposta.status
                );

            }

            return resposta.json();

        })

        .then(function (obras) {

            console.log(
                "Obras carregadas no mapa:",
                obras
            );


            obras.forEach(function (obra) {

                const latitude =
                    parseFloat(obra.latitude);

                const longitude =
                    parseFloat(obra.longitude);


                if (
                    isNaN(latitude) ||
                    isNaN(longitude)
                ) {

                    return;

                }


                const marcador = L.marker(

                    [
                        latitude,
                        longitude
                    ],

                    {
                        icon: escolherIconeObra(obra)
                    }

                ).addTo(mapa);


                marcador.bindPopup(
                    criarPopupObra(obra)
                );

            });

        })

        .catch(function (erro) {

            console.error(
                "Erro ao carregar obras:",
                erro
            );

        });

}


// =========================
// MAPA DO HERO
// =========================

const mapaHome = L.map("mapa-home")
    .setView(centro, zoom);


L.tileLayer(

    urlMapa,

    {

        attribution:
            '&copy; OpenStreetMap contributors &copy; CARTO',

        subdomains: "abcd"

    }

).addTo(mapaHome);


// Carregar relatos

carregarRelatos(mapaHome);


// Carregar obras

carregarObras(mapaHome);


// =========================
// MAPA DE PREVIEW
// =========================

const mapaHomePreview =
    L.map("mapa-home-preview")
        .setView(centro, zoom);


L.tileLayer(

    urlMapa,

    {

        attribution:
            '&copy; OpenStreetMap contributors &copy; CARTO',

        subdomains: "abcd"

    }

).addTo(mapaHomePreview);


// Carregar relatos

carregarRelatos(mapaHomePreview);


// Carregar obras

carregarObras(mapaHomePreview);