document.addEventListener("DOMContentLoaded", function () {
    const elementos = {
        datos: document.getElementById("datosGraficas"),
        filtroCiclo: document.getElementById("filtroAnio"),
        btnAplicar: document.getElementById("aplicarFiltros"),
        btnReset: document.getElementById("resetFiltros"),
        btnPDF: document.getElementById("btnDescargarPDF"),
        checkboxes: document.querySelectorAll(".grafica-check")
    };

    let datos;
    try {
        datos = JSON.parse(elementos.datos.textContent);
    } catch (error) {
        console.error("Error al parsear datos:", error);
        return;
    }

    const charts = {};
    const colores = ['#28a745'];

    function renderGraficas(tiposGraficas) {
        Object.values(charts).forEach(chart => chart && chart.destroy());

        const labels = ['Eficiencia Terminal %'];
        const valores = [parseFloat(datos.eficiencia) || 0];

        const configComun = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top' },
                datalabels: {
                    anchor: 'end',
                    align: 'top',
                    formatter: value => value + '%',
                    font: { weight: 'bold' }
                }
            }
        };

        if (tiposGraficas.includes("barras")) {
            charts.barras = new Chart(document.getElementById("graficaBarras"), {
                type: 'bar',
                data: {
                    labels,
                    datasets: [{
                        label: 'Porcentaje',
                        data: valores,
                        backgroundColor: colores,
                        borderColor: colores,
                        borderWidth: 1
                    }]
                },
                options: configComun,
                plugins: [ChartDataLabels]
            });
        }

        if (tiposGraficas.includes("linea")) {
            charts.linea = new Chart(document.getElementById("graficaLinea"), {
                type: 'line',
                data: {
                    labels,
                    datasets: [{
                        label: 'Porcentaje',
                        data: valores,
                        borderColor: colores[0],
                        backgroundColor: 'rgba(40,167,69,0.2)',
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: configComun,
                plugins: [ChartDataLabels]
            });
        }

        if (tiposGraficas.includes("pastel")) {
            charts.pastel = new Chart(document.getElementById("graficaPastel"), {
                type: 'pie',
                data: {
                    labels,
                    datasets: [{
                        data: valores,
                        backgroundColor: colores,
                        borderColor: '#fff',
                        borderWidth: 2
                    }]
                },
                options: configComun,
                plugins: [ChartDataLabels]
            });
        }

        if (tiposGraficas.includes("gauss")) {
            const calcularGauss = (data) => {
                const mean = data.reduce((a, b) => a + b, 0) / data.length;
                const stdDev = Math.sqrt(data.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / data.length);
                return data.map(x => Math.exp(-Math.pow(x - mean, 2) / (2 * Math.pow(stdDev, 2))));
            };

            charts.gauss = new Chart(document.getElementById("graficaGauss"), {
                type: 'line',
                data: {
                    labels,
                    datasets: [{
                        label: 'Distribución Gaussiana',
                        data: calcularGauss(valores),
                        borderColor: '#9966FF',
                        backgroundColor: 'rgba(153, 102, 255, 0.2)',
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

    function getGraficasSeleccionadas() {
        return Array.from(elementos.checkboxes)
            .filter(cb => cb.checked)
            .map(cb => cb.value);
    }

    function aplicarFiltros() {
        const seleccionadas = getGraficasSeleccionadas();
        document.querySelectorAll(".grafica-box").forEach(div => {
            const tipo = div.id.replace("box-", "");
            div.style.display = seleccionadas.includes(tipo) ? "block" : "none";
        });
        renderGraficas(seleccionadas);
    }

    elementos.btnAplicar.addEventListener('click', aplicarFiltros);
    elementos.btnReset.addEventListener('click', function () {
        elementos.checkboxes.forEach(cb => cb.checked = true);
        aplicarFiltros();
    });

    elementos.btnPDF.addEventListener('click', async function () {
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF();
        doc.setFontSize(16);
        doc.text("Reporte de Eficiencia Terminal", 105, 15, { align: "center" });

        const graficas = ["box-barras", "box-linea", "box-pastel", "box-gauss"];
        let y = 30;

        for (const id of graficas) {
            const container = document.getElementById(id);
            if (container && container.style.display !== "none") {
                const canvas = container.querySelector("canvas");
                if (canvas) {
                    await html2canvas(canvas, { scale: 2 }).then(c => {
                        const imgData = c.toDataURL('image/png');
                        const width = 180;
                        const height = c.height * width / c.width;

                        if (y + height > doc.internal.pageSize.getHeight() - 20) {
                            doc.addPage();
                            y = 20;
                        }

                        doc.addImage(imgData, 'PNG', 15, y, width, height);
                        y += height + 10;
                    });
                }
            }
        }

        doc.save('eficiencia_terminal.pdf');
    });

    aplicarFiltros();
});
