document.addEventListener('DOMContentLoaded', function () {
  if (!datosEvaluacion || datosEvaluacion.length === 0) return;

  const charts = {};
  const filtros = document.getElementById('filtrosContainer');

  const opcionesConEtiquetas = {
    responsive: true,
    plugins: {
      datalabels: {
        anchor: 'end',
        align: 'top',
        formatter: value => value.toFixed(2),
        font: { weight: 'bold' },
        color: '#000'
      }
    }
  };

  function renderTotalCharts() {
    const etiquetas = ['Promedio Total'];
    const promedioTotal = datosEvaluacion.reduce((acc, obj) => acc + obj.promedio, 0) / datosEvaluacion.length;
    const promedios = [parseFloat(promedioTotal.toFixed(2))];

    if (document.getElementById('lineaTotal').checked) {
      const ctx = document.getElementById('grafica-linea-total').getContext('2d');
      charts.lineaTotal = new Chart(ctx, {
        type: 'line',
        data: {
          labels: etiquetas,
          datasets: [{
            label: 'Promedio General',
            data: promedios,
            borderWidth: 2,
            fill: false,
            tension: 0.4
          }]
        },
        options: opcionesConEtiquetas,
        plugins: [ChartDataLabels]
      });
    }

    if (document.getElementById('barrasTotal').checked) {
      const ctx = document.getElementById('grafica-barras-total').getContext('2d');
      charts.barrasTotal = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: etiquetas,
          datasets: [{
            label: 'Promedio General',
            data: promedios,
            backgroundColor: '#007bff'
          }]
        },
        options: opcionesConEtiquetas,
        plugins: [ChartDataLabels]
      });
    }

    if (document.getElementById('pastelTotal').checked) {
      const ctx = document.getElementById('grafica-pastel-total').getContext('2d');
      charts.pastelTotal = new Chart(ctx, {
        type: 'pie',
        data: {
          labels: etiquetas,
          datasets: [{
            label: 'Promedio General',
            data: promedios,
            backgroundColor: ['#007bff']
          }]
        },
        options: opcionesConEtiquetas,
        plugins: [ChartDataLabels]
      });
    }

    if (document.getElementById('gaussTotal').checked) {
      const ctx = document.getElementById('grafica-gauss-total').getContext('2d');
      charts.gaussTotal = new Chart(ctx, {
        type: 'line',
        data: {
          labels: etiquetas,
          datasets: [{
            label: 'Distribución Gaussiana',
            data: calcularGauss(promedios),
            fill: true,
            tension: 0.4,
            borderWidth: 2
          }]
        },
        options: opcionesConEtiquetas,
        plugins: [ChartDataLabels]
      });
    }
  }

  const select = document.getElementById('select-ciclos');
  const choices = new Choices(select, {
    removeItemButton: true,
    placeholder: true,
    placeholderValue: 'Selecciona ciclos',
    searchEnabled: false
  });

  const ciclosUnicos = [...new Set(datosEvaluacion.map(d => d.ciclo))];
  ciclosUnicos.forEach(ciclo => {
    const option = new Option(ciclo, ciclo, true, true);
    select.add(option);
  });
  choices.setChoices(ciclosUnicos.map(c => ({ value: c, label: c, selected: true })), 'value', 'label', true);

  function renderCicloCharts() {
    const seleccionados = Array.from(select.selectedOptions).map(opt => opt.value);
    const filtrados = datosEvaluacion.filter(d => seleccionados.includes(d.ciclo));
    const etiquetas = filtrados.map(d => d.ciclo);
    const datos = filtrados.map(d => d.promedio);

    if (document.getElementById('linea').checked) {
      const ctx = document.getElementById('grafica-linea').getContext('2d');
      charts.linea = new Chart(ctx, {
        type: 'line',
        data: {
          labels: etiquetas,
          datasets: [{
            label: 'Promedio por ciclo',
            data: datos,
            borderWidth: 2,
            fill: false,
            tension: 0.4
          }]
        },
        options: opcionesConEtiquetas,
        plugins: [ChartDataLabels]
      });
    }

    if (document.getElementById('barras').checked) {
      const ctx = document.getElementById('grafica-barras').getContext('2d');
      charts.barras = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: etiquetas,
          datasets: [{
            label: 'Promedio por ciclo',
            data: datos
          }]
        },
        options: opcionesConEtiquetas,
        plugins: [ChartDataLabels]
      });
    }

    if (document.getElementById('pastel').checked) {
      const ctx = document.getElementById('grafica-pastel').getContext('2d');
      charts.pastel = new Chart(ctx, {
        type: 'pie',
        data: {
          labels: etiquetas,
          datasets: [{
            label: 'Promedio por ciclo',
            data: datos
          }]
        },
        options: opcionesConEtiquetas,
        plugins: [ChartDataLabels]
      });
    }

    if (document.getElementById('gauss').checked) {
      const ctx = document.getElementById('grafica-gauss').getContext('2d');
      charts.gauss = new Chart(ctx, {
        type: 'line',
        data: {
          labels: etiquetas,
          datasets: [{
            label: 'Distribución Gaussiana',
            data: calcularGauss(datos),
            fill: true,
            tension: 0.4,
            borderWidth: 2
          }]
        },
        options: opcionesConEtiquetas,
        plugins: [ChartDataLabels]
      });
    }
  }

  function calcularGauss(datos) {
    if (datos.length <= 1) return datos.map(() => 1);
    const media = datos.reduce((a, b) => a + b, 0) / datos.length;
    const desviacion = Math.sqrt(datos.reduce((sum, val) => sum + Math.pow(val - media, 2), 0) / datos.length);
    if (desviacion === 0 || isNaN(desviacion)) return datos.map(() => 1);
    return datos.map(x => {
      const exponente = -Math.pow(x - media, 2) / (2 * Math.pow(desviacion, 2));
      return (1 / (desviacion * Math.sqrt(2 * Math.PI))) * Math.exp(exponente);
    });
  }

  function destruirGraficas() {
    for (let key in charts) {
      if (charts[key]) charts[key].destroy();
    }
  }

  document.querySelectorAll('.form-check-input').forEach(input => {
    input.addEventListener('change', () => {
      destruirGraficas();
      renderTotalCharts();
      renderCicloCharts();
    });
  });

  select.addEventListener('change', () => {
    destruirGraficas();
    renderTotalCharts();
    renderCicloCharts();
  });

  document.getElementById('btnDescargarPDF').addEventListener('click', () => {
    if (filtros) filtros.style.display = 'none';

    const element = document.getElementById('contenidoParaPDF');
    const opt = {
      margin: 0.2,
      filename: 'evaluacion_docente_concentrado.pdf',
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { scale: 2 },
      jsPDF: { unit: 'in', format: 'a4', orientation: 'landscape' }
    };

    html2pdf().set(opt).from(element).save().then(() => {
      if (filtros) filtros.style.display = 'block';
    });
  });

  renderTotalCharts();
  renderCicloCharts();
});
