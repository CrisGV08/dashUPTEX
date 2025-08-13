/* ========= Helpers ========= */
function parseJSON(id){
  try { return JSON.parse(document.getElementById(id).textContent); }
  catch { return []; }
}
function avg(arr){ return arr.length ? arr.reduce((a,b)=>a+b,0)/arr.length : 0; }

/* ========= Datos base del backend ========= */
const ALL = parseJSON('datosGraficas'); // [{ciclo, programa_id, programa, promedio}, ...]

/* ========= Lectura de UI ========= */
function getCiclo(){ return document.getElementById('filtroAnio')?.value || 'Todos'; }
function getProgramasSeleccionados(){
  const set = new Set();
  document.querySelectorAll('.programa-checkbox:checked').forEach(el => set.add(el.value));
  return set;
}
function getChartsWanted(){
  return {
    barras: document.getElementById('checkBarras')?.checked,
    linea:  document.getElementById('checkLinea')?.checked,
    pastel: document.getElementById('checkPastel')?.checked,
    gauss:  document.getElementById('checkGauss')?.checked,
  };
}

/* ========= Filtro ========= */
function filtrar(){
  const ciclo = document.getElementById('filtroAnio')?.value || 'Todos';
  const progs = new Set([...document.querySelectorAll('.programa-checkbox:checked')].map(el => el.value));

  return ALL.filter(r =>
    (ciclo === 'Todos' || r.ciclo === ciclo) &&
    (progs.size === 0 || progs.has(String(r.programa_id)))
  );
}


/* ========= Preparación datasets ========= */
function preparar(rows){
  if (!rows.length) return { labels: [], data: [] };

  if (getCiclo() === 'Todos'){
    const byCiclo = {};
    rows.forEach(r => (byCiclo[r.ciclo] = (byCiclo[r.ciclo]||[])).push(Number(r.promedio)));
    const labels = Object.keys(byCiclo);
    const data = labels.map(k => Number(avg(byCiclo[k]).toFixed(2)));
    return { labels, data };
  } else {
    const byProg = {};
    rows.forEach(r => (byProg[r.programa] = (byProg[r.programa]||[])).push(Number(r.promedio)));
    const labels = Object.keys(byProg);
    const data = labels.map(k => Number(avg(byProg[k]).toFixed(2)));
    return { labels, data };
  }
}

/* ========= Chart.js ========= */
let chBarras, chLinea, chPastel, chGauss;
function destroyAll(){ [chBarras, chLinea, chPastel, chGauss].forEach(c => c && c.destroy()); chBarras=chLinea=chPastel=chGauss=null; }
function toggleBoxes(){
  const g = getChartsWanted();
  document.getElementById('box-barras').style.display = g.barras ? '' : 'none';
  document.getElementById('box-linea').style.display  = g.linea  ? '' : 'none';
  document.getElementById('box-pastel').style.display = g.pastel ? '' : 'none';
  document.getElementById('box-gauss').style.display  = g.gauss  ? '' : 'none';
}

function dibujar(){
  const rows = filtrar();
  const {labels, data} = preparar(rows);

  destroyAll();
  toggleBoxes();

  const baseOpts = {
    responsive: true,
    plugins: { datalabels: { anchor: 'end', align: 'top', formatter: v => Number.isFinite(v) ? v.toFixed(2) : '' } },
    scales: { y: { beginAtZero: true, suggestedMax: 10 } }
  };

  if (getChartsWanted().barras){
    chBarras = new Chart(document.getElementById('graficaBarras').getContext('2d'), {
      type: 'bar', data: { labels, datasets: [{ label: 'Promedio', data }] }, options: baseOpts
    });
  }
  if (getChartsWanted().linea){
    chLinea = new Chart(document.getElementById('graficaLinea').getContext('2d'), {
      type: 'line', data: { labels, datasets: [{ label: 'Promedio', data, tension: .3, fill: false }] }, options: baseOpts
    });
  }
  if (getChartsWanted().pastel){
    const total = data.reduce((a,b)=>a+b,0) || 1;
    chPastel = new Chart(document.getElementById('graficaPastel').getContext('2d'), {
      type: 'pie',
      data: { labels, datasets: [{ data }] },
      options: { responsive: true, plugins: { datalabels: { formatter: v => ((v/total)*100).toFixed(1)+'%' } } }
    });
  }
  if (getChartsWanted().gauss){
    chGauss = new Chart(document.getElementById('graficaGauss').getContext('2d'), {
      type: 'line', data: { labels, datasets: [{ label: 'Promedio', data, tension: .45 }] }, options: baseOpts
    });
  }

  // tabla
  const tbody = document.querySelector('#tablaDetalle tbody');
  if (tbody){
    tbody.innerHTML = '';
    rows.forEach(r=>{
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${r.ciclo}</td><td>${r.programa}</td><td>${Number(r.promedio).toFixed(2)}</td>`;
      tbody.appendChild(tr);
    });
  }
}

/* ========= Listeners ========= */
document.addEventListener('DOMContentLoaded', () => {
  // Acciones de programas
  document.getElementById('select-all-prog')?.addEventListener('click', ()=>{
    document.querySelectorAll('.programa-checkbox').forEach(c => c.checked = true);
  });
  document.getElementById('clear-all-prog')?.addEventListener('click', ()=>{
    document.querySelectorAll('.programa-checkbox').forEach(c => c.checked = false);
  });

  // Botones aplicar/reset
  document.getElementById('aplicarFiltros')?.addEventListener('click', dibujar);
  document.getElementById('resetFiltros')?.addEventListener('click', ()=>{
    const sel = document.getElementById('filtroAnio'); if (sel) sel.value = 'Todos';
    ['checkBarras','checkLinea','checkPastel','checkGauss'].forEach(id=>{
      const el = document.getElementById(id); if (el) el.checked = true;
    });
    document.querySelectorAll('.programa-checkbox').forEach(c => c.checked = true);
    dibujar();
  });

  // Primera carga
  dibujar();
});
