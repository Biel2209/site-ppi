const mapa = L.map("mapa");

L.tileLayer("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png?key=cb1_3vy9_1_0c9d8d43e5e259404039d999", {
    attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
    subdomains: "abcd"
}).addTo(mapa);


// Cria os marcadores coloridos
function criarMarcador(cor) {
    return L.divIcon({
        className: "",
        html: `<div class="marcador-cor" style="border-color: ${cor};"></div>`,
        iconSize: [20, 20],
        iconAnchor: [10, 10]
    });
}

const azul = criarMarcador("#5581C9");
const verde = criarMarcador("#4CAF7D");
const vermelho = criarMarcador("#D9534F");
const amarelo = criarMarcador("#E8B94A");


// Tenta descobrir a localização do usuário
navigator.geolocation.getCurrentPosition(
    function (posicao) {

        const latitude = posicao.coords.latitude;
        const longitude = posicao.coords.longitude;

        mapa.setView([latitude, longitude], 14);

        L.marker([latitude, longitude])
            .addTo(mapa)
            .bindPopup("Você está aqui")
            .openPopup();
    },

    function () {

        mapa.setView([-20.4711, -55.7874], 13);

        L.popup()
            .setLatLng([-20.4711, -55.7874])
            .setContent("Não foi possível acessar sua localização.")
            .openOn(mapa);
    }
);


// Obra em andamento
const obra = L.marker([-20.4711, -55.7874], {
    icon: azul
}).addTo(mapa);

obra.bindPopup(`
    <strong>Pavimentação da rua</strong><br>
    Bairro: Centro<br>
    Status: Em andamento<br>
    Previsão: Dezembro/2026
`);


// Obra concluída
const obra2 = L.marker([-20.4685, -55.7905], {
    icon: verde
}).addTo(mapa);

obra2.bindPopup(`
    <strong>Reforma da praça</strong><br>
    Bairro: Alto<br>
    Status: Concluída<br>
    Conclusão: Setembro/2026
`);


// Problema
const problema = L.marker([-20.4752, -55.7818], {
    icon: vermelho
}).addTo(mapa);

problema.bindPopup(`
    <strong>Buraco na via</strong><br>
    Bairro: Guanandi<br>
    Status: Problema registrado<br>
    Registrado em: Setembro/2026
`);


// Problema em análise
const problema2 = L.marker([-20.4658, -55.7835], {
    icon: amarelo
}).addTo(mapa);

problema2.bindPopup(`
    <strong>Iluminação pública danificada</strong><br>
    Bairro: Nova Aquidauana<br>
    Status: Em análise<br>
    Registrado em: Setembro/2026
`);