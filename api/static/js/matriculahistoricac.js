document.addEventListener('DOMContentLoaded', function () {
    const labels = JSON.parse(document.getElementById('labels-data').textContent);
    const totales = JSON.parse(document.getElementById('totales-data').textContent);
    const programas = JSON.parse(document.getElementById('programas-data').textContent);
    const filtroGraficas = document.getElementById('filtroGraficas');
    const selectCiclos = document.getElementById('filtro-ciclos');

    const choices = new Choices(selectCiclos, {
        removeItemButton: true,
        placeholderValue: 'Selecciona ciclos...',
        searchPlaceholderValue: 'Buscar...',
        noResultsText: 'Sin resultados',
    });
 
    const contenedores = {
        graficoMatriculaTotal: document.getElementById('graficoMatriculaTotalContainer'),
        graficoMatriculaCarrera: document.getElementById('graficoMatriculaCarreraContainer'),
        graficoPastelCarreras: document.getElementById('graficoPastelCarrerasContainer'),
        graficoGauss: document.getElementById('graficoGaussContainer')
    };

    const charts = {};

    function obtenerColores(n) {
        const colores = [];
        for (let i = 0; i < n; i++) {
            colores.push(`hsl(${(i * 360) / n}, 70%, 70%)`);
        }
        return colores;
    }

    function actualizarGraficas() {
        const ciclosSeleccionados = Array.from(selectCiclos.selectedOptions).map(opt => opt.value);

        const datosFiltrados = labels.reduce((acc, ciclo, index) => {
            if (ciclosSeleccionados.length === 0 || ciclosSeleccionados.includes(ciclo)) {
                acc.labels.push(ciclo);
                acc.totales.push(totales[ciclo] || 0);
                for (const [programa, valores] of Object.entries(programas)) {
                    if (!acc.programas[programa]) acc.programas[programa] = [];
                    acc.programas[programa].push(valores[index] || 0);
                }
            }
            return acc;
        }, { labels: [], totales: [], programas: {} });

        const colores = obtenerColores(Object.keys(datosFiltrados.programas).length);

        // 📈 Lineal
        if (charts.total) charts.total.destroy();
        charts.total = new Chart(document.getElementById('graficoMatriculaTotal'), {
            type: 'line',
            data: {
                labels: datosFiltrados.labels,
                datasets: [{
                    label: 'Matrícula Total',
                    data: datosFiltrados.totales,
                    borderColor: '#42a5f5',
                    backgroundColor: 'rgba(66, 165, 245, 0.2)',
                    fill: true
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    tooltip: { enabled: true },
                    legend: { display: false },
                    datalabels: {
                        anchor: 'end',
                        align: 'top',
                        formatter: Math.round,
                        font: { weight: 'bold' }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { precision: 0 }
                    }
                }
            },
            plugins: [ChartDataLabels]
        });

        // 📊 Barras
        if (charts.carrera) charts.carrera.destroy();
        charts.carrera = new Chart(document.getElementById('graficoMatriculaCarrera'), {
            type: 'bar',
            data: {
                labels: datosFiltrados.labels,
                datasets: Object.entries(datosFiltrados.programas).map(([nombre, datos], i) => ({
                    label: nombre,
                    data: datos,
                    backgroundColor: colores[i % colores.length]
                }))
            },
            options: {
                responsive: true,
                plugins: {
                    tooltip: { enabled: true },
                    datalabels: { display: false }
                }
            },
            plugins: [ChartDataLabels]
        });

        // 🍰 Pastel
        if (charts.pastel) charts.pastel.destroy();
        const sumas = Object.values(datosFiltrados.programas).map(datos =>
            datos.reduce((a, b) => a + b, 0)
        );
        charts.pastel = new Chart(document.getElementById('graficoPastelCarreras'), {
            type: 'pie',
            data: {
                labels: Object.keys(datosFiltrados.programas),
                datasets: [{
                    data: sumas,
                    backgroundColor: colores
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    tooltip: { enabled: true },
                    datalabels: {
                        formatter: Math.round,
                        color: '#000'
                    }
                }
            },
            plugins: [ChartDataLabels]
        });

        // 🧠 Gauss
        if (charts.gauss) charts.gauss.destroy();
        const promedio = datosFiltrados.totales.reduce((a, b) => a + b, 0) / (datosFiltrados.totales.length || 1);
        const desviacion = Math.sqrt(
            datosFiltrados.totales.reduce((suma, val) => suma + Math.pow(val - promedio, 2), 0) / (datosFiltrados.totales.length || 1)
        );
        const valoresGauss = datosFiltrados.totales.map(val =>
            (1 / (desviacion * Math.sqrt(2 * Math.PI))) *
            Math.exp(-0.5 * Math.pow((val - promedio) / desviacion, 2)) * 10000
        );
        charts.gauss = new Chart(document.getElementById('graficoGauss'), {
            type: 'line',
            data: {
                labels: datosFiltrados.labels,
                datasets: [{
                    label: 'Distribución Gaussiana',
                    data: valoresGauss,
                    borderColor: '#f06292',
                    backgroundColor: 'rgba(240, 98, 146, 0.2)',
                    fill: true
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    tooltip: { enabled: true },
                    datalabels: {
                        formatter: value => value.toFixed(2),
                        color: '#000'
                    }
                }
            },
            plugins: [ChartDataLabels]
        });
    }

    // Filtros de gráficas visibles
    filtroGraficas.addEventListener('change', function () {
        Object.keys(contenedores).forEach(id => {
            const checkbox = filtroGraficas.querySelector(`input[value="${id}"]`);
            contenedores[id].style.display = checkbox.checked ? 'block' : 'none';
        });
    });

    // Botón: Mostrar todas
    document.getElementById('btnMostrarTodas').addEventListener('click', function () {
        Array.from(filtroGraficas.querySelectorAll('input[type="checkbox"]')).forEach(chk => chk.checked = true);
        Object.keys(contenedores).forEach(id => contenedores[id].style.display = 'block');
        for (let i = 0; i < selectCiclos.options.length; i++) {
            selectCiclos.options[i].selected = true;
        }
        selectCiclos.dispatchEvent(new Event('change'));
    });

    // Filtro por ciclos
    selectCiclos.addEventListener('change', actualizarGraficas);

    // Botón: Descargar PDF
    document.getElementById('btnDescargarPDF').addEventListener('click', async () => {
        const { jsPDF } = window.jspdf;
        const pdf = new jsPDF('p', 'mm', 'a4');
        const graficas = [
            { id: 'graficoMatriculaTotalContainer', titulo: ' Matrícula Total (Gráfico Lineal)' },
            { id: 'graficoMatriculaCarreraContainer', titulo: ' Matrícula por Carrera (Barras)' },
            { id: 'graficoPastelCarrerasContainer', titulo: ' Distribución por Carrera (Pastel)' },
            { id: 'graficoGaussContainer', titulo: ' Distribución Gaussiana' }
        ];

        let y = 10;

        pdf.setFontSize(16);
        pdf.setTextColor(40, 40, 40);
        pdf.text(' Matrícula Histórica', 105, y, { align: 'center' });
        y += 10;

        for (const grafica of graficas) {
            const container = document.getElementById(grafica.id);
            if (container && container.style.display !== 'none') {
                const canvas = await html2canvas(container, { scale: 2 });
                const imgData = canvas.toDataURL('image/png');
                const imgProps = pdf.getImageProperties(imgData);
                const pdfWidth = 180;
                const pdfHeight = (imgProps.height * pdfWidth) / imgProps.width;

                y += 10;
                if (y + pdfHeight > 280) {
                    pdf.addPage();
                    y = 20;
                }

                pdf.setFontSize(12);
                pdf.setTextColor(80, 80, 80);
                pdf.text(grafica.titulo, 15, y);
                y += 3;
                pdf.addImage(imgData, 'PNG', 15, y, pdfWidth, pdfHeight);
                y += pdfHeight + 5;
            }
        }

        pdf.save('matricula_historica.pdf');
    });

    // Carga inicial
    actualizarGraficas();
});
