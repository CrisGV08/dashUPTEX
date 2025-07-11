document.addEventListener('DOMContentLoaded', function () {
    const datosGeneraciones = JSON.parse(document.getElementById('jsonDatos').textContent);
    const selectCarreras = document.getElementById('selectCarreras');
    const selectGraficas = document.getElementById('selectGraficas');

    const charts = {
        linea: null,
        barras: null,
        pastel: null,
        gauss: null
    };

    const colores = [
        '#4e79a7', '#f28e2b', '#e15759', '#76b7b2',
        '#59a14f', '#edc949', '#af7aa1', '#ff9da7',
        '#9c755f', '#bab0ab'
    ];

    new Choices(selectCarreras, {
        removeItemButton: true,
        placeholderValue: 'Selecciona una o más carreras',
        searchEnabled: true
    });

    new Choices(selectGraficas, {
        removeItemButton: true,
        placeholderValue: 'Selecciona tipo de gráfica'
    });

    function actualizarGraficas() {
        const carrerasSeleccionadas = Array.from(selectCarreras.selectedOptions).map(op => op.value);
        const tiposGraficas = Array.from(selectGraficas.selectedOptions).map(op => op.value);

        const datosFiltrados = datosGeneraciones.filter(reg => {
            const etiqueta = `${reg.nombre_programa} (${reg.anio})`;
            return carrerasSeleccionadas.length === 0 || carrerasSeleccionadas.includes(etiqueta);
        });

        const etiquetas = datosFiltrados.map(reg => `${reg.nombre_programa} (${reg.anio})`);
        const valores = datosFiltrados.map(reg => reg.tasa_titulacion);

        // Destruir gráficas anteriores si existen
        Object.keys(charts).forEach(tipo => {
            if (charts[tipo]) {
                charts[tipo].destroy();
                charts[tipo] = null;
            }
        });

        // Línea
        if (tiposGraficas.includes('linea')) {
            const ctx = document.getElementById('graficaLinea').getContext('2d');
            charts.linea = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: etiquetas,
                    datasets: [{
                        label: 'Tasa de Titulación',
                        data: valores,
                        borderColor: colores[0],
                        fill: false,
                        tension: 0.1
                    }]
                },
                options: {
                    plugins: {
                        legend: { display: false },
                        tooltip: { enabled: true }
                    },
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            });
        }

        // Barras
        if (tiposGraficas.includes('barras')) {
            const ctx = document.getElementById('graficaBarras').getContext('2d');
            charts.barras = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: etiquetas,
                    datasets: [{
                        label: 'Tasa de Titulación',
                        data: valores,
                        backgroundColor: colores
                    }]
                },
                options: {
                    plugins: {
                        legend: { display: false },
                        tooltip: { enabled: true }
                    },
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            });
        }

        // Pastel
        if (tiposGraficas.includes('pastel')) {
            const ctx = document.getElementById('graficaPastel').getContext('2d');
            charts.pastel = new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: etiquetas,
                    datasets: [{
                        label: 'Tasa de Titulación',
                        data: valores,
                        backgroundColor: colores
                    }]
                },
                options: {
                    plugins: {
                        legend: { position: 'right' },
                        tooltip: { enabled: true }
                    }
                }
            });
        }

        // Gaussiana
        if (tiposGraficas.includes('gauss')) {
            const ctx = document.getElementById('graficaGauss').getContext('2d');
            const media = valores.reduce((a, b) => a + b, 0) / valores.length;
            const desviacion = Math.sqrt(valores.map(x => Math.pow(x - media, 2)).reduce((a, b) => a + b, 0) / valores.length);

            const xValues = [];
            const yValues = [];

            for (let x = media - 3 * desviacion; x <= media + 3 * desviacion; x += 0.5) {
                const y = (1 / (desviacion * Math.sqrt(2 * Math.PI))) *
                    Math.exp(-0.5 * Math.pow((x - media) / desviacion, 2));
                xValues.push(x.toFixed(2));
                yValues.push(y);
            }

            charts.gauss = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: xValues,
                    datasets: [{
                        label: 'Distribución Gaussiana',
                        data: yValues,
                        borderColor: colores[1],
                        fill: false,
                        tension: 0.2
                    }]
                },
                options: {
                    plugins: {
                        legend: { display: true },
                        tooltip: { enabled: true }
                    },
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            });
        }
    }

    // Escuchar cambios
    selectCarreras.addEventListener('change', actualizarGraficas);
    selectGraficas.addEventListener('change', actualizarGraficas);

    // Mostrar al cargar
    actualizarGraficas();
});

// Exportar PDF
function descargarPDF() {
    const contenedor = document.querySelector('.graficas-container');
    import('https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js').then(html2pdf => {
        html2pdf.default()
            .from(contenedor)
            .set({
                filename: 'titulados_historico_actual.pdf',
                image: { type: 'jpeg', quality: 0.98 },
                html2canvas: { scale: 2 },
                jsPDF: { unit: 'pt', format: 'a4', orientation: 'portrait' }
            })
            .save();
    });
}
