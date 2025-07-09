// Obtener datos desde los atributos data-* del contenedor invisible
const contenedor = document.getElementById("datosGraficas");
const datos = {
    examen: parseInt(contenedor.dataset.examen),
    renoes: parseInt(contenedor.dataset.renoes),
    uaem_gem: parseInt(contenedor.dataset.uaem_gem),         // <- así en snake_case
    pase_directo: parseInt(contenedor.dataset.pase_directo)  // <- así en snake_case
};


const etiquetas = {
    examen: "Examen",
    renoes: "RENOES",
    uaem_gem: "UAEM-GEM",
    pase_directo: "Pase Directo"
};

let charts = {};

function calcularGauss(data) {
    const mean = data.reduce((a, b) => a + b, 0) / data.length;
    const stdDev = Math.sqrt(data.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / data.length);
    return data.map(x => Math.exp(-Math.pow(x - mean, 2) / (2 * stdDev * stdDev)));
}

function renderGraficas(seleccionadas, modalidades) {
    const keys = modalidades.length ? modalidades : Object.keys(datos);
    const labels = keys.map(k => etiquetas[k]);
    const values = keys.map(k => datos[k]);

    Object.values(charts).forEach(chart => chart.destroy());
    charts = {};

    const pluginDatalabels = {
        plugins: [ChartDataLabels],
        options: {
            plugins: {
                datalabels: {
                    anchor: 'end',
                    align: 'top',
                    formatter: Math.round,
                    font: { weight: 'bold' }
                }
            }
        }
    };

    if (seleccionadas.includes("barras")) {
        charts.barras = new Chart(document.getElementById("graficaBarras"), {
            type: "bar",
            data: {
                labels: labels,
                datasets: [{
                    label: "Total por modalidad",
                    data: values,
                    backgroundColor: ['#007bff', '#fd7e14', '#28a745', '#dc3545']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: pluginDatalabels.options.plugins
            },
            plugins: pluginDatalabels.plugins
        });
    }

    if (seleccionadas.includes("linea")) {
        charts.linea = new Chart(document.getElementById("graficaLinea"), {
            type: "line",
            data: {
                labels: labels,
                datasets: [{
                    label: "Total por modalidad",
                    data: values,
                    borderColor: "#17a2b8",
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: pluginDatalabels.options.plugins
            },
            plugins: pluginDatalabels.plugins
        });
    }

    if (seleccionadas.includes("pastel")) {
        charts.pastel = new Chart(document.getElementById("graficaPastel"), {
            type: "pie",
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: ['#007bff', '#fd7e14', '#28a745', '#dc3545']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: pluginDatalabels.options.plugins
            },
            plugins: pluginDatalabels.plugins
        });
    }

    if (seleccionadas.includes("gauss")) {
        const gaussValues = calcularGauss(values);
        charts.gauss = new Chart(document.getElementById("graficaGauss"), {
            type: "line",
            data: {
                labels: labels,
                datasets: [{
                    label: "Campana de Gauss",
                    data: gaussValues,
                    borderColor: "purple",
                    backgroundColor: "rgba(153, 102, 255, 0.2)",
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }
}

document.getElementById("aplicarFiltros").addEventListener("click", () => {
    const graficas = [...document.querySelectorAll(".grafica-check:checked")].map(g => g.value);
    const modalidades = [...document.querySelectorAll(".modalidad-check:checked")].map(m => m.value);
    document.querySelectorAll(".grafica-box").forEach(div => {
        div.style.display = graficas.includes(div.id.replace("box-", "")) ? "block" : "none";
    });
    renderGraficas(graficas, modalidades);
});

document.getElementById("resetFiltros").addEventListener("click", () => location.reload());

renderGraficas(["barras", "linea", "pastel", "gauss"], Object.keys(datos));

document.getElementById("btnDescargarPDF").addEventListener("click", async () => {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();
    const pageWidth = doc.internal.pageSize.getWidth();
    doc.setFont("helvetica", "bold");
    doc.setFontSize(16);
    doc.text("Examen de Admisión", pageWidth / 2, 20, { align: "center" });

    const graficas = ["box-barras", "box-linea", "box-pastel", "box-gauss"];
    let y = 30;

    for (const id of graficas) {
        const container = document.getElementById(id);
        if (container && container.style.display !== "none") {
            const canvas = container.querySelector("canvas");
            await html2canvas(canvas, {
                scale: 2,
                useCORS: true
            }).then(c => {
                const imgData = c.toDataURL("image/png");
                const width = 180;
                const height = c.height * (width / c.width);
                if (y + height > 270) {
                    doc.addPage();
                    y = 20;
                }
                doc.addImage(imgData, "PNG", 15, y, width, height);
                y += height + 10;
            });
        }
    }

    doc.save("Examen_de_Admision.pdf");
});
