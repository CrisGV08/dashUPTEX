const datos = JSON.parse(document.getElementById('datos-json').textContent);
const selectCiclos = document.getElementById('filtro-ciclos');
const choices = new Choices(selectCiclos, {
  removeItemButton: true,
  shouldSort: false,
  searchEnabled: false,
});

let chartBarras, chartLinea, chartPastel, chartGauss;

function actualizarGraficas() {
  const ciclosSeleccionados = Array.from(selectCiclos.options)
    .filter(opt => opt.selected)
    .map(opt => opt.value);

  const indices = datos.labels
    .map((label, i) => ciclosSeleccionados.includes(label) ? i : -1)
    .filter(i => i !== -1);

  const labels = indices.map(i => datos.labels[i]);
  const mujeres = indices.map(i => datos.mujeres[i]);
  const hombres = indices.map(i => datos.hombres[i]);
  const totales = indices.map(i => datos.totales[i]);

  const pie_data = [
    mujeres.reduce((a, b) => a + b, 0),
    hombres.reduce((a, b) => a + b, 0)
  ];

  [chartBarras, chartLinea, chartPastel, chartGauss].forEach(c => c?.destroy());

  if (document.querySelector('input[value="graficaBarras"]').checked) {
    chartBarras = new Chart(document.getElementById('graficaBarras'), {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          { label: 'Mujeres', data: mujeres, backgroundColor: '#f06292' },
          { label: 'Hombres', data: hombres, backgroundColor: '#64b5f6' }
        ]
      },
      options: {
        responsive: true,
        scales: { x: { stacked: true }, y: { stacked: true, beginAtZero: true } }
      }
    });
  }

  if (document.querySelector('input[value="graficaLinea"]').checked) {
    chartLinea = new Chart(document.getElementById('graficaLinea'), {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          { label: 'Mujeres', data: mujeres, borderColor: '#f06292', fill: false },
          { label: 'Hombres', data: hombres, borderColor: '#64b5f6', fill: false }
        ]
      },
      options: { responsive: true, scales: { y: { beginAtZero: true } } }
    });
  }

  if (document.querySelector('input[value="graficaPastel"]').checked) {
    chartPastel = new Chart(document.getElementById('graficaPastel'), {
      type: 'pie',
      data: {
        labels: ['Mujeres', 'Hombres'],
        datasets: [{ data: pie_data, backgroundColor: ['#f06292', '#64b5f6'] }]
      },
      options: { responsive: true }
    });
  }

  if (document.querySelector('input[value="graficaGauss"]').checked) {
    const gaussData = generarGaussiana(totales);
    chartGauss = new Chart(document.getElementById('graficaGauss'), {
      type: 'line',
      data: {
        labels: gaussData.x_vals,
        datasets: [{
          label: 'Gauss',
          data: gaussData.y_vals,
          borderColor: '#9c27b0',
          backgroundColor: 'rgba(156, 39, 176, 0.2)',
          fill: true
        }]
      },
      options: { responsive: true }
    });
  }
}

function generarGaussiana(datos) {
  if (!datos.length) return { x_vals: [], y_vals: [] };
  const media = datos.reduce((a, b) => a + b, 0) / datos.length;
  const desviacion = Math.sqrt(datos.reduce((a, b) => a + Math.pow(b - media, 2), 0) / datos.length);
  const x_vals = [], y_vals = [];
  for (let i = -3; i <= 3; i += 0.1) {
    const x = media + i * desviacion;
    const y = (1 / (desviacion * Math.sqrt(2 * Math.PI))) * Math.exp(-0.5 * Math.pow((x - media) / desviacion, 2));
    x_vals.push(x.toFixed(1)); y_vals.push(y);
  }
  return { x_vals, y_vals };
}

document.querySelectorAll('.filtro-grafica').forEach(cb => cb.addEventListener('change', actualizarGraficas));
selectCiclos.addEventListener('change', () => requestAnimationFrame(actualizarGraficas));

actualizarGraficas();
