const mapa = L.map("mapa");

L.tileLayer(
    "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png?key=cb1_3vy9_1_0c9d8d43e5e259404039d999",
    {
        attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
        subdomains: "abcd"
    }
).addTo(mapa);


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


// Cores

const azul = criarMarcador("#5581C9");
const verde = criarMarcador("#4CAF7D");
const vermelho = criarMarcador("#D9534F");
const amarelo = criarMarcador("#E8B94A");
const marcadoresMapa = [];

function escaparHtml(valor) {
    return String(valor ?? "").replace(/[&<>\"']/g, function (caractere) {
        return {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            "\"": "&quot;",
            "'": "&#39;"
        }[caractere];
    });
}

let filtroAtual = "todos";

function aplicarFiltroMapa() {

    marcadoresMapa.forEach(function (item) {

        if (
            filtroAtual === "todos" ||
            item.status === filtroAtual
        ) {
            item.marcador.addTo(mapa);
        }
        else {
            mapa.removeLayer(item.marcador);
        }

    });

}


// =========================
// LOCALIZAÇÃO DO USUÁRIO
// =========================

function usarCentroPadrao() {
    mapa.setView([-20.4711, -55.7874], 13);
    L.popup()
        .setLatLng([-20.4711, -55.7874])
        .setContent("Não foi possível acessar sua localização.")
        .openOn(mapa);
}

if (navigator.geolocation && navigator.geolocation.getCurrentPosition) {

    navigator.geolocation.getCurrentPosition(

    function (posicao) {

        const latitude = posicao.coords.latitude;
        const longitude = posicao.coords.longitude;

        mapa.setView(
            [latitude, longitude],
            14
        );

        L.marker([
            latitude,
            longitude
        ])
            .addTo(mapa)
            .bindPopup("Você está aqui")
            .openPopup();

    },

        usarCentroPadrao
    );

} else {
    usarCentroPadrao();
}


// =========================
// RELATOS DO BANCO DE DADOS
// =========================

fetch("/api/relatos")

    .then(function (resposta) {

        return resposta.json();

    })

    .then(function (relatos) {

        relatos.forEach(function (relato) {

            let icone = azul;

            if (relato.status === "Em análise") {
                icone = amarelo;
            }
            else if (relato.status === "Em andamento") {
                icone = azul;
            }
            else if (relato.status === "Concluída") {
                icone = verde;
            }
            else if (relato.status === "Cancelado") {
                icone = vermelho;
            }


            const marcador = L.marker(
                [
                    parseFloat(relato.latitude),
                    parseFloat(relato.longitude)
                ],
                {
                    icon: icone
                }
            );

            marcadoresMapa.push({
                marcador: marcador,
                status: relato.status
            });
            aplicarFiltroMapa();

            // =========================
            // FOTOS DO RELATO
            // =========================

            let imagens = "";

            relato.fotos.forEach(function (foto) {

                imagens += `

                    <img
                        src="/static/uploads/${escaparHtml(foto)}"
                        alt="Foto do problema"
                        style="
                            width: 100%;
                            max-width: 250px;
                            margin-top: 10px;
                            border-radius: 8px;
                        "
                    >

                `;

            });


            // =========================
            // POPUP DO RELATO
            // =========================

            marcador.bindPopup(`
                
                <strong>
                    ${escaparHtml(relato.tipo)}
                </strong>

                <br><br>

                <strong>
                    📍 Rua:
                </strong>
                ${escaparHtml(relato.rua || "Não informada")}

                <br>

                <strong>
                    🏘️ Bairro:
                </strong>
                ${escaparHtml(relato.bairro || "Não informado")}

                <br><br>

                ${escaparHtml(relato.descricao)}

                <br><br>

                <strong>
                    Status:
                </strong>
                
                ${escaparHtml(relato.status)}

                <br>

                <strong>
                    Registrado em:
                </strong>
                
                ${escaparHtml(relato.data)}

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
// OBRAS DO BANCO DE DADOS
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

            else if (obra.status === "Cancelado") {

                icone = vermelho;

            }

            else {

                icone = azul;

            }


            // =========================
            // MARCADOR
            // =========================

            const marcador = L.marker(
                [
                    parseFloat(obra.latitude),
                    parseFloat(obra.longitude)
                ],
                {
                    icon: icone
                }
            );

            marcadoresMapa.push({
                marcador: marcador,
                status: obra.status
            });
            aplicarFiltroMapa();

            // =========================
            // POPUP DA OBRA
            // =========================

            let popup = `
                <strong>
                    ${escaparHtml(obra.titulo)}
                </strong>

                <br><br>

                <strong>
                    📍 Rua:
                </strong>
                ${escaparHtml(obra.rua || obra.localizacao || "Não informada")}

                <br>

                <strong>
                    🏘️ Bairro:
                </strong>
                ${escaparHtml(obra.bairro || "Não informado")}

                <br><br>

                <strong>
                    Status:
                </strong>
                ${escaparHtml(obra.status)}
            `;


            if (obra.previsao) {

                popup += `

                    <br>

                    <strong>
                        Previsão:
                    </strong>

                    ${escaparHtml(obra.previsao)}

                `;

            }


            if (obra.descricao) {

                popup += `

                    <br><br>

                    ${escaparHtml(obra.descricao)}

                `;

            }


            marcador.bindPopup(popup);

        });

    })

    .catch(function (erro) {

        console.error(
            "Erro ao carregar as obras:",
            erro
        );

    });

const botaoFiltros = document.getElementById("botao-filtros");
const painelFiltros = document.getElementById("painel-filtros");
const filtroStatus = document.getElementById("filtro-status");

if (botaoFiltros && painelFiltros) {

    botaoFiltros.addEventListener("click", function () {

        painelFiltros.classList.toggle("aberto");

    });

}

if (filtroStatus) {

    filtroStatus.addEventListener("change", function () {

        filtroAtual = filtroStatus.value;

        aplicarFiltroMapa();

    });

}    
