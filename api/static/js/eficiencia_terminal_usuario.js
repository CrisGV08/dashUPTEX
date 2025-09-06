// static/js/eficiencia_terminal_usuario.js
document.addEventListener("DOMContentLoaded", function () {
  const elementos = {
    datos: document.getElementById("datosGraficas"),
    filtroCiclo: document.getElementById("filtroAnio"),
    btnAplicar: document.getElementById("aplicarFiltros"),
    btnReset: document.getElementById("resetFiltros"),
    checkboxes: document.querySelectorAll(".grafica-check"),
  };

  // Auto-submit al cambiar el ciclo
  if (elementos.filtroCiclo && elementos.filtroCiclo.form) {
    elementos.filtroCiclo.addEventListener("change", function () {
      this.form.submit();
    });
  }

  // Leer JSON de datos
  let datos = { eficiencia: 0 };
  try {
    datos = JSON.parse(elementos.datos?.textContent || '{"eficiencia":0}');
  } catch (e) {
    console.error("JSON inválido en #datosGraficas", e);
  }

  const charts = {};
  const color = "#28a745";

  function renderGraficas(tipos) {
    // Destruir previas
    Object.values(charts).forEach(c => c && c.destroy());

    const labels = ["Eficiencia Terminal %"];
    const valores = [Number.isFinite(+datos.eficiencia) ? +datos.eficiencia : 0];

    const configComun = {
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
    if (tipos.includes("barras")) {
      charts.barras = new Chart(document.getElementById("graficaBarras"), {
        type: "bar",
        data: {
          labels,
          datasets: [{ label: "Porcentaje", data: valores, backgroundColor: [color], borderColor: [color], borderWidth: 1 }]
        },
        options: configComun,
        plugins: [ChartDataLabels]
      });
    }

    // Línea
    if (tipos.includes("linea")) {
      charts.linea = new Chart(document.getElementById("graficaLinea"), {
        type: "line",
        data: {
          labels,
          datasets: [{ label: "Porcentaje", data: valores, borderColor: color, backgroundColor: "rgba(40,167,69,0.2)", fill: true, tension: 0.4 }]
        },
        options: configComun,
        plugins: [ChartDataLabels]
      });
    }

    // Pastel
    if (tipos.includes("pastel")) {
      charts.pastel = new Chart(document.getElementById("graficaPastel"), {
        type: "pie",
        data: {
          labels,
          datasets: [{ data: valores, backgroundColor: [color], borderColor: "#fff", borderWidth: 2 }]
        },
        options: configComun,
        plugins: [ChartDataLabels]
      });
    }

    // Gauss -> no tiene sentido con 1 valor: ocultamos
    const boxGauss = document.getElementById("box-gauss");
    if (boxGauss) boxGauss.style.display = "none";
  }

  function getGraficasSeleccionadas() {
    return Array.from(elementos.checkboxes).filter(cb => cb.checked).map(cb => cb.value);
  }

  function aplicarFiltros() {
    const seleccionadas = getGraficasSeleccionadas();

    document.querySelectorAll(".grafica-box").forEach(div => {
      const tipo = div.id.replace("box-", "");
      div.style.display = seleccionadas.includes(tipo) ? "block" : "none";
    });

    renderGraficas(seleccionadas);
  }

  if (elementos.btnAplicar) elementos.btnAplicar.addEventListener("click", aplicarFiltros);
  if (elementos.btnReset) {
    elementos.btnReset.addEventListener("click", () => {
      elementos.checkboxes.forEach(cb => cb.checked = true);
      aplicarFiltros();
    });
  }

  // Render inicial
  aplicarFiltros();
});
