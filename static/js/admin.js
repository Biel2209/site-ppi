document.addEventListener("DOMContentLoaded", function () {
    const botaoFiltros = document.getElementById("botao-filtros");
    const opcoesFiltros = document.getElementById("opcoes-filtros");
    const filtroTipo = document.getElementById("filtro-tipo");
    const filtroStatus = document.getElementById("filtro-status");
    const botaoLimpar = document.getElementById("limpar-filtros");
    const itens = document.querySelectorAll(".item-admin");

    const botaoCadastrarObra = document.getElementById("botao-cadastrar-obra");
    const formularioCadastroObra = document.getElementById("formulario-cadastro-obra");
    const fecharFormularioObra = document.getElementById("fechar-formulario-obra");
    const cancelarCadastroObra = document.getElementById("cancelar-cadastro-obra");

    const mapaElemento = document.getElementById("mapa-obra");
    const formularioObra = formularioCadastroObra
        ? formularioCadastroObra.querySelector("form")
        : null;
    const campoLocalizacao = document.getElementById("localizacao-obra");
    const campoLatitude = document.getElementById("latitude-obra");
    const campoLongitude = document.getElementById("longitude-obra");

    let mapaObra = null;
    let marcadorObra = null;
    let localizacaoSelecionada = false;
    let requisicaoEnderecoAtual = 0;

    function inicializarMapaObra() {
        if (!mapaElemento || typeof L === "undefined") {
            return;
        }

        if (!mapaObra) {
            mapaObra = L.map(mapaElemento).setView([-20.4711, -55.7874], 13);

            L.tileLayer(
                "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png?key=cb1_3vy9_1_0c9d8d43e5e259404039d999",
                {
                    attribution: "&copy; OpenStreetMap contributors &copy; CARTO",
                    subdomains: "abcd"
                }
            ).addTo(mapaObra);

            mapaObra.on("click", function (evento) {
                const latitude = evento.latlng.lat;
                const longitude = evento.latlng.lng;

                if (!marcadorObra) {
                    marcadorObra = L.marker(evento.latlng).addTo(mapaObra);
                } else {
                    marcadorObra.setLatLng(evento.latlng);
                }

                campoLatitude.value = latitude.toFixed(7);
                campoLongitude.value = longitude.toFixed(7);
                localizacaoSelecionada = true;
                buscarEnderecoObra(latitude, longitude);
            });
        }

        window.setTimeout(function () {
            if (mapaObra) {
                mapaObra.invalidateSize();
            }
        }, 100);
    }

    function buscarEnderecoObra(latitude, longitude) {
        const requisicaoEndereco = ++requisicaoEnderecoAtual;
        const parametros = new URLSearchParams({
            lat: latitude,
            lon: longitude,
            format: "jsonv2",
            addressdetails: "1"
        });

        fetch("https://nominatim.openstreetmap.org/reverse?" + parametros.toString(), {
            headers: {
                Accept: "application/json"
            }
        })
            .then(function (resposta) {
                if (!resposta.ok) {
                    throw new Error("Falha ao consultar o endereço.");
                }
                return resposta.json();
            })
            .then(function (dados) {
                if (requisicaoEndereco !== requisicaoEnderecoAtual) {
                    return;
                }

                const endereco = dados.address || {};
                const rua = endereco.road
                    || endereco.pedestrian
                    || endereco.residential
                    || endereco.footway;
                const bairro = endereco.neighbourhood
                    || endereco.suburb
                    || endereco.quarter
                    || endereco.city_district;
                const partes = [rua, bairro].filter(Boolean);
                const localizacao = partes.join(", ") || dados.display_name;

                if (localizacao && campoLocalizacao) {
                    campoLocalizacao.value = localizacao;
                }
            })
            .catch(function (erro) {
                console.error("Não foi possível descobrir rua e bairro:", erro);
            });
    }

    if (botaoCadastrarObra && formularioCadastroObra) {
        botaoCadastrarObra.addEventListener("click", function () {
            formularioCadastroObra.classList.add("aberto");
            formularioCadastroObra.scrollIntoView({
                behavior: "smooth",
                block: "start"
            });
            inicializarMapaObra();
        });
    }

    function fecharFormulario() {
        if (formularioCadastroObra) {
            formularioCadastroObra.classList.remove("aberto");
        }
    }

    if (fecharFormularioObra) {
        fecharFormularioObra.addEventListener("click", fecharFormulario);
    }

    if (cancelarCadastroObra) {
        cancelarCadastroObra.addEventListener("click", fecharFormulario);
    }

    if (botaoFiltros && opcoesFiltros) {
        botaoFiltros.addEventListener("click", function () {
            opcoesFiltros.classList.toggle("aberto");
        });
    }

    function aplicarFiltros() {
        if (!filtroTipo || !filtroStatus) {
            return;
        }

        const tipoSelecionado = filtroTipo.value;
        const statusSelecionado = filtroStatus.value;

        itens.forEach(function (item) {
            const correspondeTipo = tipoSelecionado === "todos"
                || item.dataset.tipo === tipoSelecionado;
            const correspondeStatus = statusSelecionado === "todos"
                || item.dataset.status === statusSelecionado;

            item.style.display = correspondeTipo && correspondeStatus ? "" : "none";
        });
    }

    if (filtroTipo) {
        filtroTipo.addEventListener("change", aplicarFiltros);
    }

    if (filtroStatus) {
        filtroStatus.addEventListener("change", aplicarFiltros);
    }

    if (botaoLimpar) {
        botaoLimpar.addEventListener("click", function () {
            if (filtroTipo) {
                filtroTipo.value = "todos";
            }
            if (filtroStatus) {
                filtroStatus.value = "todos";
            }
            aplicarFiltros();
        });
    }

    if (formularioObra) {
        formularioObra.addEventListener("submit", function (evento) {
            if (!localizacaoSelecionada || !campoLatitude.value || !campoLongitude.value) {
                evento.preventDefault();
                window.alert("Selecione uma localização clicando no mapa antes de cadastrar a obra.");
                mapaElemento.scrollIntoView({ behavior: "smooth", block: "center" });
                return;
            }

            if (!campoLocalizacao.value.trim()) {
                evento.preventDefault();
                campoLocalizacao.setCustomValidity("Informe a localização da obra.");
                campoLocalizacao.reportValidity();
                campoLocalizacao.addEventListener("input", function limparValidacao() {
                    campoLocalizacao.setCustomValidity("");
                    campoLocalizacao.removeEventListener("input", limparValidacao);
                });
            }
        });
    }
});
