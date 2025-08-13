document.addEventListener("DOMContentLoaded", function () {
  const elementos = {
    datos: document.getElementById("datosGraficas"),
    filtroCiclo: document.getElementById("filtroAnio"),
    btnAplicar: document.getElementById("aplicarFiltros"),
    btnReset: document.getElementById("resetFiltros"),
    btnPDF: document.getElementById("btnDescargarPDF"),
    checkboxes: document.querySelectorAll(".grafica-check"),
    selectAllProg: document.getElementById("select-all-prog"),
    clearAllProg: document.getElementById("clear-all-prog"),
    programaCheckboxes: document.querySelectorAll('input[name="programas[]"]'),
    formFiltros: document.getElementById("filter-form")
  };

  // Manejo de eventos para filtros
  if (elementos.filtroCiclo) {
    elementos.filtroCiclo.addEventListener('change', function() {
      elementos.formFiltros.submit();
    });
  }

  // Selección múltiple de programas
  if (elementos.selectAllProg) {
    elementos.selectAllProg.addEventListener('click', function() {
      elementos.programaCheckboxes.forEach(el => el.checked = true);
      elementos.formFiltros.submit();
    });
  }

  if (elementos.clearAllProg) {
    elementos.clearAllProg.addEventListener('click', function() {
      elementos.programaCheckboxes.forEach(el => el.checked = false);
      elementos.formFiltros.submit();
    });
  }

  // Reset de filtros
  if (elementos.btnReset) {
    elementos.btnReset.addEventListener('click', function() {
      // Resetear checkboxes de gráficas
      elementos.checkboxes.forEach(cb => cb.checked = true);
      
      // Resetear select de ciclo
      if (elementos.filtroCiclo) {
        elementos.filtroCiclo.value = "Todos";
      }
      
      // Resetear checkboxes de programas
      elementos.programaCheckboxes.forEach(el => el.checked = false);
      
      // Enviar formulario
      elementos.formFiltros.submit();
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('filter-form');
  const anioHidden = document.getElementById('filtroAnioHidden');
  const anioRadios = document.querySelectorAll('input[name="anioChip"]');

  // 1) Al cambiar de chip, copiar al hidden (lo que lee el backend)
  anioRadios.forEach(r => {
    r.addEventListener('change', () => {
      anioHidden.value = r.value;
      // Si quieres que filtre automáticamente al cambiar, descomenta:
      // form?.submit();
    });
  });

  // 2) Botón Reset: pone "Todos" en ciclo y limpia checks (opcional)
  const resetBtn = document.getElementById('resetFiltros');
  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      // Ciclo → Todos
      const chipTodos = document.getElementById('anio-Todos');
      if (chipTodos) chipTodos.checked = true;
      anioHidden.value = 'Todos';

      // Opcional: desmarcar programas y tipos de gráfica
      document.querySelectorAll('.programa-checkbox').forEach(c => c.checked = false);
      document.querySelectorAll('.grafica-check').forEach(c => c.checked = false);

      // Envía con reset aplicado (si prefieres que solo limpie sin enviar, comenta la línea siguiente)
      form?.submit();
    });
  }

  // 3) Botón Aplicar: asegura que el hidden lleve lo que está seleccionado
  const aplicarBtn = document.getElementById('aplicarFiltros');
  if (aplicarBtn) {
    aplicarBtn.addEventListener('click', () => {
      const sel = document.querySelector('input[name="anioChip"]:checked');
      if (sel) anioHidden.value = sel.value;
      // el submit lo hace el propio botón type="submit"
    });
  }
});



  // Cargar datos iniciales
  let datos;
  try {
    datos = JSON.parse(elementos.datos.textContent);
  } catch (error) {
    console.error("Error al parsear JSON:", error);
    return;
  }

  const charts = {};

  function renderGraficas(tipos) {
    Object.values(charts).forEach(chart => chart?.destroy());

    const labels = datos.programas || [];
    const valores = datos.promedios || [];
    const tiposPrograma = datos.tipos || [];

    const colores = tiposPrograma.map(tipo => 
      tipo === 'antiguo' ? 'rgba(75, 192, 192, 0.7)' : 'rgba(153, 102, 255, 0.7)'
    );

    const baseOptions = {
      responsive: true,
      maintainAspectRatio: false,
      layout: { padding: 20 },
      plugins: {
        legend: { 
          position: 'top',
          labels: {
            generateLabels: function(chart) {
              const original = Chart.overrides.pie.plugins.legend.labels.generateLabels(chart);
              return original.map(label => {
                if (label.text.includes('(Antiguo)')) {
                  label.fillStyle = 'rgba(75, 192, 192, 0.7)';
                } else if (label.text.includes('(Nuevo)')) {
                  label.fillStyle = 'rgba(153, 102, 255, 0.7)';
                }
                return label;
              });
            }
          }
        },
        datalabels: {
          anchor: 'end',
          align: 'top',
          formatter: value => value.toFixed(2),
          font: { weight: 'bold' }
        }
      },
      scales: {
        x: {
          ticks: {
            callback: function (value, index, ticks) {
              const texto = this.getLabelForValue(value);
              return texto.length > 20 ? texto.substring(0, 20) + '…' : texto;
            },
            maxRotation: 45,
            minRotation: 30,
            autoSkip: false
          }
        }
      }
    };

    if (tipos.includes("barras")) {
      charts.barras = new Chart(document.getElementById("graficaBarras"), {
        type: "bar",
        data: {
          labels,
          datasets: [{
            label: "Promedio",
            data: valores,
            backgroundColor: colores,
            borderColor: colores.map(c => c.replace('0.7', '1')),
            borderWidth: 1
          }]
        },
        options: baseOptions,
        plugins: [ChartDataLabels]
      });
    }

    if (tipos.includes("linea")) {
      charts.linea = new Chart(document.getElementById("graficaLinea"), {
        type: "line",
        data: {
          labels,
          datasets: [{
            label: "Promedio",
            data: valores,
            borderColor: colores,
            backgroundColor: colores.map(c => c.replace('0.7', '0.2')),
            tension: 0.4,
            fill: true,
            borderWidth: 2
          }]
        },
        options: baseOptions,
        plugins: [ChartDataLabels]
      });
    }

    if (tipos.includes("pastel")) {
      charts.pastel = new Chart(document.getElementById("graficaPastel"), {
        type: "pie",
        data: {
          labels,
          datasets: [{
            data: valores,
            backgroundColor: colores,
            borderColor: '#fff',
            borderWidth: 1
          }]
        },
        options: {
          responsive: true,
          plugins: {
            legend: { 
              position: 'right',
              labels: {
                usePointStyle: true,
                padding: 20
              }
            },
            datalabels: {
              formatter: value => value.toFixed(2),
              font: { weight: 'bold' }
            }
          }
        },
        plugins: [ChartDataLabels]
      });
    }

    if (tipos.includes("gauss")) {
      const calcularGauss = (data) => {
        const mean = data.reduce((a, b) => a + b, 0) / data.length;
        const std = Math.sqrt(data.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / data.length);
        return data.map(x => Math.exp(-Math.pow(x - mean, 2) / (2 * Math.pow(std, 2)));
      };

      charts.gauss = new Chart(document.getElementById("graficaGauss"), {
        type: "line",
        data: {
          labels,
          datasets: [{
            label: "Distribución Gaussiana",
            data: calcularGauss(valores),
            borderColor: "#FF9800",
            backgroundColor: "rgba(255, 152, 0, 0.2)",
            tension: 0.4,
            fill: true,
            borderWidth: 2
          }]
        },
        options: baseOptions
      });
    }
  }

  function aplicarFiltros() {
    const seleccionadas = Array.from(elementos.checkboxes)
      .filter(cb => cb.checked)
      .map(cb => cb.value);

    document.querySelectorAll(".grafica-box").forEach(div => {
      const tipo = div.id.replace("box-", "");
      div.style.display = seleccionadas.includes(tipo) ? "block" : "none";
    });

    renderGraficas(seleccionadas);
  }

  // Aplicar filtros al cargar la página
  aplicarFiltros();

  // Generar PDF
  if (elementos.btnPDF) {
    elementos.btnPDF.addEventListener("click", async () => {
      const { jsPDF } = window.jspdf;
      const doc = new jsPDF();
      doc.setFontSize(16);
      doc.text("Reporte de Aprovechamiento Académico", 105, 15, { align: "center" });

      // Fecha de generación
      const fecha = new Date().toLocaleDateString();
      doc.setFontSize(10);
      doc.text(`Generado el: ${fecha}`, 105, 22, { align: "center" });

      // Filtros aplicados
      let filtrosText = "Filtros aplicados: ";
      if (elementos.filtroCiclo && elementos.filtroCiclo.value !== "Todos") {
        filtrosText += `Ciclo: ${elementos.filtroCiclo.value} `;
      }
      
      const programasSeleccionados = Array.from(elementos.programaCheckboxes)
        .filter(cb => cb.checked)
        .map(cb => cb.nextElementSibling.textContent.trim());
      
      if (programasSeleccionados.length > 0) {
        filtrosText += `Programas: ${programasSeleccionados.join(', ')}`;
      } else {
        filtrosText += "Todos los programas";
      }
      
      doc.setFontSize(10);
      doc.text(filtrosText, 105, 28, { align: "center", maxWidth: 180 });

      const graficas = ["box-barras", "box-linea", "box-pastel", "box-gauss"];
      let y = 40;

      for (const id of graficas) {
        const box = document.getElementById(id);
        if (box && box.style.display !== "none") {
          const canvas = box.querySelector("canvas");
          if (canvas) {
            const imgData = await html2canvas(canvas, { 
              scale: 2,
              logging: false,
              useCORS: true
            }).then(c => c.toDataURL("image/png"));
            
            const width = 180;
            const height = canvas.offsetHeight * (width / canvas.offsetWidth);

            if (y + height > doc.internal.pageSize.getHeight() - 20) {
              doc.addPage();
              y = 20;
            }

            doc.addImage(imgData, "PNG", 15, y, width, height);
            y += height + 15;
          }
        }
      }

      doc.save(`reporte_aprovechamiento_${new Date().toISOString().slice(0,10)}.pdf`);
    });
  }
});