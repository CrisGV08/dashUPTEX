document.addEventListener("DOMContentLoaded", function () {
  if (!datosEvaluacion || datosEvaluacion.length === 0) return;

  const selectCiclos = document.getElementById("select-ciclos");
  const charts = {};

  // Inicializa Choices.js
  const choices = new Choices(selectCiclos, {
    removeItemButton: true,
    placeholder: true,
    placeholderValue: "Selecciona uno o más ciclos",
    searchEnabled: false,
  });

  // Cargar ciclos disponibles
  const ciclosUnicos = [...new Set(datosEvaluacion.map(d => d.ciclo))];
  ciclosUnicos.sort().forEach(ciclo => {
    const option = document.createElement("option");
    option.value = ciclo;
    option.textContent = ciclo;
    selectCiclos.appendChild(option);
  });
  choices.setChoices([...selectCiclos.options], "value", "label", true);
  choices.setChoiceByValue(ciclosUnicos); // Selecciona todos por defecto

  const filtrosGraficas = {
    linea: document.getElementById("linea"),
    barras: document.getElementById("barras"),
    pastel: document.getElementById("pastel"),
    gauss: document.getElementById("gauss"),
  };

  Object.values(filtrosGraficas).forEach(checkbox => {
    checkbox.addEventListener("change", actualizarVisibilidadGraficas);
  });

  selectCiclos.addEventListener("change", () => {
    renderGraficas();
  });

  function actualizarVisibilidadGraficas() {
    Object.entries(filtrosGraficas).forEach(([tipo, checkbox]) => {
      const canvasCiclo = document.getElementById(`grafica-${tipo}`);
      const canvasTotal = document.getElementById(`grafica-${tipo}-total`);
      if (canvasCiclo) canvasCiclo.parentElement.style.display = checkbox.checked ? "block" : "none";
      if (canvasTotal) canvasTotal.parentElement.style.display = checkbox.checked ? "block" : "none";
    });
  }

  function renderGraficas() {
    const seleccionados = Array.from(selectCiclos.selectedOptions).map(o => o.value);
    const datosFiltrados = datosEvaluacion.filter(d => seleccionados.includes(d.ciclo));

    const etiquetas = datosFiltrados.map(d => d.ciclo);
    const datos = datosFiltrados.map(d => d.promedio);

    const promedioGeneral = datos.reduce((a, b) => a + b, 0) / (datos.length || 1);
    const colores = etiquetas.map(() => generarColor());

    // Configuraciones base
    const configLineal = {
      type: "line",
      data: {
        labels: etiquetas,
        datasets: [{
          label: "Promedio",
          data: datos,
          tension: 0.3,
        }]
      },
      options: opcionesBase()
    };

    const configBarras = {
      type: "bar",
      data: {
        labels: etiquetas,
        datasets: [{
          label: "Promedio",
          data: datos,
          backgroundColor: colores,
        }]
      },
      options: opcionesBase()
    };

    const configPastel = {
      type: "pie",
      data: {
        labels: etiquetas,
        datasets: [{
          data: datos,
          backgroundColor: colores,
        }]
      },
      options: opcionesBase()
    };

    const configGauss = {
      type: "line",
      data: {
        labels: generarEtiquetasGauss(promedioGeneral),
        datasets: [{
          label: "Campana de Gauss",
          data: generarDatosGauss(promedioGeneral),
          borderDash: [5, 5],
          fill: false,
          pointRadius: 0,
        }]
      },
      options: opcionesBase()
    };

    const configLinealTotal = {
      type: "line",
      data: {
        labels: ["Promedio General"],
        datasets: [{
          label: "Promedio Total",
          data: [promedioGeneral],
        }]
      },
      options: opcionesBase()
    };

    const configBarrasTotal = {
      type: "bar",
      data: {
        labels: ["Promedio General"],
        datasets: [{
          label: "Promedio Total",
          data: [promedioGeneral],
          backgroundColor: generarColor(),
        }]
      },
      options: opcionesBase()
    };

    const configPastelTotal = {
      type: "pie",
      data: {
        labels: ["Promedio General"],
        datasets: [{
          data: [promedioGeneral],
          backgroundColor: [generarColor()],
        }]
      },
      options: opcionesBase()
    };

    const configGaussTotal = {
      type: "line",
      data: {
        labels: generarEtiquetasGauss(promedioGeneral),
        datasets: [{
          label: "Campana de Gauss",
          data: generarDatosGauss(promedioGeneral),
          borderDash: [5, 5],
          fill: false,
          pointRadius: 0,
        }]
      },
      options: opcionesBase()
    };

    // Renderizar todas
    renderChart("grafica-linea", configLineal);
    renderChart("grafica-barras", configBarras);
    renderChart("grafica-pastel", configPastel);
    renderChart("grafica-gauss", configGauss);
    renderChart("grafica-linea-total", configLinealTotal);
    renderChart("grafica-barras-total", configBarrasTotal);
    renderChart("grafica-pastel-total", configPastelTotal);
    renderChart("grafica-gauss-total", configGaussTotal);

    actualizarVisibilidadGraficas();
  }

  function renderChart(id, config) {
    const canvas = document.getElementById(id);
    if (!canvas) return;
    if (charts[id]) charts[id].destroy();
    charts[id] = new Chart(canvas, config);
  }

  function generarColor() {
    const r = Math.floor(Math.random() * 156) + 100;
    const g = Math.floor(Math.random() * 156) + 100;
    const b = Math.floor(Math.random() * 156) + 100;
    return `rgba(${r},${g},${b},0.7)`;
  }

  function opcionesBase() {
    return {
      responsive: true,
      plugins: {
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
          max: 10,
          ticks: {
            stepSize: 1
          }
        }
      }
    };
  }

  function generarEtiquetasGauss(prom) {
    const min = Math.max(0, prom - 3);
    const max = Math.min(10, prom + 3);
    const step = 0.1;
    const etiquetas = [];
    for (let x = min; x <= max; x += step) etiquetas.push(x.toFixed(1));
    return etiquetas;
  }

  function generarDatosGauss(media) {
    const sigma = 1;
    return generarEtiquetasGauss(media).map(x => {
      const val = (1 / (sigma * Math.sqrt(2 * Math.PI))) * Math.exp(-0.5 * ((x - media) / sigma) ** 2);
      return (val * 100).toFixed(2);
    });
  }

  renderGraficas();
});
