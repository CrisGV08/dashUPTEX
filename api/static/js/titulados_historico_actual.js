document.addEventListener('DOMContentLoaded', function () {
  // ===== Helpers
  const $ = sel => document.querySelector(sel);
  const $$ = sel => Array.from(document.querySelectorAll(sel));

  // ===== Choices en select servidor (IDs)
  const srv = $('#selectCarrerasServer');
  let choicesSrv = null;
  if (srv) choicesSrv = new Choices(srv, { removeItemButton: true, searchEnabled: true, placeholderValue: 'Carreras (BD)' });

  // ===== Píldoras de año (setean el select real)
  const anioReal = $('#anioReal');
  const pillsAnios = $('#pillsAnios');
  if (pillsAnios && anioReal) {
    pillsAnios.addEventListener('click', (e) => {
      const btn = e.target.closest('.pill');
      if (!btn) return;
      $$('.pill').forEach(x => x.classList.remove('active'));
      btn.classList.add('active');
      anioReal.value = btn.dataset.valor || '';
    });
  }

  // ===== Acciones rápidas en select servidor
  if (choicesSrv) {
    $('#srvSelTodos')?.addEventListener('click', () => {
      choicesSrv.setValue(Array.from(srv.options).map(o => ({ value: o.value, label: o.textContent })));
    });
    $('#srvSelNinguno')?.addEventListener('click', () => choicesSrv.removeActiveItems());
    $('#srvSelInvertir')?.addEventListener('click', () => {
      const actuales = new Set(choicesSrv.getValue(true));
      const nuevas = Array.from(srv.options)
        .filter(o => !actuales.has(o.value))
        .map(o => ({ value: o.value, label: o.textContent }));
      choicesSrv.removeActiveItems();
      choicesSrv.setValue(nuevas);
    });
  }

  // ===== Filtros visuales (no recarga)
  if (!Array.isArray(datosGeneraciones)) return;

  const selectCli = $('#selectCarreras');
  let choicesCli = null;
  if (selectCli) {
    const carrerasUnicas = [...new Set(datosGeneraciones.map(g => g.nombre_programa))].sort();
    carrerasUnicas.forEach(nom => {
      const opt = document.createElement('option');
      opt.value = nom; opt.textContent = nom;
      selectCli.appendChild(opt);
    });
    choicesCli = new Choices(selectCli, { removeItemButton: true, searchEnabled: true, placeholderValue: 'Selecciona carreras' });
  }

  // Botones rápidos (visual)
  $('#cliSelTodos')?.addEventListener('click', () => {
    if (!choicesCli) return;
    const vals = Array.from(selectCli.options).map(o => ({ value: o.value, label: o.textContent }));
    choicesCli.setValue(vals);
    actualizarTodo();
  });
  $('#cliSelNinguno')?.addEventListener('click', () => { choicesCli?.removeActiveItems(); actualizarTodo(); });
  $('#cliSelInvertir')?.addEventListener('click', () => {
    if (!choicesCli) return;
    const actuales = new Set(choicesCli.getValue(true));
    const nuevas = Array.from(selectCli.options)
      .filter(o => !actuales.has(o.value))
      .map(o => ({ value: o.value, label: o.textContent }));
    choicesCli.removeActiveItems();
    choicesCli.setValue(nuevas);
    actualizarTodo();
  });

  const buscador = $('#buscadorCarrera');

  // ===== Dataset + gráficas
  let datasetBase = [...datosGeneraciones];
  let datasetActual = [...datosGeneraciones];

  const labels = () => datasetActual.map(g => `${g.nombre_programa} (${g.anio})`);
  const tasas  = () => datasetActual.map(g => g.tasa_titulacion);

  const charts = {};

  charts.lineal = new Chart($('#graficaLineal'), {
    type: 'line',
    data: { labels: labels(), datasets: [{ label: 'Tasa de Titulación (%)', data: tasas(), fill: true, tension: 0.35 }] },
    options: {
      plugins: { title: { display: true, text: 'Tasa de Titulación - Línea' }, legend: { display: false } },
      scales: { y: { beginAtZero: true, title: { display: true, text: '%' } } }
    }
  });

  charts.barras = new Chart($('#graficaBarras'), {
    type: 'bar',
    data: { labels: labels(), datasets: [{ label: 'Tasa de Titulación (%)', data: tasas() }] },
    options: { plugins: { title: { display: true, text: 'Tasa de Titulación - Barras' } }, scales: { y: { beginAtZero: true } } }
  });

  function recomputaPastel() {
    const sumas = {};
    datasetActual.forEach(g => { sumas[g.nombre_programa] = (sumas[g.nombre_programa] || 0) + g.tasa_titulacion; });
    return { labels: Object.keys(sumas), data: Object.values(sumas) };
  }
  const p0 = recomputaPastel();
  charts.pastel = new Chart($('#graficaPastel'), {
    type: 'pie',
    data: { labels: p0.labels, datasets: [{ data: p0.data }] },
    options: { plugins: { title: { display: true, text: 'Distribución de Tasa - Pastel' } } }
  });

  function datosGauss(y) {
    const n = y.length || 1;
    const media = y.reduce((a,b)=>a+b,0)/n;
    const desv  = Math.sqrt(y.reduce((acc,v)=>acc+Math.pow(v-media,2),0)/n) || 1;
    const xs = Array.from({length:100}, (_,i)=> media-3*desv + i*(6*desv/100));
    const ys = xs.map(x => (1/(desv*Math.sqrt(2*Math.PI)))*Math.exp(-0.5*Math.pow((x-media)/desv,2)));
    return { xs, ys };
  }
  const g0 = datosGauss(tasas());
  charts.gauss = new Chart($('#graficaGauss'), {
    type: 'line',
    data: { labels: g0.xs.map(v=>v.toFixed(1)), datasets: [{ label: 'Distribución Gaussiana', data: g0.ys, fill: true }] },
    options: {
      plugins: { title: { display: true, text: 'Distribución Gaussiana (simulada)' } },
      scales: { y: { beginAtZero: true }, x: { title: { display: true, text: 'Tasa (%)' } } }
    }
  });

  // ===== Actualización global (gráficas + tabla)
  function actualizarTodo() {
    const seleccionadas = choicesCli ? new Set(choicesCli.getValue(true)) : new Set();
    const filtroNombre = (buscador?.value || '').toLowerCase();

    datasetActual = datasetBase.filter(g => {
      const pasaCarrera = (seleccionadas.size === 0) || seleccionadas.has(g.nombre_programa);
      const pasaTexto   = g.nombre_programa.toLowerCase().includes(filtroNombre);
      return pasaCarrera && pasaTexto;
    });

    // Gráficas
    charts.lineal.data.labels = labels();
    charts.lineal.data.datasets[0].data = tasas();
    charts.lineal.update();

    charts.barras.data.labels = labels();
    charts.barras.data.datasets[0].data = tasas();
    charts.barras.update();

    const p = recomputaPastel();
    charts.pastel.data.labels = p.labels;
    charts.pastel.data.datasets[0].data = p.data;
    charts.pastel.update();

    const y = tasas();
    const g = datosGauss(y);
    charts.gauss.data.labels = g.xs.map(v=>v.toFixed(1));
    charts.gauss.data.datasets[0].data = g.ys;
    charts.gauss.update();

    // Tabla (visual)
    $$('#tablaGeneraciones tbody tr').forEach(tr => {
      const prog = (tr.dataset.programa || '').toLowerCase();
      const visible = (filtroNombre === '' || prog.includes(filtroNombre)) &&
        (seleccionadas.size === 0 || seleccionadas.has(tr.dataset.programa));
      tr.style.display = visible ? '' : 'none';
    });
  }

  // Eventos visuales
  selectCli?.addEventListener('change', actualizarTodo);
  buscador?.addEventListener('input', actualizarTodo);

  // Toggle de cada canvas + estilo chip activo
  $$('.filtro-grafica').forEach(cb => {
    cb.addEventListener('change', () => {
      const cnv = document.getElementById(cb.value);
      if (!cnv) return;
      cnv.style.display = cb.checked ? 'block' : 'none';
      cb.closest('.chip')?.classList.toggle('active', cb.checked);
    });
  });

  // PDF
  $('#btnDescargarPDF')?.addEventListener('click', async () => {
    const area = $('#contenedorPDF');
    if (!area) return;
    const opt = {
      margin: 0.5,
      filename: 'titulados_historico_actual.pdf',
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { scale: 3, useCORS: true },
      jsPDF: { unit: 'in', format: 'letter', orientation: 'landscape' }
    };
    await html2pdf().set(opt).from(area).save();
  });
});
