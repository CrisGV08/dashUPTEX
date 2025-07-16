document.addEventListener("DOMContentLoaded", function () {
  const elementos = {
    datos: document.getElementById("datosGraficas"),
    filtroCiclo: document.getElementById("filtroAnio"),
    btnAplicar: document.getElementById("aplicarFiltros"),
    btnReset: document.getElementById("resetFiltros"),
    btnPDF: document.getElementById("btnDescargarPDF"),
    checkboxes: document.querySelectorAll(".grafica-check")
  };

  if (elementos.filtroCiclo) {
    elementos.filtroCiclo.addEventListener('change', function () {
      this.form.submit();
    });
  }

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

    const baseOptions = {
      responsive: true,
      maintainAspectRatio: false,
      layout: {
        padding: 20
      },
      plugins: {
        legend: { position: 'top' },
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
            backgroundColor: "#4CAF50"
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
            borderColor: "#007bff",
            backgroundColor: "rgba(0, 123, 255, 0.2)",
            tension: 0.4,
            fill: true
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
            backgroundColor: labels.map(() =>
              `hsl(${Math.floor(Math.random() * 360)}, 60%, 60%)`
            )
          }]
        },
        options: {
          responsive: true,
          plugins: {
            legend: { position: 'right' },
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
        return data.map(x => Math.exp(-Math.pow(x - mean, 2) / (2 * Math.pow(std, 2))));
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
            fill: true
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

  elementos.btnAplicar?.addEventListener("click", aplicarFiltros);

  elementos.btnReset?.addEventListener("click", () => {
    elementos.checkboxes.forEach(cb => cb.checked = true);
    aplicarFiltros();
  });

  elementos.btnPDF?.addEventListener("click", async () => {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();
    doc.setFontSize(16);
    doc.text("Reporte de Aprovechamiento Académico", 105, 15, { align: "center" });

    const graficas = ["box-barras", "box-linea", "box-pastel", "box-gauss"];
    let y = 30;

    for (const id of graficas) {
      const box = document.getElementById(id);
      if (box && box.style.display !== "none") {
        const canvas = box.querySelector("canvas");
        if (canvas) {
          const imgData = await html2canvas(canvas, { scale: 2 }).then(c => c.toDataURL("image/png"));
          const width = 180;
          const height = canvas.offsetHeight * (width / canvas.offsetWidth);

          if (y + height > doc.internal.pageSize.getHeight() - 20) {
            doc.addPage();
            y = 20;
          }

          doc.addImage(imgData, "PNG", 15, y, width, height);
          y += height + 10;
        }
      }
    }

    doc.save("reporte_aprovechamiento.pdf");
  });

  aplicarFiltros();
});
