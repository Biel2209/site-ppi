const mapa = L.map("mapa");

L.tileLayer("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png?key=cb1_3vy9_1_0c9d8d43e5e259404039d999", {
    attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
    subdomains: "abcd"
}).addTo(mapa);


// Tenta descobrir a localização do usuário
navigator.geolocation.getCurrentPosition(

    function (posicao) {

        const latitude = posicao.coords.latitude;
        const longitude = posicao.coords.longitude;

        // Centraliza o mapa na localização encontrada
        mapa.setView([latitude, longitude], 14);

        // Coloca um marcador na localização
        L.marker([latitude, longitude])
            .addTo(mapa)
            .bindPopup("Você está aqui")
            .openPopup();
    },

    function () {

        // Caso a pessoa negue a localização,
        // usamos Aquidauana como posição padrão.
        mapa.setView([-20.4711, -55.7874], 13);

        L.popup()
            .setLatLng([-20.4711, -55.7874])
            .setContent("Não foi possível acessar sua localização.")
            .openOn(mapa);
    }
);