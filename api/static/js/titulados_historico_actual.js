
document.addEventListener('DOMContentLoaded', function () {
    if (!datosGeneraciones || datosGeneraciones.length === 0) return;

    const selectCarreras = document.getElementById('selectCarreras');
    const charts = {};

    const choices = new Choices(selectCarreras, {
        removeItemButton: true,
        placeholder: true,
        placeholderValue: 'Selecciona una o más carreras',
        searchEnabled: true
    });

    function actualizarGraficasPorCarrera(carrerasSeleccionadas) {
        const filtrados = datosGeneraciones.filter(gen => {
            const etiqueta = `${gen.nombre_programa} (${gen.anio})`;
            return carrerasSeleccionadas.length === 0 || carrerasSeleccionadas.includes(etiqueta);
        });

        const etiquetas = filtrados.map(gen => `${gen.nombre_programa} (${gen.anio})`);
        const tasas = filtrados.map(gen => gen.tasa_titulacion);

        if (charts.lineal) {
            charts.lineal.data.labels = etiquetas;
            charts.lineal.data.datasets[0].data = tasas;
            charts.lineal.update();
        }
        if (charts.barras) {
            charts.barras.data.labels = etiquetas;
            charts.barras.data.datasets[0].data = tasas;
            charts.barras.update();
        }
        if (charts.pastel) {
            const acumulado = {};
            filtrados.forEach(g => {
                acumulado[g.nombre_programa] = (acumulado[g.nombre_programa] || 0) + g.tasa_titulacion;
            });
            charts.pastel.data.labels = Object.keys(acumulado);
            charts.pastel.data.datasets[0].data = Object.values(acumulado);
            charts.pastel.update();
        }
        if (charts.gauss) {
            const media = tasas.reduce((a, b) => a + b, 0) / (tasas.length || 1);
            const desv = Math.sqrt(tasas.reduce((acc, v) => acc + Math.pow(v - media, 2), 0) / (tasas.length || 1));
            const valoresX = Array.from({ length: 100 }, (_, i) => media - 3 * desv + i * (6 * desv / 100));
            const valoresY = valoresX.map(x =>
                (1 / (desv * Math.sqrt(2 * Math.PI))) * Math.exp(-0.5 * Math.pow((x - media) / desv, 2))
            );
            charts.gauss.data.labels = valoresX.map(x => x.toFixed(1));
            charts.gauss.data.datasets[0].data = valoresY;
            charts.gauss.update();
        }
    }

    // Mostrar/ocultar gráficas
    document.querySelectorAll('.filtro-grafica').forEach(checkbox => {
        checkbox.addEventListener('change', () => {
            const canvas = document.getElementById(checkbox.value);
            if (canvas) {
                if (checkbox.checked) {
                    canvas.style.display = 'block';
                } else {
                    canvas.style.display = 'none';
                }
            }
        });
    });

    // Crear gráficas al cargar
    const etiquetasIniciales = datosGeneraciones.map(gen => `${gen.nombre_programa} (${gen.anio})`);
    const tasasIniciales = datosGeneraciones.map(gen => gen.tasa_titulacion);

    charts.lineal = new Chart(document.getElementById('graficaLineal'), {
        type: 'line',
        data: {
            labels: etiquetasIniciales,
            datasets: [{
                label: 'Tasa de Titulación (%)',
                data: tasasIniciales,
                borderColor: 'rgba(75, 192, 192, 1)',
                backgroundColor: 'rgba(75, 192, 192, 0.4)',
                fill: true,
                tension: 0.4,
                pointRadius: 5,
                pointHoverRadius: 7
            }]
        },
        options: {
            plugins: {
                legend: { display: false },
                title: { display: true, text: 'Tasa de Titulación - Línea' }
            },
            scales: {
                y: { beginAtZero: true, title: { display: true, text: '%' } }
            }
        }
    });

    charts.barras = new Chart(document.getElementById('graficaBarras'), {
        type: 'bar',
        data: {
            labels: etiquetasIniciales,
            datasets: [{
                label: 'Tasa de Titulación (%)',
                data: tasasIniciales,
                backgroundColor: 'rgba(153, 102, 255, 0.6)',
                borderColor: 'rgba(153, 102, 255, 1)',
                borderWidth: 1
            }]
        },
        options: {
            plugins: {
                title: { display: true, text: 'Tasa de Titulación - Barras' }
            },
            scales: { y: { beginAtZero: true } }
        }
    });

    const acumuladoInicial = {};
    datosGeneraciones.forEach(gen => {
        acumuladoInicial[gen.nombre_programa] = (acumuladoInicial[gen.nombre_programa] || 0) + gen.tasa_titulacion;
    });

    charts.pastel = new Chart(document.getElementById('graficaPastel'), {
        type: 'pie',
        data: {
            labels: Object.keys(acumuladoInicial),
            datasets: [{
                data: Object.values(acumuladoInicial),
                backgroundColor: Object.keys(acumuladoInicial).map(() => `hsl(${Math.random() * 360}, 70%, 65%)`)
            }]
        },
        options: {
            plugins: { title: { display: true, text: 'Distribución Tasa de Titulación - Pastel' } }
        }
    });

    const mediaInicial = tasasIniciales.reduce((a, b) => a + b, 0) / tasasIniciales.length;
    const desvInicial = Math.sqrt(tasasIniciales.reduce((acc, val) => acc + Math.pow(val - mediaInicial, 2), 0) / tasasIniciales.length);
    const valoresXInicial = Array.from({ length: 100 }, (_, i) => mediaInicial - 3 * desvInicial + i * (6 * desvInicial / 100));
    const valoresYInicial = valoresXInicial.map(x =>
        (1 / (desvInicial * Math.sqrt(2 * Math.PI))) * Math.exp(-0.5 * Math.pow((x - mediaInicial) / desvInicial, 2))
    );

    charts.gauss = new Chart(document.getElementById('graficaGauss'), {
        type: 'line',
        data: {
            labels: valoresXInicial.map(x => x.toFixed(1)),
            datasets: [{
                label: 'Distribución Gaussiana',
                data: valoresYInicial,
                borderColor: 'rgba(255, 99, 132, 1)',
                backgroundColor: 'rgba(255, 99, 132, 0.4)',
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            plugins: { title: { display: true, text: 'Distribución Gaussiana (Simulada)' } },
            scales: {
                y: { beginAtZero: true },
                x: { title: { display: true, text: 'Tasa (%)' } }
            }
        }
    });

    selectCarreras.addEventListener('change', () => {
        const seleccionadas = Array.from(selectCarreras.selectedOptions).map(opt => opt.value);
        actualizarGraficasPorCarrera(seleccionadas);
    });
});

