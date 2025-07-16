document.addEventListener("DOMContentLoaded", function () {
    // ======================
    // 1. CONFIGURACIÓN INICIAL
    // ======================
    console.log("Iniciando carga de indicadores...");

    // Elementos del DOM
    const elementos = {
        datos: document.getElementById("datosGraficas"),
        filtroCiclo: document.getElementById("filtroAnio"), // Usando el ID correcto de tu HTML
        btnAplicar: document.getElementById("aplicarFiltros"),
        btnReset: document.getElementById("resetFiltros"),
        btnPDF: document.getElementById("btnDescargarPDF"),
        checkboxes: document.querySelectorAll(".grafica-check")
    };

    // Verificación de elementos
    for (const [nombre, elemento] of Object.entries(elementos)) {
        if (!elemento) console.error(`Elemento no encontrado: ${nombre}`);
    }

    // ======================
    // 2. MANEJO DEL FILTRO DE CICLO
    // ======================
    if (elementos.filtroCiclo) {
        elementos.filtroCiclo.addEventListener('change', function() {
            console.log("Ciclo cambiado a:", this.value);
            this.form.submit(); // Envía el formulario automáticamente
        });
    }

    // ======================
    // 3. CARGAR DATOS
    // ======================
    let datos;
    try {
        datos = JSON.parse(elementos.datos.textContent);
        console.log("Datos cargados:", datos);
    } catch (error) {
        console.error("Error al parsear datos:", error);
        return;
    }

    // ======================
    // 4. CONFIGURACIÓN DE GRÁFICAS
    // ======================
    const charts = {};
    const colores = {
        desercion: '#FF6384', // Rojo
        reprobacion: '#36A2EB' // Azul
    };

    // Función para renderizar gráficas
    function renderGraficas(tiposGraficas) {
        console.log("Renderizando gráficas:", tiposGraficas);

        // Destruir gráficas anteriores
        Object.values(charts).forEach(chart => chart && chart.destroy());

        // Datos comunes
        const labels = ['Deserción', 'Reprobación'];
        const valores = [
            parseFloat(datos.desercion) || 0,
            parseFloat(datos.reprobacion) || 0
        ];

        // Configuración común
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

        // Gráfico de Barras
        if (tiposGraficas.includes("barras")) {
            charts.barras = new Chart(document.getElementById("graficaBarras"), {
                type: 'bar',
                data: {
                    labels,
                    datasets: [{
                        label: 'Porcentaje',
                        data: valores,
                        backgroundColor: [colores.desercion, colores.reprobacion],
                        borderColor: [colores.desercion, colores.reprobacion],
                        borderWidth: 1
                    }]
                },
                options: configComun,
                plugins: [ChartDataLabels]
            });
        }

        // Gráfico de Línea
        if (tiposGraficas.includes("linea")) {
            charts.linea = new Chart(document.getElementById("graficaLinea"), {
                type: 'line',
                data: {
                    labels,
                    datasets: [{
                        label: 'Porcentaje',
                        data: valores,
                        borderColor: '#4BC0C0',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: configComun,
                plugins: [ChartDataLabels]
            });
        }

        // Gráfico de Pastel
        if (tiposGraficas.includes("pastel")) {
            charts.pastel = new Chart(document.getElementById("graficaPastel"), {
                type: 'pie',
                data: {
                    labels,
                    datasets: [{
                        data: valores,
                        backgroundColor: [colores.desercion, colores.reprobacion],
                        borderColor: '#fff',
                        borderWidth: 2
                    }]
                },
                options: configComun,
                plugins: [ChartDataLabels]
            });
        }

        // Gráfico de Gauss (Distribución Normal)
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

    // ======================
    // 5. MANEJO DE FILTROS
    // ======================
    function getGraficasSeleccionadas() {
        return Array.from(elementos.checkboxes)
            .filter(cb => cb.checked)
            .map(cb => cb.value);
    }

    function aplicarFiltros() {
        const seleccionadas = getGraficasSeleccionadas();
        console.log("Filtros aplicados:", seleccionadas);

        // Mostrar/ocultar gráficas
        document.querySelectorAll(".grafica-box").forEach(div => {
            const tipo = div.id.replace("box-", "");
            div.style.display = seleccionadas.includes(tipo) ? "block" : "none";
        });

        renderGraficas(seleccionadas);
    }

    // Event Listeners
    elementos.btnAplicar.addEventListener('click', aplicarFiltros);
    elementos.btnReset.addEventListener('click', function() {
        elementos.checkboxes.forEach(cb => cb.checked = true);
        aplicarFiltros();
    });

    // ======================
    // 6. EXPORTAR PDF
    // ======================
    elementos.btnPDF.addEventListener('click', async function() {
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF();
        
        // Título
        doc.setFontSize(16);
        doc.text("Reporte de Indicadores Académicos", 105, 15, { align: "center" });
        
        // Gráficas
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
        
        doc.save('reporte_indicadores.pdf');
    });

    // ======================
    // 7. INICIALIZACIÓN
    // ======================
    aplicarFiltros(); // Render inicial con todos los gráficos
    console.log("Aplicación inicializada correctamente");
});