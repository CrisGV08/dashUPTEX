document.addEventListener("DOMContentLoaded", function () {
  // ======================
  // 1. CONFIGURACIÓN INICIAL
  // ======================
  const elementos = {
    datos: document.getElementById("datosGraficas"),
    filtroCiclo: document.getElementById("filtroAnio"),
    btnAplicar: document.getElementById("aplicarFiltros"),
    btnReset: document.getElementById("resetFiltros"),
    btnPDF: document.getElementById("btnDescargarPDF"),   // 👈 puede NO existir en usuario
    checkboxes: document.querySelectorAll(".grafica-check")
  };

  // 2) Cargar datos JSON robusto
  let datos = { desercion: 0, reprobacion: 0 };
  try {
    if (!elementos.datos) throw new Error("No se encontró #datosGraficas");
    const raw = elementos.datos.textContent || "{}";
    datos = JSON.parse(raw);
  } catch (e) {
    console.error("Error al parsear datos:", e);
  }

  // ======================
  // 3. MANEJO DEL FILTRO DE CICLO (auto submit)
  // ======================
  if (elementos.filtroCiclo && elementos.filtroCiclo.form) {
    elementos.filtroCiclo.addEventListener("change", function () {
      this.form.submit();
    });
  }

  // ======================
  // 4. CONFIGURACIÓN DE GRÁFICAS
  // ======================
  const charts = {};
  const colores = {
    desercion: "#FF6384",
    reprobacion: "#36A2EB"
  };
  const pluginsDatalabels = (window.ChartDataLabels ? [ChartDataLabels] : []);

  function renderGraficas(tiposGraficas) {
    // destruir previas
    Object.values(charts).forEach(ch => ch && ch.destroy());

    const labels = ["Deserción", "Reprobación"];
    const valores = [
      Number.parseFloat(datos.desercion) || 0,
      Number.parseFloat(datos.reprobacion) || 0
    ];

    // mostrar/ocultar contenedores
    document.querySelectorAll(".grafica-box").forEach(div => {
      const tipo = div.id.replace("box-", "");
      div.style.display = tiposGraficas.includes(tipo) ? "block" : "none";
    });

    const opcionesBase = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "top" },
        datalabels: {
          anchor: "end",
          align: "top",
          formatter: v => `${v}%`,
          font: { weight: "bold" }
        }
      }
    };

    // Barras
    if (tiposGraficas.includes("barras")) {
      charts.barras = new Chart(document.getElementById("graficaBarras"), {
        type: "bar",
        data: {
          labels,
          datasets: [{
            label: "Porcentaje",
            data: valores,
            backgroundColor: [colores.desercion, colores.reprobacion],
            borderColor: [colores.desercion, colores.reprobacion],
            borderWidth: 1
          }]
        },
        options: opcionesBase,
        plugins: pluginsDatalabels
      });
    }

    // Línea
    if (tiposGraficas.includes("linea")) {
      charts.linea = new Chart(document.getElementById("graficaLinea"), {
        type: "line",
        data: {
          labels,
          datasets: [{
            label: "Porcentaje",
            data: valores,
            borderColor: "#4BC0C0",
            backgroundColor: "rgba(75, 192, 192, 0.2)",
            fill: true,
            tension: 0.4
          }]
        },
        options: opcionesBase,
        plugins: pluginsDatalabels
      });
    }

    // Pastel
    if (tiposGraficas.includes("pastel")) {
      charts.pastel = new Chart(document.getElementById("graficaPastel"), {
        type: "pie",
        data: {
          labels,
          datasets: [{
            data: valores,
            backgroundColor: [colores.desercion, colores.reprobacion],
            borderColor: "#fff",
            borderWidth: 2
          }]
        },
        options: opcionesBase,
        plugins: pluginsDatalabels
      });
    }

    // Gauss
    if (tiposGraficas.includes("gauss")) {
      const gauss = (data) => {
        const m = data.reduce((a, b) => a + b, 0) / data.length;
        const sd = Math.sqrt(data.reduce((a, b) => a + Math.pow(b - m, 2), 0) / data.length) || 1;
        return data.map(x => Math.exp(-Math.pow(x - m, 2) / (2 * Math.pow(sd, 2))));
      };
      charts.gauss = new Chart(document.getElementById("graficaGauss"), {
        type: "line",
        data: {
          labels,
          datasets: [{
            label: "Distribución Gaussiana",
            data: gauss(valores),
            borderColor: "#9966FF",
            backgroundColor: "rgba(153, 102, 255, 0.2)",
            fill: true,
            tension: 0.4
          }]
        },
        options: { responsive: true, maintainAspectRatio: false }
      });
    }
  }

  // ======================
  // 5. MANEJO DE FILTROS (UI)
  // ======================
  const getGraficasSeleccionadas = () =>
    Array.from(elementos.checkboxes || []).filter(cb => cb.checked).map(cb => cb.value);

  function aplicarFiltros() {
    renderGraficas(getGraficasSeleccionadas());
  }

  if (elementos.btnAplicar) {
    elementos.btnAplicar.addEventListener("click", aplicarFiltros);
  }
  if (elementos.btnReset) {
    elementos.btnReset.addEventListener("click", () => {
      (elementos.checkboxes || []).forEach(cb => cb.checked = true);
      aplicarFiltros();
    });
  }

  // ======================
  // 6. EXPORTAR PDF (solo si existe el botón)
  // ======================
  if (elementos.btnPDF) {
    elementos.btnPDF.addEventListener("click", async function () {
      const { jsPDF } = window.jspdf;
      const doc = new jsPDF();
      doc.setFontSize(16);
      doc.text("Reporte de Indicadores Académicos", 105, 15, { align: "center" });

      const graficas = ["box-barras", "box-linea", "box-pastel", "box-gauss"];
      let y = 30;
      for (const id of graficas) {
        const container = document.getElementById(id);
        if (!container || container.style.display === "none") continue;
        const canvas = container.querySelector("canvas");
        if (!canvas) continue;
        const c = await html2canvas(canvas, { scale: 2 });
        const imgData = c.toDataURL("image/png");
        const width = 180;
        const height = c.height * width / c.width;
        if (y + height > doc.internal.pageSize.getHeight() - 20) {
          doc.addPage();
          y = 20;
        }
        doc.addImage(imgData, "PNG", 15, y, width, height);
        y += height + 10;
      }
      doc.save("reporte_indicadores.pdf");
    });
  }

  // ======================
  // 7. INICIALIZACIÓN
  // ======================
  aplicarFiltros(); // Render inicial
});
