document.addEventListener("DOMContentLoaded", () => {
    const grupoEstrelas = document.querySelector(".estrelas");
    if (!grupoEstrelas) return;

    const radios = [...grupoEstrelas.querySelectorAll('input[name="nota"]')];
    const rotulos = [...grupoEstrelas.querySelectorAll("label[data-nota]")];

    const atualizarEstrelas = (valor) => {
        rotulos.forEach((rotulo) => {
            const selecionada = Number(rotulo.dataset.nota) <= valor;
            rotulo.classList.toggle("selecionada", selecionada);
            rotulo.textContent = selecionada ? "★" : "☆";
        });
    };

    radios.forEach((radio) => {
        radio.addEventListener("change", () => atualizarEstrelas(Number(radio.value)));
    });

    const inicial = radios.find((radio) => radio.checked);
    if (inicial) atualizarEstrelas(Number(inicial.value));
});
