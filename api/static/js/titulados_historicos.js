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

    function renderGraficas() {
        destruirGraficas();
        const datosFiltrados = filtrarDatos();

        const etiquetas = datosFiltrados.map(d => `${d.nombre_programa} (${d.anio})`);
        const valores = datosFiltrados.map(d => d.total_titulados);

        const configEtiquetas = {
            plugins: {
                datalabels: {
                    color: '#000',
                    anchor: 'end',
                    align: 'top',
                    font: { weight: 'bold' },
                    formatter: Math.round
                },
                tooltip: { enabled: true },
                legend: { display: false }
            }
        };

        if (document.getElementById('grafica-lineal') && document.querySelector('.filtro-grafica[value="graficaLinea"]').checked) {
            const ctx = document.getElementById('grafica-lineal').getContext('2d');
            charts.linea = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: etiquetas,
                    datasets: [{
                        label: 'Total Titulados',
                        data: valores,
                        borderWidth: 2,
                        borderColor: '#2196F3',
                        backgroundColor: '#BBDEFB',
                        fill: false
                    }]
                },
                options: {
                    responsive: true,
                    ...configEtiquetas
                },
                plugins: [ChartDataLabels]
            });
        }

        if (document.getElementById('grafica-barras') && document.querySelector('.filtro-grafica[value="graficaBarras"]').checked) {
            const ctx = document.getElementById('grafica-barras').getContext('2d');
            charts.barras = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: etiquetas,
                    datasets: [{
                        label: 'Total Titulados',
                        data: valores,
                        backgroundColor: '#4CAF50'
                    }]
                },
                options: {
                    responsive: true,
                    ...configEtiquetas
                },
                plugins: [ChartDataLabels]
            });
        }

        if (document.getElementById('grafica-pastel') && document.querySelector('.filtro-grafica[value="graficaPastel"]').checked) {
            const ctx = document.getElementById('grafica-pastel').getContext('2d');
            charts.pastel = new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: etiquetas,
                    datasets: [{
                        label: 'Titulados',
                        data: valores,
                        backgroundColor: etiquetas.map(() => `hsl(${Math.random() * 360}, 70%, 60%)`)
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { position: 'bottom' },
                        datalabels: {
                            color: '#000',
                            formatter: Math.round
                        }
                    }
                },
                plugins: [ChartDataLabels]
            });
        }

        if (document.getElementById('grafica-gauss') && document.querySelector('.filtro-grafica[value="graficaGauss"]').checked) {
            const ctx = document.getElementById('grafica-gauss').getContext('2d');

            const media = valores.reduce((a, b) => a + b, 0) / valores.length;
            const desviacion = Math.sqrt(valores.map(x => Math.pow(x - media, 2)).reduce((a, b) => a + b, 0) / valores.length);

            const gaussLabels = Array.from({ length: 100 }, (_, i) =>
                media - 3 * desviacion + i * (6 * desviacion / 99)
            );
            const gaussData = gaussLabels.map(x =>
                (1 / (desviacion * Math.sqrt(2 * Math.PI))) *
                Math.exp(-0.5 * Math.pow((x - media) / desviacion, 2))
            );

            charts.gauss = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: gaussLabels.map(x => x.toFixed(1)),
                    datasets: [{
                        label: 'Distribución Gaussiana',
                        data: gaussData,
                        borderColor: '#FF9800',
                        backgroundColor: 'rgba(255, 152, 0, 0.3)',
                        borderWidth: 2,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
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
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2 },
        jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' }
    };
    html2pdf().set(opt).from(contenedor).save();
}
