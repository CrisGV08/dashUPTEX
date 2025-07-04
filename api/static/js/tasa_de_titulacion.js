document.addEventListener("DOMContentLoaded", function () {
    const datos = JSON.parse(document.getElementById("jsonDatos").textContent || "[]");

    const filtroAnio = document.getElementById("filtro_anio");
    const filtroPrograma = document.getElementById("filtro_programa");
    const filtroGrafica = document.getElementById("filtro_grafica");

    const ctxLinea = document.getElementById("graficaLinea").getContext("2d");
    const ctxBarras = document.getElementById("graficaBarras").getContext("2d");
    const ctxPastel = document.getElementById("graficaPastel").getContext("2d");
    const ctxGauss = document.getElementById("graficaGauss").getContext("2d");

    let chartLinea, chartBarras, chartPastel, chartGauss;

    // Inicializar filtros con todas las opciones seleccionadas
    function inicializarFiltros() {
        const anios = [...new Set(datos.map(d => d.anio_ingreso))].sort();
        const programas = [...new Set(datos.map(d => d.programa))].sort();

        anios.forEach(anio => {
            const opt = new Option(anio, anio);
            opt.selected = true;
            filtroAnio.add(opt);
        });

        programas.forEach(p => {
            const opt = new Option(p, p);
            opt.selected = true;
            filtroPrograma.add(opt);
        });

        Array.from(filtroGrafica.options).forEach(opt => opt.selected = true);
    }

    function obtenerSeleccionados(select) {
        return Array.from(select.selectedOptions).map(opt => opt.value);
    }

    function filtrarDatos() {
        const anios = obtenerSeleccionados(filtroAnio);
        const programas = obtenerSeleccionados(filtroPrograma);
        return datos
            .filter(d => anios.includes(d.anio_ingreso.toString()) && programas.includes(d.programa))
            .sort((a, b) => a.anio_ingreso - b.anio_ingreso);
    }

    function crearGraficas() {
        const filtrados = filtrarDatos();
        const visibleGraficas = obtenerSeleccionados(filtroGrafica);

        // Destruir gráficas existentes
        if (chartLinea) chartLinea.destroy();
        if (chartBarras) chartBarras.destroy();
        if (chartPastel) chartPastel.destroy();
        if (chartGauss) chartGauss.destroy();

        // Ocultar todas
        document.querySelectorAll(".grafica").forEach(div => div.style.display = "none");

        if (filtrados.length === 0) return;

        const etiquetas = filtrados.map(d => `${d.programa} (${d.anio_ingreso})`);
        const valores = filtrados.map(d => d.tasa_titulacion);

        const data = {
            labels: etiquetas,
            datasets: [{
                label: 'Tasa de Titulación (%)',
                data: valores,
                backgroundColor: 'rgba(76, 175, 80, 0.4)',
                borderColor: 'rgba(76, 175, 80, 1)',
                borderWidth: 2,
                fill: true
            }]
        };

        if (visibleGraficas.includes("linea")) {
            document.getElementById("graficaLinea").parentElement.style.display = "block";
            chartLinea = new Chart(ctxLinea, {
                type: 'line',
                data,
                options: { responsive: true, maintainAspectRatio: false }
            });
        }

        if (visibleGraficas.includes("barras")) {
            document.getElementById("graficaBarras").parentElement.style.display = "block";
            chartBarras = new Chart(ctxBarras, {
                type: 'bar',
                data,
                options: { responsive: true, maintainAspectRatio: false }
            });
        }

        if (visibleGraficas.includes("pastel")) {
            document.getElementById("graficaPastel").parentElement.style.display = "block";
            chartPastel = new Chart(ctxPastel, {
                type: 'pie',
                data,
                options: { responsive: true, maintainAspectRatio: false }
            });
        }

        if (visibleGraficas.includes("gauss")) {
            document.getElementById("graficaGauss").parentElement.style.display = "block";
            const puntos = valores.map((y, i) => ({ x: i, y }));
            chartGauss = new Chart(ctxGauss, {
                type: 'line',
                data: {
                    datasets: [{
                        label: 'Distribución Gaussiana (simulada)',
                        data: puntos,
                        fill: false,
                        borderColor: 'rgba(33, 150, 243, 0.8)',
                        backgroundColor: 'rgba(33, 150, 243, 0.2)',
                        tension: 0.3
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: { title: { display: true, text: 'Índice' } },
                        y: { title: { display: true, text: 'Tasa (%)' } }
                    }
                }
            });
        }
    }

    // Exportar las gráficas visibles a PDF
    function descargarPDF() {
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF();
        let y = 10;

        document.querySelectorAll("canvas").forEach(canvas => {
            if (canvas.offsetParent !== null) {
                const img = canvas.toDataURL("image/png");
                doc.addImage(img, "PNG", 10, y, 180, 60);
                y += 70;
                if (y > 250) {
                    doc.addPage();
                    y = 10;
                }
            }
        });

        doc.save("tasa_titulacion.pdf");
    }

    // Eventos
    filtroAnio.addEventListener("change", crearGraficas);
    filtroPrograma.addEventListener("change", crearGraficas);
    filtroGrafica.addEventListener("change", crearGraficas);
    window.descargarPDF = descargarPDF;

    // Inicialización
    inicializarFiltros();
    crearGraficas();
});
