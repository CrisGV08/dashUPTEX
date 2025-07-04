document.addEventListener("DOMContentLoaded", function () {
    const tabla = document.querySelector("table tbody");
    const graficaCanvas = document.getElementById("graficaTitulacion");
    const filtroAnio = document.getElementById("filtro_anio");
    const filtroCarrera = document.getElementById("filtro_carrera");
    const filtroGrafica = document.getElementById("filtro_grafica");
    const botonPDF = document.getElementById("descargarPDF");

    // Extraer datos iniciales
    let datosOriginales = Array.from(tabla.querySelectorAll("tr")).map(tr => {
        const tds = tr.querySelectorAll("td");
        return {
            anio: tr.dataset.anio,
            carrera: tr.dataset.carrera,
            matricula: parseInt(tds[2].querySelector("input").value),
            egresados: parseInt(tds[3].querySelector("input").value),
            titulados: parseInt(tds[4].querySelector("input").value)
        };
    });

    function actualizarFiltros() {
        const anios = [...new Set(datosOriginales.map(d => d.anio))];
        const carreras = [...new Set(datosOriginales.map(d => d.carrera))];

        anios.forEach(anio => {
            const option = document.createElement("option");
            option.value = anio;
            option.textContent = anio;
            filtroAnio.appendChild(option);
        });

        carreras.forEach(carrera => {
            const option = document.createElement("option");
            option.value = carrera;
            option.textContent = carrera;
            filtroCarrera.appendChild(option);
        });
    }

    function obtenerSeleccionados(select) {
        return Array.from(select.selectedOptions).map(opt => opt.value);
    }

    function filtrarDatos() {
        let seleccionAnios = obtenerSeleccionados(filtroAnio);
        let seleccionCarreras = obtenerSeleccionados(filtroCarrera);

        return datosOriginales.filter(d => {
            const matchAnio = seleccionAnios.length ? seleccionAnios.includes(d.anio) : true;
            const matchCarrera = seleccionCarreras.length ? seleccionCarreras.includes(d.carrera) : true;
            return matchAnio && matchCarrera;
        });
    }

    function renderGrafica() {
        const datos = filtrarDatos();
        const tipo = filtroGrafica.value;

        const labels = datos.map(d => `${d.carrera} ${d.anio}`);
        const valores = datos.map(d => {
            return d.egresados > 0 ? parseFloat(((d.titulados / d.egresados) * 100).toFixed(2)) : 0;
        });

        if (window.miGrafica) {
            window.miGrafica.destroy();
        }

        window.miGrafica = new Chart(graficaCanvas, {
            type: tipo,
            data: {
                labels: labels,
                datasets: [{
                    label: '% Tasa de Titulación',
                    data: valores,
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: tipo !== 'bar',
                    }
                }
            }
        });
    }

    function exportarPDF() {
        const element = graficaCanvas;
        const opt = {
            margin: 0.3,
            filename: "tasa_titulacion.pdf",
            image: { type: "jpeg", quality: 0.98 },
            html2canvas: { scale: 2 },
            jsPDF: { unit: "in", format: "letter", orientation: "portrait" }
        };
        html2pdf().from(element).set(opt).save();
    }

    // Eventos
    filtroAnio.addEventListener("change", renderGrafica);
    filtroCarrera.addEventListener("change", renderGrafica);
    filtroGrafica.addEventListener("change", renderGrafica);
    botonPDF.addEventListener("click", exportarPDF);

    actualizarFiltros();
    renderGrafica();
});
