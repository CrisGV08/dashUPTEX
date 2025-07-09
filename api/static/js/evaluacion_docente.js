// evaluacion_docente.js

const charts = {};

// Plugin para mostrar valores encima de cada dato
const mostrarEtiquetas = {
    id: 'mostrarEtiquetas',
    afterDatasetsDraw(chart) {
        const { ctx } = chart;
        chart.data.datasets.forEach((dataset, i) => {
            const meta = chart.getDatasetMeta(i);
            if (!meta.hidden) {
                meta.data.forEach((element, index) => {
                    ctx.save();
                    ctx.fillStyle = 'black';
                    ctx.font = 'bold 11px sans-serif';
                    ctx.textAlign = 'center';
                    ctx.fillText(dataset.data[index], element.x, element.y - 10);
                    ctx.restore();
                });
            }
        });
    }
};

// Gráficos principales
function crearGraficos(etiquetas, valores) {
    // Línea
    charts.linea = new Chart(document.getElementById("grafico-linea"), {
        type: 'line',
        data: {
            labels: etiquetas,
            datasets: [{
                label: 'Promedio',
                data: valores,
                backgroundColor: 'rgba(0,123,255,0.2)',
                borderColor: '#007bff',
                fill: true,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            plugins: {
                tooltip: { enabled: true },
                datalabels: {
                    color: 'black',
                    font: { weight: 'bold' },
                    formatter: val => val
                }
            }
        },
        plugins: [ChartDataLabels]
    });

    // Barras
    charts.barras = new Chart(document.getElementById("grafico-barras"), {
        type: 'bar',
        data: {
            labels: etiquetas,
            datasets: [{
                label: 'Promedio',
                data: valores,
                backgroundColor: '#28a745'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                tooltip: { enabled: true },
                datalabels: {
                    color: 'black',
                    font: { weight: 'bold' },
                    anchor: 'end',
                    align: 'start',
                    formatter: val => val
                }
            },
            scales: {
                x: {
                    ticks: {
                        autoSkip: false,
                        maxRotation: 60,
                        minRotation: 45
                    }
                }
            }
        },
        plugins: [ChartDataLabels]
    });

    // Pastel
    charts.pastel = new Chart(document.getElementById("grafico-pastel"), {
        type: 'pie',
        data: {
            labels: etiquetas,
            datasets: [{
                data: valores,
                backgroundColor: etiquetas.map((_, i) => `hsl(${i * 60}, 70%, 70%)`)
            }]
        },
        options: {
            responsive: true,
            plugins: {
                tooltip: { enabled: true },
                datalabels: {
                    color: 'black',
                    font: {
                        weight: 'bold',
                        size: 14
                    },
                    formatter: val => val
                }
            }
        },
        plugins: [ChartDataLabels]
    });

    // Gauss
    charts.gauss = new Chart(document.getElementById("grafico-gauss"), {
        type: 'line',
        data: {
            labels: etiquetas,
            datasets: [{
                label: 'Distribución Gaussiana',
                data: calcularGauss(valores),
                borderColor: '#6f42c1',
                backgroundColor: 'rgba(111,66,193,0.2)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            plugins: {
                tooltip: { enabled: true },
                datalabels: {
                    color: '#6f42c1',
                    anchor: 'end',
                    align: 'start',
                    font: { weight: 'bold' },
                    formatter: val => val.toFixed(2)
                }
            }
        },
        plugins: [ChartDataLabels]
    });
}

// Gaussiana
function calcularGauss(datos) {
    const prom = datos.reduce((a, b) => a + b, 0) / datos.length;
    const sigma = Math.sqrt(datos.reduce((a, b) => a + (b - prom) ** 2, 0) / datos.length);
    return datos.map(x => Math.exp(-Math.pow(x - prom, 2) / (2 * sigma ** 2)));
}

// Filtros
document.getElementById("btnAplicar").addEventListener("click", () => {
    const seleccionados = [...document.querySelectorAll('#filtro-ciclos option:checked')].map(opt => opt.value.trim());
    const checks = [...document.querySelectorAll('.form-check-input')];

    checks.forEach(chk => {
        document.getElementById(`grafico-${chk.value}-container`).style.display = chk.checked ? 'block' : 'none';
    });

    const nuevasEtiquetas = [];
    const nuevosValores = [];

    etiquetas.forEach((et, i) => {
        if (seleccionados.includes(et.trim())) {
            nuevasEtiquetas.push(et);
            nuevosValores.push(promedios[i]);
        }
    });

    Object.entries(charts).forEach(([key, chart]) => {
        chart.data.labels = nuevasEtiquetas;
        chart.data.datasets[0].data = (key === 'gauss') ? calcularGauss(nuevosValores) : nuevosValores;
        chart.update();
    });
});

// Reset filtros
document.getElementById("btnReset").addEventListener("click", () => location.reload());

// PDF
document.getElementById("btnDescargarPDF").addEventListener("click", async () => {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();
    const pageWidth = doc.internal.pageSize.getWidth();

    doc.setFont("helvetica", "bold");
    doc.setFontSize(14);
    doc.text("Evaluación Docente por Cuatrimestre", pageWidth / 2, 20, { align: "center" });

    const visibleCharts = [
        "grafico-linea-container",
        "grafico-barras-container",
        "grafico-pastel-container",
        "grafico-gauss-container"
    ];

    let yOffset = 30;

    for (const id of visibleCharts) {
        const container = document.getElementById(id);
        if (container && container.style.display !== 'none') {
            await html2canvas(container, { scale: 3 }).then(canvas => {
                const width = 180;
                const height = canvas.height * (width / canvas.width);

                if (yOffset + height > 280) {
                    doc.addPage();
                    yOffset = 20;
                }

                doc.addImage(canvas.toDataURL("image/png"), "PNG", 10, yOffset, width, height);
                yOffset += height + 10;
            });
        }
    }

    doc.save("Evaluacion_Docente_por_Cuatrimestre.pdf");
});

// Select estilizado (Choices.js)
const cicloSelect = document.getElementById('filtro-ciclos');
new Choices(cicloSelect, {
    removeItemButton: true,
    placeholderValue: 'Selecciona ciclos...',
    searchPlaceholderValue: 'Buscar...',
    noResultsText: 'Sin resultados',
});

// Ejecutar al cargar
document.addEventListener('DOMContentLoaded', () => crearGraficos(etiquetas, promedios));
