(() => {
  const root = document.getElementById('tsui-root');
  if (!root) return;

  const API_LIST   = root.dataset.apiList;
  const API_PROGS  = root.dataset.apiProgramas;
  const API_CREATE = root.dataset.apiCreate;
  const API_UD     = root.dataset.apiUdBase.replace(/1\/?$/, ''); // base para /<id>/

  // --------- UI refs
  const tabTodos = document.getElementById('tabTodos');
  const tabTSU   = document.getElementById('tabTSU');
  const tabING   = document.getElementById('tabING');

  const ptTodos = document.getElementById('ptTodos');
  const ptAnt   = document.getElementById('ptAntiguo');
  const ptNvo   = document.getElementById('ptNuevo');

  const filtroCarrera = document.getElementById('filtroCarrera');
  const anioIngreso = document.getElementById('anioIngreso');
  const anioEgreso  = document.getElementById('anioEgreso');

  const btnAplicar = document.getElementById('btnAplicar');
  const btnReset   = document.getElementById('btnReset');
  const btnPdf     = document.getElementById('btnPdf');
  const chipCount  = document.getElementById('chipCount');

  const tbody = document.getElementById('tbody');

  // Modal
  const modalBk = document.getElementById('modalBk');
  const btnNuevo = document.getElementById('btnNuevo');
  const btnCloseModal = document.getElementById('btnCloseModal');
  const btnCancelModal = document.getElementById('btnCancelModal');
  const form = document.getElementById('formRegistro');
  const modalTitle = document.getElementById('modalTitle');

  const f_id = document.getElementById('f_id');
  const f_nivel = document.getElementById('f_nivel');
  const f_prog_tipo = document.getElementById('f_prog_tipo');
  const f_programa = document.getElementById('f_programa');
  const f_mes_ing = document.getElementById('f_mes_ing');
  const f_anio_ing = document.getElementById('f_anio_ing');
  const f_mes_egr = document.getElementById('f_mes_egr');
  const f_anio_egr = document.getElementById('f_anio_egr');
  const f_ing_h = document.getElementById('f_ing_h');
  const f_ing_m = document.getElementById('f_ing_m');
  const f_eg_coh_h = document.getElementById('f_eg_coh_h');
  const f_eg_coh_m = document.getElementById('f_eg_coh_m');
  const f_eg_rez_h = document.getElementById('f_eg_rez_h');
  const f_eg_rez_m = document.getElementById('f_eg_rez_m');
  const f_tit_h = document.getElementById('f_tit_h');
  const f_tit_m = document.getElementById('f_tit_m');
  const f_dgp_h = document.getElementById('f_dgp_h');
  const f_dgp_m = document.getElementById('f_dgp_m');

  // --------- estado
  let nivelActivo = 'TODOS';     // botones superiores
  let progTipo = 'todos';        // filtro (todos|antiguo|nuevo)
  let itemsById = new Map();     // cache de filas

  // --------- helpers
  const pad = (n) => String(n).padStart(2, '0');
  function parseMMYYYY(s){
    if(!s) return {m:1,y:2000};
    const [mm,yy] = s.split('-').map(x=>parseInt(x,10));
    return {m:mm||1, y:yy||2000};
  }

  function setActive(elm, group) {
    group.forEach(e => e.classList.remove('active'));
    elm.classList.add('active');
  }

  async function loadProgramasFor(tipo, selectEl) {
    selectEl.innerHTML = '';
    if (tipo !== 'antiguo' && tipo !== 'nuevo') {
      const opt = document.createElement('option');
      opt.value = ''; opt.textContent = '—';
      selectEl.appendChild(opt);
      return;
    }
    const url = `${API_PROGS}?tipo=${encodeURIComponent(tipo)}`;
    const res = await fetch(url);
    const data = await res.json();
    const items = (data && data.items) || [];
    for (const it of items) {
      const opt = document.createElement('option');
      opt.value = it.id;
      opt.textContent = it.nombre;
      selectEl.appendChild(opt);
    }
  }

  async function fillFiltroCarrera() {
    filtroCarrera.innerHTML = '';
    if (progTipo === 'antiguo' || progTipo === 'nuevo') {
      await loadProgramasFor(progTipo, filtroCarrera);
      const opt = document.createElement('option');
      opt.value = '';
      opt.textContent = 'Todas';
      filtroCarrera.prepend(opt);
      filtroCarrera.value = '';
    } else {
      const opt = document.createElement('option');
      opt.value = '';
      opt.textContent = 'Todas';
      filtroCarrera.appendChild(opt);
    }
  }

  // --------- tabla
  function renderTable(items) {
    tbody.innerHTML = '';
    itemsById.clear();
    chipCount.textContent = items.length;

    for (const r of items) {
      itemsById.set(String(r.id), r);
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
        <td>
          <button class="btn btn-sm" data-act="edit" data-id="${r.id}">Editar</button>
          <button class="btn btn-sm warn" data-act="del" data-id="${r.id}">Eliminar</button>
        </td>
      `;
      tbody.appendChild(tr);
    }
  }

  // --- Plugin para mostrar el valor (% ) en la gráfica ---
  const valueLabelPlugin = {
    id: 'valueLabel',
    afterDatasetsDraw(chart, args, pluginOptions) {
      const { ctx } = chart;
      const type = chart.config.type;
      const ds = chart.data.datasets[0];
      const meta = chart.getDatasetMeta(0);
      if (!ds || !meta) return;

      ctx.save();
      ctx.font = (pluginOptions && pluginOptions.font) || '12px sans-serif';
      ctx.fillStyle = (pluginOptions && pluginOptions.color) || '#111';
      ctx.textAlign = 'center';

      meta.data.forEach((el, i) => {
        const val = ds.data[i];
        if (val == null) return;

        const label = `${val}%`;
        const pos = el.tooltipPosition();

        if (type === 'pie') {
          ctx.textBaseline = 'middle';
          ctx.fillText(label, pos.x, pos.y);
        } else {
          ctx.textBaseline = 'bottom';
          ctx.fillText(label, pos.x, pos.y - 6);
        }
      });

      ctx.restore();
    }
  };
  if (window.Chart && !Chart.registry.plugins.get('valueLabel')) {
    Chart.register(valueLabelPlugin);
  }

  // --------- gráfico
  let chart;
  function drawChart(tasas, type='bar') {
    const ctx = document.getElementById('chart').getContext('2d');
    if (chart) chart.destroy();
    chart = new Chart(ctx, {
      type,
      data: {
        labels: ['TSU', 'Ingeniería'],
        datasets: [{
          label: 'Tasa de titulación (%)',
          data: [tasas.TSU || 0, tasas.ING || 0],
        }]
      },
      options: {
        plugins: { valueLabel: { font: '12px sans-serif', color: '#111' } },
        responsive: true,
        scales: type === 'pie' ? {} : { y: { beginAtZero: true, max: 100 } }
      }
    });
  }

  async function cargar() {
    const params = new URLSearchParams();
    if (nivelActivo !== 'TODOS') params.set('nivel', nivelActivo);
    if (progTipo === 'antiguo' || progTipo === 'nuevo') params.set('prog_tipo', progTipo);
    if (filtroCarrera.value) params.set('programa', filtroCarrera.value);
    if (anioIngreso.value) params.set('anio_ing', anioIngreso.value);
    if (anioEgreso.value)  params.set('anio_egr', anioEgreso.value);

    const res = await fetch(`${API_LIST}?${params}`);
    const data = await res.json();
    if (!data.ok) { alert('Error al cargar'); return; }
    renderTable(data.items || []);
    drawChart(data.tasas || {TSU:0, ING:0});
  }

  // --------- eventos de filtros
  tabTodos.addEventListener('click', () => { setActive(tabTodos, [tabTodos,tabTSU,tabING]); nivelActivo='TODOS'; cargar(); });
  tabTSU.addEventListener('click',   () => { setActive(tabTSU,   [tabTodos,tabTSU,tabING]); nivelActivo='TSU';   cargar(); });
  tabING.addEventListener('click',   () => { setActive(tabING,   [tabTodos,tabTSU,tabING]); nivelActivo='ING';   cargar(); });

  ptTodos.addEventListener('click', async () => { setActive(ptTodos,[ptTodos,ptAnt,ptNvo]); progTipo='todos'; await fillFiltroCarrera(); cargar(); });
  ptAnt.addEventListener('click',   async () => { setActive(ptAnt,  [ptTodos,ptAnt,ptNvo]); progTipo='antiguo'; await fillFiltroCarrera(); cargar(); });
  ptNvo.addEventListener('click',   async () => { setActive(ptNvo,  [ptTodos,ptAnt,ptNvo]); progTipo='nuevo';   await fillFiltroCarrera(); cargar(); });

  btnAplicar.addEventListener('click', cargar);
  btnReset.addEventListener('click', async () => {
    progTipo='todos'; setActive(ptTodos,[ptTodos,ptAnt,ptNvo]);
    nivelActivo='TODOS'; setActive(tabTodos,[tabTodos,tabTSU,tabING]);
    anioIngreso.value=''; anioEgreso.value='';
    await fillFiltroCarrera();
    cargar();
  });

  // --------- modal
  function openModal() { modalBk.style.display = 'flex'; }
  function closeModal() { modalBk.style.display = 'none'; }

  async function resetModalForCreate() {
    modalTitle.textContent = 'Nuevo registro';
    f_id.value = '';
    f_nivel.value = 'TSU';
    f_prog_tipo.value = 'antiguo';
    await loadProgramasFor('antiguo', f_programa);
    f_programa.value = '';
    f_mes_ing.value = 1;  f_anio_ing.value = 2020;
    f_mes_egr.value = 12; f_anio_egr.value = 2023;
    f_ing_h.value = 0; f_ing_m.value = 0;
    f_eg_coh_h.value = 0; f_eg_coh_m.value = 0;
    f_eg_rez_h.value = 0; f_eg_rez_m.value = 0;
    f_tit_h.value = 0; f_tit_m.value = 0;
    f_dgp_h.value = 0; f_dgp_m.value = 0;
  }

  btnNuevo.addEventListener('click', async () => {
    await resetModalForCreate();
    openModal();
  });
  btnCloseModal.addEventListener('click', closeModal);
  btnCancelModal.addEventListener('click', closeModal);

  f_prog_tipo.addEventListener('change', async () => {
    await loadProgramasFor(f_prog_tipo.value, f_programa);
  });

  // Delegación acciones Editar/Eliminar
  tbody.addEventListener('click', async (e) => {
    const btn = e.target.closest('button[data-act]');
    if (!btn) return;
    const id = btn.dataset.id;
    const act = btn.dataset.act;

    if (act === 'del') {
      if (!confirm('¿Eliminar este registro?')) return;
      try {
        const res = await fetch(`${API_UD}${id}/`, {
          method: 'DELETE',
          headers: { 'X-CSRFToken': window.CSRF_TOKEN },
        });
        const data = await res.json().catch(()=>({}));
        if (!res.ok || data.ok === false) {
          alert('No se pudo eliminar\n' + (data.error || data.detail || `HTTP ${res.status}`));
          return;
        }
        await cargar();
      } catch (err) {
        alert('No se pudo eliminar\n' + (err.message || 'Error de red'));
      }
      return;
    }

    if (act === 'edit') {
      const r = itemsById.get(String(id));
      if (!r) return;

      modalTitle.textContent = 'Editar registro';
      f_id.value = id;
      f_nivel.value = r.nivel;
      f_prog_tipo.value = r.prog_tipo;
      await loadProgramasFor(r.prog_tipo, f_programa);
      f_programa.value = r.programa_id;

      const ing = parseMMYYYY(r.ingreso);
      const egr = parseMMYYYY(r.egreso);
      f_mes_ing.value = ing.m; f_anio_ing.value = ing.y;
      f_mes_egr.value = egr.m; f_anio_egr.value = egr.y;

      f_ing_h.value = r.ing_h; f_ing_m.value = r.ing_m;
      f_eg_coh_h.value = r.eg_coh_h; f_eg_coh_m.value = r.eg_coh_m;
      f_eg_rez_h.value = r.eg_rez_h; f_eg_rez_m.value = r.eg_rez_m;
      f_tit_h.value = r.tit_h; f_tit_m.value = r.tit_m;
      f_dgp_h.value = r.dgp_h; f_dgp_m.value = r.dgp_m;

      openModal();
    }
  });

  // cambio tipo gráfico
  document.querySelectorAll('[data-chart]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('[data-chart]').forEach(b=>b.classList.remove('active'));
      btn.classList.add('active');
      // mantener valores actuales
      const tsu = chart?.data?.datasets?.[0]?.data?.[0] ?? 0;
      const ing = chart?.data?.datasets?.[0]?.data?.[1] ?? 0;
      drawChart({TSU: tsu, ING: ing}, btn.dataset.chart);
    });
  });

  // --------- submit (CREATE/UPDATE)
  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const payload = {
      nivel: f_nivel.value,
      prog_tipo: f_prog_tipo.value,
      programa: f_programa.value,

      mes_ing: parseInt(f_mes_ing.value || '1', 10),
      anio_ing: parseInt(f_anio_ing.value || '2020', 10),
      mes_egr: parseInt(f_mes_egr.value || '12', 10),
      anio_egr: parseInt(f_anio_egr.value || '2023', 10),

      ing_h: parseInt(f_ing_h.value || '0', 10),
      ing_m: parseInt(f_ing_m.value || '0', 10),

      eg_coh_h: parseInt(f_eg_coh_h.value || '0', 10),
      eg_coh_m: parseInt(f_eg_coh_m.value || '0', 10),

      eg_rez_h: parseInt(f_eg_rez_h.value || '0', 10),
      eg_rez_m: parseInt(f_eg_rez_m.value || '0', 10),

      tit_h: parseInt(f_tit_h.value || '0', 10),
      tit_m: parseInt(f_tit_m.value || '0', 10),

      dgp_h: parseInt(f_dgp_h.value || '0', 10),
      dgp_m: parseInt(f_dgp_m.value || '0', 10),
    };

    if (!payload.programa) { alert('Selecciona un programa.'); return; }
    if (payload.anio_egr < payload.anio_ing || (payload.anio_egr === payload.anio_ing && payload.mes_egr < payload.mes_ing)) {
      alert('La fecha de egreso no puede ser menor que la de ingreso.');
      return;
    }

    const isEdit = !!f_id.value;

    try {
      const res = await fetch(isEdit ? `${API_UD}${f_id.value}/` : API_CREATE, {
        method: isEdit ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': window.CSRF_TOKEN },
        body: JSON.stringify(
          isEdit ? {
            nivel: payload.nivel,
            prog_tipo: payload.prog_tipo,
            programa: payload.programa,
            mes_ing: payload.mes_ing, anio_ing: payload.anio_ing,
            mes_egr: payload.mes_egr, anio_egr: payload.anio_egr,
            ingreso_hombres: payload.ing_h, ingreso_mujeres: payload.ing_m,
            egresados_cohorte_h: payload.eg_coh_h, egresados_cohorte_m: payload.eg_coh_m,
            egresados_rezagados_h: payload.eg_rez_h, egresados_rezagados_m: payload.eg_rez_m,
            titulados_h: payload.tit_h, titulados_m: payload.tit_m,
            registrados_dgp_h: payload.dgp_h, registrados_dgp_m: payload.dgp_m,
          } : payload
        ),
      });
      const data = await res.json().catch(()=>({}));
      if (!res.ok || data.ok === false) {
        const msg = data.error || data.detail || `HTTP ${res.status}`;
        alert((isEdit ? 'No se pudo actualizar' : 'No se pudo guardar') + '\n' + msg);
        return;
      }
      closeModal();
      await cargar();
    } catch (err) {
      alert((isEdit ? 'No se pudo actualizar' : 'No se pudo guardar') + '\n' + (err.message || 'Error de red'));
    }
  });

  // --------- PDF
  btnPdf.addEventListener('click', async () => {
    const { jsPDF } = window.jspdf || {};
    if (!jsPDF || !window.jspdf || !window.jspdf.jsPDF) {
      alert('No se pudo cargar jsPDF');
      return;
    }
    const doc = new jsPDF('p', 'mm', 'a4');
    const title = 'Titulados – TSU / Ingeniería (Administrador)';
    doc.setFontSize(14);
    doc.text(title, 105, 14, { align: 'center' });

    // Filtros
    doc.setFontSize(10);
    const filtroTxt = [
      `Nivel: ${nivelActivo}`,
      `Programa: ${progTipo}`,
      `Carrera: ${filtroCarrera.options[filtroCarrera.selectedIndex]?.text || 'Todas'}`,
      `Año ingreso: ${anioIngreso.value || '-'}`,
      `Año egreso: ${anioEgreso.value || '-'}`
    ].join('  |  ');
    doc.text(filtroTxt, 14, 22);

    // Tabla (lee lo que está en el DOM)
    const head = [];
    document.querySelectorAll('#tabla thead th').forEach(th => head.push(th.innerText.trim()));
    const body = [];
    document.querySelectorAll('#tabla tbody tr').forEach(tr => {
      const row = [];
      tr.querySelectorAll('td').forEach((td, idx) => {
        // Excluye la col Acciones del PDF
        if (idx < head.length - 1) row.push(td.innerText.trim());
      });
      body.push(row);
    });

    // Elimina 'Acciones' del header
    head.pop();

    doc.autoTable({
      startY: 26,
      head: [head],
      body,
      styles: { fontSize: 8 },
      headStyles: { fillColor: [37, 99, 235] },
      theme: 'striped'
    });

    // Gráfica
    const canvas = document.getElementById('chart');
    const img = canvas.toDataURL('image/png', 1.0);
    let y = doc.lastAutoTable ? doc.lastAutoTable.finalY + 8 : 28;
    if (y > 190) { doc.addPage(); y = 20; }
    doc.setFontSize(12);
    doc.text('Tasa de Titulación por Nivel', 105, y, { align: 'center' });
    doc.addImage(img, 'PNG', 20, y + 4, 170, 70);

    doc.save('titulados_tsu_ing_admin.pdf');
  });

  // inicio
  (async () => {
    await fillFiltroCarrera();
    await cargar();
  })();

})();
