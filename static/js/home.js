// =========================
// MAPA DO HERO
// =========================

const mapaHome = L.map("mapa-home").setView([-20.4711, -55.7874], 13);

L.tileLayer("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png?key=cb1_3vy9_1_0c9d8d43e5e259404039d999", {
    attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
    subdomains: "abcd"
}).addTo(mapaHome);


// Marcadores do Hero

L.marker([-20.4711, -55.7874])
    .addTo(mapaHome)
    .bindPopup(`
        <strong>Pavimentação da rua</strong><br>
        Bairro: Centro<br>
        Status: Em andamento
    `);

L.marker([-20.4685, -55.7905])
    .addTo(mapaHome)
    .bindPopup(`
        <strong>Reforma da praça</strong><br>
        Bairro: Alto<br>
        Status: Concluída
    `);

L.marker([-20.4752, -55.7818])
    .addTo(mapaHome)
    .bindPopup(`
        <strong>Buraco na via</strong><br>
        Bairro: Guanandi<br>
        Status: Problema registrado
    `);

L.marker([-20.4658, -55.7835])
    .addTo(mapaHome)
    .bindPopup(`
        <strong>Iluminação pública danificada</strong><br>
        Bairro: Nova Aquidauana<br>
        Status: Em análise
    `);


// =========================
// ÚLTIMO MAPA DA HOME
// =========================

const mapaHomePreview = L.map("mapa-home-preview").setView([-20.4711, -55.7874], 13);

L.tileLayer("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png?key=cb1_3vy9_1_0c9d8d43e5e259404039d999", {
    attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
    subdomains: "abcd"
}).addTo(mapaHomePreview);


// Marcadores do último mapa

L.marker([-20.4711, -55.7874])
    .addTo(mapaHomePreview)
    .bindPopup(`
        <strong>Pavimentação da rua</strong><br>
        Bairro: Centro<br>
        Status: Em andamento
    `);

L.marker([-20.4685, -55.7905])
    .addTo(mapaHomePreview)
    .bindPopup(`
        <strong>Reforma da praça</strong><br>
        Bairro: Alto<br>
        Status: Concluída
    `);

L.marker([-20.4752, -55.7818])
    .addTo(mapaHomePreview)
    .bindPopup(`
        <strong>Buraco na via</strong><br>
        Bairro: Guanandi<br>
        Status: Problema registrado
    `);

L.marker([-20.4658, -55.7835])
    .addTo(mapaHomePreview)
    .bindPopup(`
        <strong>Iluminação pública danificada</strong><br>
        Bairro: Nova Aquidauana<br>
        Status: Em análise
    `); 