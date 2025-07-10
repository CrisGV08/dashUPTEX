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

    const crearConfig = (type, label, data, color, bg) => ({
        type: type,
        data: {
            labels: labelsOriginal,
            datasets: [{
                label: label,
                data: data,
                backgroundColor: bg,
                borderColor: color,
                borderWidth: 2,
                fill: true,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            plugins: {
                tooltip: { enabled: true },
                legend: { display: true },
                datalabels: {
                    anchor: 'end',
                    align: 'top',
                    color: '#000',
                    font: { weight: 'bold' },
                    formatter: Math.round
                }
            },
            scales: {
                y: { beginAtZero: true }
            }
        },
        plugins: [ChartDataLabels]
    });

    const graficaLinea = new Chart(ctxLinea, crearConfig('line', 'Total por ciclo', totalesOriginal, '#007bff', 'rgba(0,123,255,0.2)'));
    const graficaBarras = new Chart(ctxBarras, crearConfig('bar', 'Total por ciclo', totalesOriginal, '#28a745', 'rgba(40,167,69,0.6)'));
    const graficaGauss = new Chart(ctxGauss, crearConfig('line', 'Distribución (Gauss)', calcularGauss(totalesOriginal), '#dc3545', 'rgba(220,53,69,0.3)'));

    const graficaPastel = new Chart(ctxPastel, {
        type: 'pie',
        data: {
            labels: ['Programas Antiguos', 'Programas Nuevos'],
            datasets: [{
                data: [totalAntiguosOriginal, totalNuevosOriginal],
                backgroundColor: ['#ffc107', '#6610f2']
            }]
        },
        options: {
            responsive: true,
            plugins: {
                tooltip: { enabled: true },
                legend: { display: true },
                datalabels: {
                    color: '#000',
                    font: { weight: 'bold' },
                    formatter: (value) => `${value}`
                }
            }
        },
        plugins: [ChartDataLabels]
    });

    const checkboxConfig = [
        { id: "graficaLineal", container: "container-linea", chart: graficaLinea },
        { id: "graficaBarras", container: "container-barras", chart: graficaBarras },
        { id: "graficaPastel", container: "container-pastel", chart: graficaPastel },
        { id: "graficaGauss", container: "container-gauss", chart: graficaGauss }
    ];

    checkboxConfig.forEach(({ id, container, chart }) => {
        document.getElementById(id).addEventListener("change", function () {
            const div = document.getElementById(container);
            div.style.display = this.checked ? "block" : "none";
            chart.resize();
        });
    });

    const actualizarTotalesPorCiclo = (labelsFiltrados) => {
        let totalAntiguosFiltrado = 0;
        let totalNuevosFiltrado = 0;

        labelsFiltrados.forEach((label) => {
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
});

document.getElementById("descargarPDF").addEventListener("click", async () => {
    const { jsPDF } = window.jspdf;
    const titulo = " Matrícula Histórico de Nuevo Ingreso";
    const elementosGraficas = [];

    const charts = [
        { id: "container-linea", title: "Gráfico de Línea" },
        { id: "container-barras", title: "Gráfico de Barras" },
        { id: "container-pastel", title: "Gráfico de Pastel" },
        { id: "container-gauss", title: "Distribución Gauss" }
    ];

    charts.forEach(({ id, title }) => {
        const contenedor = document.getElementById(id);
        if (contenedor && contenedor.style.display !== "none") {
            const canvas = contenedor.querySelector("canvas");
            if (canvas) {
                const imgData = canvas.toDataURL("image/png");
                elementosGraficas.push({ title, imgData });
            }
        }
    });

    const pdf = new jsPDF();
    pdf.setFontSize(16);
    pdf.text(titulo, 105, 15, null, null, "center");

    let y = 30;
    elementosGraficas.forEach(({ title, imgData }) => {
        pdf.setFontSize(12);
        pdf.text(title, 105, y, null, null, "center");
        y += 5;
        pdf.addImage(imgData, "PNG", 15, y, 180, 80);
        y += 90;

        if (y > 250) {
            pdf.addPage();
            y = 20;
        }
    });

    pdf.save("matricula_nuevo_ingreso.pdf");
});
