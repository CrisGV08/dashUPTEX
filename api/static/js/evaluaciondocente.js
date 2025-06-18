
document.addEventListener("DOMContentLoaded", () => {
    const etiquetas = JSON.parse(document.getElementById("etiquetas-data").textContent);
    const valores = JSON.parse(document.getElementById("valores-data").textContent);

    const charts = {
        linea: crearLinea(etiquetas, valores),
        barras: crearBarras(etiquetas, valores),
        pastel: crearPastel(etiquetas, valores),
        gauss: crearGauss(etiquetas, valores)
    };

    document.getElementById("btnAplicar").addEventListener("click", () => {
        const seleccionados = [...document.querySelectorAll('#filtro-ciclos option:checked')].map(opt => opt.value);
        const checks = [...document.querySelectorAll('.form-check-input')];

        // Mostrar/ocultar gráficas
        checks.forEach(chk => {
            document.getElementById(`grafico-${chk.value}-container`).style.display = chk.checked ? 'block' : 'none';
        });

        // Filtrar datos
        const nuevasEtiquetas = [], nuevosValores = [];
        etiquetas.forEach((et, i) => {
            if (seleccionados.includes(et)) {
                nuevasEtiquetas.push(et);
                nuevosValores.push(valores[i]);
            }
        });

        // Actualizar todas las gráficas
        Object.entries(charts).forEach(([key, chart]) => {
            chart.data.labels = nuevasEtiquetas;
            chart.data.datasets[0].data = key === 'gauss' ? calcularGauss(nuevosValores) : nuevosValores;
            chart.update();
        });
    });

    document.getElementById("btnReset").addEventListener("click", () => location.reload());

    function calcularGauss(datos) {
        const prom = datos.reduce((a, b) => a + b, 0) / datos.length;
        const sigma = Math.sqrt(datos.reduce((a, b) => a + Math.pow(b - prom, 2), 0) / datos.length);
        return datos.map(x => Math.exp(-Math.pow(x - prom, 2) / (2 * sigma * sigma)));
    }

    function crearLinea(labels, data) {
        return new Chart(document.getElementById("grafico-linea"), {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Promedio',
                    data: data,
                    borderColor: 'blue',
                    backgroundColor: 'rgba(0,123,255,0.2)',
                    tension: 0.3
                }]
            },
            options: { responsive: true }
        });
    }

    function crearBarras(labels, data) {
        return new Chart(document.getElementById("grafico-barras"), {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Promedio',
                    data: data,
                    backgroundColor: 'rgba(40,167,69,0.6)',
                    borderColor: 'green',
                    borderWidth: 1
                }]
            },
            options: { responsive: true }
        });
    }

    function crearPastel(labels, data) {
        return new Chart(document.getElementById("grafico-pastel"), {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: labels.map((_, i) => `hsl(${i * 40}, 70%, 70%)`)
                }]
            },
            options: { responsive: true }
        });
    }

    function crearGauss(labels, data) {
        return new Chart(document.getElementById("grafico-gauss"), {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Distribución Gaussiana',
                    data: calcularGauss(data),
                    borderColor: 'purple',
                    backgroundColor: 'rgba(123, 0, 255, 0.2)',
                    tension: 0.4
                }]
            },
            options: { responsive: true }
        });
    }
});


document.getElementById("btnDescargarPDF").addEventListener("click", async () => {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();
    const visibleCharts = [
        "grafico-linea-container",
        "grafico-barras-container",
        "grafico-pastel-container",
        "grafico-gauss-container"
    ];

    let yOffset = 10;

    for (const id of visibleCharts) {
        const container = document.getElementById(id);
        if (container.style.display !== 'none') {
            await html2canvas(container).then(canvas => {
                const imgData = canvas.toDataURL("image/png");
                const width = 180;
                const height = canvas.height * (width / canvas.width);
                doc.addImage(imgData, "PNG", 15, yOffset, width, height);
                yOffset += height + 10;
            });
        }
    }

    doc.save("graficas_evaluacion_docente.pdf");
});



