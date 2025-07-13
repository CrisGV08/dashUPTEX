document.addEventListener('DOMContentLoaded', function () {
  if (!Array.isArray(datosEvaluacion) || datosEvaluacion.length === 0) return;

  const coloresPorCiclo = {};
  const paletaColores = [
    '#4e79a7', '#f28e2b', '#e15759', '#76b7b2', '#59a14f',
    '#edc948', '#b07aa1', '#ff9da7', '#9c755f', '#bab0ab'
  ];

  const ciclosUnicos = [...new Set(datosEvaluacion.map(d => d.ciclo))];
  ciclosUnicos.forEach((ciclo, index) => {
    coloresPorCiclo[ciclo] = paletaColores[index % paletaColores.length];
  });

  const selectCiclos = document.getElementById('selectCiclos');
  ciclosUnicos.forEach(ciclo => {
    const option = document.createElement('option');
    option.value = ciclo;
    option.textContent = ciclo;
    selectCiclos.appendChild(option);
  });

  const choicesCiclos = new Choices(selectCiclos, {
    removeItemButton: true,
    placeholderValue: 'Selecciona ciclos',
    searchEnabled: false,
    shouldSort: false
  });

  function filtrarDatos() {
    const seleccionados = choicesCiclos.getValue(true);
    return datosEvaluacion.filter(d => seleccionados.length === 0 || seleccionados.includes(d.ciclo));
  }

  function obtenerEtiquetasYValores(datos) {
    return {
      etiquetas: datos.map(d => d.ciclo),
      valores: datos.map(d => d.promedio)
    };
  }

  function renderizarGraficaLineal(datos) {
    const ctx = document.getElementById('graficaLineal').getContext('2d');
    return new Chart(ctx, {
      type: 'line',
      data: {
        labels: datos.map(d => d.ciclo),
        datasets: [{
          label: 'Promedio',
          data: datos.map(d => d.promedio),
          borderColor: '#007bff',
          backgroundColor: 'rgba(0, 123, 255, 0.1)',
          tension: 0.3
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } }
      }
    });
  }

  function renderizarGraficaBarras(datos) {
    const ctx = document.getElementById('graficaBarras').getContext('2d');
    return new Chart(ctx, {
      type: 'bar',
      data: {
        labels: datos.map(d => d.ciclo),
        datasets: [{
          label: 'Promedio',
          data: datos.map(d => d.promedio),
          backgroundColor: datos.map(d => coloresPorCiclo[d.ciclo])
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } }
      }
    });
  }

  function renderizarGraficaPastel(datos) {
    const ctx = document.getElementById('graficaPastel').getContext('2d');
    return new Chart(ctx, {
      type: 'pie',
      data: {
        labels: datos.map(d => d.ciclo),
        datasets: [{
          label: 'Promedio',
          data: datos.map(d => d.promedio),
          backgroundColor: datos.map(d => coloresPorCiclo[d.ciclo])
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { position: 'right' } }
      }
    });
  }

  function renderizarGraficaGauss(datos) {
    const ctx = document.getElementById('graficaGauss').getContext('2d');
    const media = datos.reduce((acc, val) => acc + val.promedio, 0) / datos.length;
    const desviacion = Math.sqrt(datos.reduce((acc, val) => acc + Math.pow(val.promedio - media, 2), 0) / datos.length);

    const etiquetas = [];
    const valores = [];
    for (let x = media - 3 * desviacion; x <= media + 3 * desviacion; x += 0.1) {
      etiquetas.push(x.toFixed(1));
      const gauss = (1 / (desviacion * Math.sqrt(2 * Math.PI))) * Math.exp(-0.5 * Math.pow((x - media) / desviacion, 2));
      valores.push(gauss);
    }

    return new Chart(ctx, {
      type: 'line',
      data: {
        labels: etiquetas,
        datasets: [{
          label: 'Distribución Normal',
          data: valores,
          borderColor: '#8e44ad',
          fill: true,
          backgroundColor: 'rgba(142, 68, 173, 0.2)',
          tension: 0.4
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } }
      }
    });
  }

  let charts = {};

  function actualizarGraficas() {
    const datosFiltrados = filtrarDatos();
    if (charts.lineal) charts.lineal.destroy();
    if (charts.barras) charts.barras.destroy();
    if (charts.pastel) charts.pastel.destroy();
    if (charts.gauss) charts.gauss.destroy();

    if (document.querySelector('input[value="lineal"]').checked) {
      charts.lineal = renderizarGraficaLineal(datosFiltrados);
    }
    if (document.querySelector('input[value="barras"]').checked) {
      charts.barras = renderizarGraficaBarras(datosFiltrados);
    }
    if (document.querySelector('input[value="pastel"]').checked) {
      charts.pastel = renderizarGraficaPastel(datosFiltrados);
    }
    if (document.querySelector('input[value="gauss"]').checked) {
      charts.gauss = renderizarGraficaGauss(datosFiltrados);
    }
  }

  actualizarGraficas();

  document.querySelectorAll('.grafica-check').forEach(check => {
    check.addEventListener('change', actualizarGraficas);
  });

  selectCiclos.addEventListener('change', actualizarGraficas);
});
