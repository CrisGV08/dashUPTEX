document.addEventListener("DOMContentLoaded", function () {
    const datos = datosDashboard;
    const labelsOriginal = datos.labels;
    const totalesOriginal = datos.totales;
    const totalAntiguosOriginal = datos.total_antiguos;
    const totalNuevosOriginal = datos.total_nuevos;
    const programasTotales = datos.programas_totales;

    const ctxLinea = document.getElementById("graficoLinea");
    const ctxBarras = document.getElementById("graficoBarras");
    const ctxPastel = document.getElementById("graficoPastel");
    const ctxGauss = document.getElementById("graficoGauss");

    const calcularGauss = (data) => {
        const mean = data.reduce((a, b) => a + b, 0) / data.length;
        const std = Math.sqrt(data.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / data.length);
        return data.map(x => Math.exp(-Math.pow(x - mean, 2) / (2 * std * std)));
    };

    const opcionesComunes = {
        responsive: true,
        plugins: {
            tooltip: { enabled: true },
            legend: { display: true },
            datalabels: {
                display: true,
                color: '#111',
                font: { weight: 'bold' },
                formatter: Math.round
            }
        },
        scales: { y: { beginAtZero: true } }
    };

    const graficaLinea = new Chart(ctxLinea, {
        type: 'line',
        data: {
            labels: labelsOriginal,
            datasets: [{
                label: 'Total por ciclo',
                data: totalesOriginal,
                borderColor: '#007bff',
                backgroundColor: 'rgba(0,123,255,0.2)',
                fill: true,
                tension: 0.3
            }]
        },
        options: opcionesComunes,
        plugins: [ChartDataLabels]
    });

    const graficaBarras = new Chart(ctxBarras, {
        type: 'bar',
        data: {
            labels: labelsOriginal,
            datasets: [{
                label: 'Total por ciclo',
                data: totalesOriginal,
                backgroundColor: 'rgba(40,167,69,0.6)',
                borderColor: '#28a745',
                borderWidth: 2
            }]
        },
        options: opcionesComunes,
        plugins: [ChartDataLabels]
    });

    const graficaPastel = new Chart(ctxPastel, {
        type: 'pie',
        data: {
            labels: ['Programas Antiguos', 'Programas Nuevos'],
            datasets: [{
                data: [totalAntiguosOriginal, totalNuevosOriginal],
                backgroundColor: ['#ffc107', '#6610f2']
            }]
        },
        options: opcionesComunes,
        plugins: [ChartDataLabels]
    });

    const graficaGauss = new Chart(ctxGauss, {
        type: 'line',
        data: {
            labels: labelsOriginal,
            datasets: [{
                label: 'Distribución (Gauss)',
                data: calcularGauss(totalesOriginal),
                borderColor: '#dc3545',
                backgroundColor: 'rgba(220,53,69,0.3)',
                fill: true,
                tension: 0.3
            }]
        },
        options: opcionesComunes,
        plugins: [ChartDataLabels]
    });

    const actualizarTotalesPorCiclo = (labelsFiltrados) => {
        let totalAntiguosFiltrado = 0;
        let totalNuevosFiltrado = 0;
        labelsFiltrados.forEach(label => {
            const index = labelsOriginal.indexOf(label);
            totalAntiguosFiltrado += programasTotales["Programas Antiguos"]?.[index] || 0;
            totalNuevosFiltrado += programasTotales["Programas Nuevos"]?.[index] || 0;
        });
        return [totalAntiguosFiltrado, totalNuevosFiltrado];
    };

    const filtroCiclos = document.getElementById("filtro-ciclos");
    filtroCiclos.addEventListener("change", function () {
        const seleccionados = Array.from(this.selectedOptions).map(op => op.value);
        const nuevosLabels = labelsOriginal.filter(l => seleccionados.includes(l));
        const nuevosTotales = labelsOriginal.map((l, i) => seleccionados.includes(l) ? totalesOriginal[i] : null).filter(x => x !== null);

        graficaLinea.data.labels = nuevosLabels;
        graficaLinea.data.datasets[0].data = nuevosTotales;
        graficaLinea.update();

        graficaBarras.data.labels = nuevosLabels;
        graficaBarras.data.datasets[0].data = nuevosTotales;
        graficaBarras.update();

        graficaGauss.data.labels = nuevosLabels;
        graficaGauss.data.datasets[0].data = calcularGauss(nuevosTotales);
        graficaGauss.update();

        const [nuevoAntiguos, nuevoNuevos] = actualizarTotalesPorCiclo(nuevosLabels);
        graficaPastel.data.datasets[0].data = [nuevoAntiguos, nuevoNuevos];
        graficaPastel.update();
    });

    document.getElementById("descargarPDF").addEventListener("click", () => {
        const charts = [
            { id: "container-linea", title: "Gráfico de Línea" },
            { id: "container-barras", title: "Gráfico de Barras" },
            { id: "container-pastel", title: "Gráfico de Pastel" },
            { id: "container-gauss", title: "Distribución Gauss" }
        ];

        const pdf = new window.jspdf.jsPDF();
        pdf.setFontSize(16);
        pdf.text("📘 Matrícula Histórico de Nuevo Ingreso", 105, 15, null, null, "center");

        let y = 30;
        charts.forEach(({ id, title }) => {
            const contenedor = document.getElementById(id);
            if (contenedor && contenedor.style.display !== "none") {
                const canvas = contenedor.querySelector("canvas");
                if (canvas) {
                    const img = canvas.toDataURL("image/png");
                    pdf.setFontSize(12);
                    pdf.text(title, 105, y, null, null, "center");
                    y += 5;
                    pdf.addImage(img, "PNG", 15, y, 180, 80);
                    y += 90;
                    if (y > 250) {
                        pdf.addPage();
                        y = 20;
                    }
                }
            }
        });

        pdf.save("matricula_h_nuevo_ingreso.pdf");
    });
});
