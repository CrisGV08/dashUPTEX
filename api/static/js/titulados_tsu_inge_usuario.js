// static/js/titulados_tsu_inge_usuario.js
(() => {
  const root = document.getElementById('tsui-user-root');
  if (!root) return;

  const API_LIST  = root.dataset.apiList;       // {% url 'tsui_api_public' %}
  const API_PROGS = root.dataset.apiProgramas;  // {% url 'tsui_programas_api_public' %}

  // UI refs
  const tabTodos = document.getElementById('tabTodos');
  const tabTSU   = document.getElementById('tabTSU');
  const tabING   = document.getElementById('tabING');

  const ptTodos = document.getElementById('ptTodos');
  const ptAnt   = document.getElementById('ptAntiguo');
  const ptNvo   = document.getElementById('ptNuevo');

  const filtroCarrera = document.getElementById('filtroCarrera');
  const anioIngreso   = document.getElementById('anioIngreso');
  const anioEgreso    = document.getElementById('anioEgreso');
  const btnAplicar    = document.getElementById('btnAplicar');
  const btnReset      = document.getElementById('btnReset');

  const chipCount = document.getElementById('chipCount');
  const tbody     = document.getElementById('tbody');

  // Estado
  let nivelActivo = 'TODOS'; // TODOS|TSU|ING
  let progTipo    = 'todos'; // todos|antiguo|nuevo

  // Helpers
  function setActive(el, group) { group.forEach(e => e.classList.remove('active')); el.classList.add('active'); }

  async function loadProgramasFor(tipo, selectEl) {
    selectEl.innerHTML = '';
    if (tipo !== 'antiguo' && tipo !== 'nuevo') {
      const opt = document.createElement('option'); opt.value=''; opt.textContent='Todas';
      selectEl.appendChild(opt); return;
    }
    const res = await fetch(`${API_PROGS}?tipo=${encodeURIComponent(tipo)}`);
    const data = await res.json();
    const items = (data && data.items) || [];
    const optAll = document.createElement('option'); optAll.value=''; optAll.textContent='Todas';
    selectEl.appendChild(optAll);
    for (const it of items) {
      const opt = document.createElement('option'); opt.value = it.id; opt.textContent = it.nombre;
      selectEl.appendChild(opt);
    }
  }

  async function fillFiltroCarrera() {
    if (progTipo === 'antiguo' || progTipo === 'nuevo') {
      await loadProgramasFor(progTipo, filtroCarrera);
    } else {
      filtroCarrera.innerHTML = '';
      const optAll = document.createElement('option'); optAll.value=''; optAll.textContent='Todas';
      filtroCarrera.appendChild(optAll);
    }
  }

  function renderTable(items) {
    tbody.innerHTML = '';
    chipCount.textContent = items.length;
    for (const r of items) {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${r.nivel}</td>
        <td>${r.programa}</td>
        <td>${r.ingreso}</td>
        <td>${r.egreso}</td>
        <td>${r.ing_h}</td>
        <td>${r.ing_m}</td>
        <td>${r.eg_coh_h}</td>
        <td>${r.eg_coh_m}</td>
        <td>${r.eg_rez_h}</td>
        <td>${r.eg_rez_m}</td>
        <td>${r.tit_h}</td>
        <td>${r.tit_m}</td>
        <td>${r.dgp_h}</td>
        <td>${r.dgp_m}</td>
        <td>${r.tasa}</td>
      `;
      tbody.appendChild(tr);
    }
  }

  let chart;
  function drawChart(tasas, type='bar') {
    const ctx = document.getElementById('chart').getContext('2d');
    if (chart) chart.destroy();
    chart = new Chart(ctx, {
      type,
      data: {
        labels: ['TSU', 'Ingeniería'],
        datasets: [{ label: 'Tasa de titulación (%)', data: [tasas.TSU || 0, tasas.ING || 0] }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: type === 'pie' }, tooltip: { enabled: true } },
        scales: type === 'pie' ? {} : { y: { beginAtZero: true, max: 100 } }
      },
      plugins: [window.chartValueLabelPlugin]
    });
  }

  async function cargar() {
    const params = new URLSearchParams();
    if (nivelActivo !== 'TODOS') params.set('nivel', nivelActivo);
    if (progTipo === 'antiguo' || progTipo === 'nuevo') params.set('prog_tipo', progTipo);
    if (filtroCarrera.value) params.set('programa', filtroCarrera.value);
    if (anioIngreso.value) params.set('anio_ing', anioIngreso.value);
    if (anioEgreso.value)  params.set('anio_egr', anioEgreso.value);

    const res = await fetch(`${API_LIST}?${params.toString()}`);
    const data = await res.json();
    if (!data.ok) { alert('Error al cargar'); return; }
    renderTable(data.items || []);
    drawChart(data.tasas || {TSU:0, ING:0});
  }

  // Eventos
  tabTodos.addEventListener('click', () => { setActive(tabTodos,[tabTodos,tabTSU,tabING]); nivelActivo='TODOS'; cargar(); });
  tabTSU  .addEventListener('click', () => { setActive(tabTSU,  [tabTodos,tabTSU,tabING]); nivelActivo='TSU'; cargar(); });
  tabING  .addEventListener('click', () => { setActive(tabING,  [tabTodos,tabTSU,tabING]); nivelActivo='ING'; cargar(); });

  ptTodos.addEventListener('click', async () => { setActive(ptTodos,[ptTodos,ptAnt,ptNvo]); progTipo='todos'; await fillFiltroCarrera(); cargar(); });
  ptAnt  .addEventListener('click', async () => { setActive(ptAnt,  [ptTodos,ptAnt,ptNvo]); progTipo='antiguo'; await fillFiltroCarrera(); cargar(); });
  ptNvo  .addEventListener('click', async () => { setActive(ptNvo,  [ptTodos,ptAnt,ptNvo]); progTipo='nuevo';   await fillFiltroCarrera(); cargar(); });

  btnAplicar.addEventListener('click', cargar);
  btnReset  .addEventListener('click', async () => {
    progTipo='todos'; setActive(ptTodos,[ptTodos,ptAnt,ptNvo]);
    nivelActivo='TODOS'; setActive(tabTodos,[tabTodos,tabTSU,tabING]);
    anioIngreso.value=''; anioEgreso.value='';
    await fillFiltroCarrera();
    cargar();
  });

  // Cambio tipo gráfico
  document.querySelectorAll('[data-chart]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('[data-chart]').forEach(b=>b.classList.remove('active'));
      btn.classList.add('active');
      const type = btn.dataset.chart;
      const tasas = chart?.data ? {TSU: chart.data.datasets[0].data[0], ING: chart.data.datasets[0].data[1]} : {TSU:0,ING:0};
      drawChart(tasas, type);
    });
  });

  (async () => {
    await fillFiltroCarrera();
    await cargar();
  })();
})();
