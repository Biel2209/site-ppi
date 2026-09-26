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


// =========================
// LOCALIZAÇÃO DO USUÁRIO
// =========================

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

    function () {

        mapa.setView(
            [-20.4711, -55.7874],
            13
        );

        L.popup()

            .setLatLng([
                -20.4711,
                -55.7874
            ])

            .setContent(
                "Não foi possível acessar sua localização."
            )

            .openOn(mapa);

    }

);


// =========================
// RELATOS DO BANCO DE DADOS
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

            } else {

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

            ).addTo(mapa);


            // =========================
            // FOTOS DO RELATO
            // =========================

            let imagens = "";

            relato.fotos.forEach(function (foto) {

                imagens += `

                    <img
                        src="/static/uploads/${foto}"
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

            ).addTo(mapa);


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


            marcador.bindPopup(popup);

        });

    })

    .catch(function (erro) {

        console.error(
            "Erro ao carregar as obras:",
            erro
        );

    });