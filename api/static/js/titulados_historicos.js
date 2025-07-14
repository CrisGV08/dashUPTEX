document.addEventListener('DOMContentLoaded', function () {
    const charts = {};
    const datos = datosTitulados || [];

    function filtrarDatos() {
        return datos;
    }

    function destruirGraficas() {
        Object.values(charts).forEach(chart => chart.destroy());
        Object.keys(charts).forEach(k => delete charts[k]);
    }

    function generarColoresPastel(n) {
        const colores = [];
        for (let i = 0; i < n; i++) {
            const hue = (i * 360 / n) % 360;
            colores.push(`hsl(${hue}, 70%, 65%)`);
        }
        return colores;
    }

    function renderGraficas() {
        destruirGraficas();
        const datosFiltrados = filtrarDatos();
        if (datosFiltrados.length === 0) return;

        const etiquetas = datosFiltrados.map(d => `${d.nombre_programa} (${d.anio})`);
        const valores = datosFiltrados.map(d => d.total_titulados);

        const configEtiquetas = {
            responsive: true,
            devicePixelRatio: 3,
            animation: false,
            plugins: {
                datalabels: {
                    color: '#000',
                    anchor: 'end',
                    align: 'top',
                    font: { weight: 'bold', size: 13 },
                    formatter: Math.round
                },
                tooltip: { enabled: true },
                legend: { display: false }
            }
        };

        // Gráfico de Línea
        if (document.getElementById('grafica-lineal') && document.querySelector('.filtro-grafica[value="graficaLinea"]').checked) {
            const ctx = document.getElementById('grafica-lineal').getContext('2d');
            charts.linea = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: etiquetas,
                    datasets: [{
                        label: 'Total Titulados',
                        data: valores,
                        borderColor: '#1976D2',
                        backgroundColor: '#BBDEFB',
                        borderWidth: 2,
                        fill: false
                    }]
                },
                options: configEtiquetas,
                plugins: [ChartDataLabels]
            });
        }

        // Gráfico de Barras
        if (document.getElementById('grafica-barras') && document.querySelector('.filtro-grafica[value="graficaBarras"]').checked) {
            const ctx = document.getElementById('grafica-barras').getContext('2d');
            charts.barras = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: etiquetas,
                    datasets: [{
                        label: 'Total Titulados',
                        data: valores,
                        backgroundColor: '#43A047'
                    }]
                },
                options: configEtiquetas,
                plugins: [ChartDataLabels]
            });
        }

        // Gráfico Pastel
        if (document.getElementById('grafica-pastel') && document.querySelector('.filtro-grafica[value="graficaPastel"]').checked) {
            const ctx = document.getElementById('grafica-pastel').getContext('2d');
            charts.pastel = new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: etiquetas,
                    datasets: [{
                        data: valores,
                        backgroundColor: generarColoresPastel(etiquetas.length)
                    }]
                },
                options: {
                    responsive: true,
                    animation: false,
                    plugins: {
                        legend: { position: 'bottom' },
                        datalabels: {
                            color: '#000',
                            font: { weight: 'bold', size: 13 },
                            formatter: Math.round
                        }
                    }
                },
                plugins: [ChartDataLabels]
            });
        }

        // Gráfico Gauss
        if (document.getElementById('grafica-gauss') && document.querySelector('.filtro-grafica[value="graficaGauss"]').checked) {
            const ctx = document.getElementById('grafica-gauss').getContext('2d');
            const media = valores.reduce((a, b) => a + b, 0) / valores.length;
            const desviacion = Math.sqrt(valores.map(x => Math.pow(x - media, 2)).reduce((a, b) => a + b, 0) / valores.length);
            const gaussLabels = Array.from({ length: 100 }, (_, i) => media - 3 * desviacion + (i * (6 * desviacion / 99)));
            const gaussData = gaussLabels.map(x =>
                (1 / (desviacion * Math.sqrt(2 * Math.PI))) * Math.exp(-0.5 * Math.pow((x - media) / desviacion, 2))
            );

            charts.gauss = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: gaussLabels.map(x => x.toFixed(1)),
                    datasets: [{
                        label: 'Distribución Gaussiana',
                        data: gaussData,
                        borderColor: '#FF5722',
                        backgroundColor: 'rgba(255, 87, 34, 0.2)',
                        borderWidth: 2,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    animation: false,
                    plugins: {
                        tooltip: { enabled: false },
                        legend: { display: false }
                    },
                    scales: {
                        y: { ticks: { display: false }, grid: { display: false } },
                        x: { ticks: { display: false }, grid: { display: false } }
                    }
                }
            });
        }
    }

    document.querySelectorAll('.filtro-grafica').forEach(input => {
        input.addEventListener('change', renderGraficas);
    });

    renderGraficas();
});

function exportarPDF() {
    const contenedor = document.getElementById('contenedorGraficas');
    const opt = {
        margin: 0.5,
        filename: 'titulados_historicos.pdf',
        image: { type: 'jpeg', quality: 1 },
        html2canvas: {
            scale: 3,
            useCORS: true,
            allowTaint: true
        },
        jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' }
    };
    html2pdf().set(opt).from(contenedor).save();
}
