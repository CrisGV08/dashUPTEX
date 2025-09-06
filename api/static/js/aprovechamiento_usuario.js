/* ========= Helpers ========= */
function parseJSON(id){
  try { return JSON.parse(document.getElementById(id)?.textContent || '[]'); }
  catch { return []; }
}
function avg(arr){ return arr.length ? arr.reduce((a,b)=>a+b,0)/arr.length : 0; }
const norm = s => String(s ?? '').replace(/\s+/g,' ').trim();
const $ = sel => document.querySelector(sel);

/* ========= Paleta y utilidades de color ========= */
/* Paleta agradable (Tailwind-ish) */
const PALETTE = [
  '#2563eb', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
  '#14b8a6', '#e11d48', '#f97316', '#22c55e', '#06b6d4',
  '#a855f7', '#84cc16', '#0ea5e9', '#d946ef', '#64748b'
];
function hashCode(str){
  let h = 0; for (let i = 0; i < str.length; i++) { h = ((h << 5) - h) + str.charCodeAt(i); h |= 0; }
  return Math.abs(h);
}
function colorForLabel(label){
  const idx = hashCode(String(label)) % PALETTE.length;
  return PALETTE[idx];
}
function withAlpha(hex, a){
  const r = parseInt(hex.slice(1,3),16), g = parseInt(hex.slice(3,5),16), b = parseInt(hex.slice(5,7),16);
  return `rgba(${r}, ${g}, ${b}, ${a})`;
}

/* ========= Datos base ========= */
const ALL = parseJSON('datosGraficas') || [];
console.log('[Aprovechamiento Usuario] Recibidos:', ALL.length);

/* ========= Lectura de UI ========= */
function getCiclo(){ return $('#filtroAnio')?.value || 'Todos'; }
function getProgramasSeleccionados(){
  const set = new Set();
  document.querySelectorAll('.programa-checkbox:checked').forEach(el => set.add(el.value));
  return set;
}
function getChartsWanted(){
  return {
    barras: $('#checkBarras')?.checked,
    linea:  $('#checkLinea')?.checked,
    pastel: $('#checkPastel')?.checked,
    gauss:  $('#checkGauss')?.checked,
  };
}

/* ========= Filtro ========= */
function filtrar(){
  const ciclo = getCiclo();
  const progs = getProgramasSeleccionados();

  const rows = ALL.filter(r =>
    (ciclo === 'Todos' || norm(r.ciclo) === norm(ciclo)) &&
    (progs.size === 0 || progs.has(String(r.programa_id)))
  );

  const badge = $('#badgeFiltrados'); if (badge) badge.textContent = `Filtrados: ${rows.length}`;
  const msg = $('#msgSinDatos'); if (msg) msg.style.display = rows.length ? 'none' : '';
  return rows;
}

/* ========= Preparación datasets (ignora promedios no numéricos SOLO para gráficas) ========= */
function toNum(x){ const n = Number(x); return Number.isFinite(n) ? n : null; }

function preparar(rows){
  if (!rows.length) return { labels: [], data: [] };

  if (getCiclo() === 'Todos'){
    const byCiclo = {};
    rows.forEach(r => {
      const n = toNum(r.promedio);
      if (n !== null){
        (byCiclo[r.ciclo] = byCiclo[r.ciclo] || []).push(n);
      }
    });
    const labels = Object.keys(byCiclo);
    const data = labels.map(k => Number(avg(byCiclo[k]).toFixed(2)));
    return { labels, data };
  } else {
    const byProg = {};
    rows.forEach(r => {
      const n = toNum(r.promedio);
      if (n !== null){
        (byProg[r.programa] = byProg[r.programa] || []).push(n);
      }
    });
    const labels = Object.keys(byProg);
    const data = labels.map(k => Number(avg(byProg[k]).toFixed(2)));
    return { labels, data };
  }
}

/* ========= Chart.js ========= */
let chBarras, chLinea, chPastel, chGauss;
if (window.Chart && window.ChartDataLabels) Chart.register(ChartDataLabels);

function destroyAll(){ [chBarras, chLinea, chPastel, chGauss].forEach(c => c && c.destroy()); chBarras=chLinea=chPastel=chGauss=null; }
function toggleBoxes(){
  const g = getChartsWanted();
  $('#box-barras').style.display = g.barras ? '' : 'none';
  $('#box-linea').style.display  = g.linea  ? '' : 'none';
  $('#box-pastel').style.display = g.pastel ? '' : 'none';
  $('#box-gauss').style.display  = g.gauss  ? '' : 'none';
}

function dibujar(){
  const rows = filtrar();
  const {labels, data} = preparar(rows);

  destroyAll();
  toggleBoxes();

  // Colores consistentes por etiqueta
  const baseColors = labels.map(l => colorForLabel(l));
  const bgLight = baseColors.map(c => withAlpha(c, 0.25));
  const bgPie   = baseColors.map(c => withAlpha(c, 0.85));
  const borders = baseColors;

  const baseOpts = {
    responsive: true,
    plugins: {
      legend: { display: true },
      datalabels: {
        anchor: 'end', align: 'top',
        formatter: v => Number.isFinite(v) ? v.toFixed(2) : ''
      }
    },
    scales: { y: { beginAtZero: true, suggestedMax: 10 } }
  };

  if (getChartsWanted().barras && $('#graficaBarras')){
    chBarras = new Chart($('#graficaBarras').getContext('2d'), {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'Promedio',
          data,
          backgroundColor: bgLight,
          borderColor: borders,
          borderWidth: 2,
          hoverBackgroundColor: baseColors.map(c => withAlpha(c, 0.35))
        }]
      },
      options: baseOpts
    });
  }

  if (getChartsWanted().linea && $('#graficaLinea')){
    chLinea = new Chart($('#graficaLinea').getContext('2d'), {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: 'Promedio',
          data,
          tension: .35,
          fill: false,
          borderColor: borders,                // color por punto/segmento
          pointBackgroundColor: baseColors,    // color por punto
          pointBorderColor: '#ffffff',
          pointBorderWidth: 1.5
        }]
      },
      options: baseOpts
    });
  }

  if (getChartsWanted().pastel && $('#graficaPastel')){
    const total = data.reduce((a,b)=>a+b,0) || 1;
    chPastel = new Chart($('#graficaPastel').getContext('2d'), {
      type: 'pie',
      data: {
        labels,
        datasets: [{
          data,
          backgroundColor: bgPie,
          borderColor: '#ffffff',
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: true },
          datalabels: { formatter: v => ((v/total)*100).toFixed(1)+'%' }
        }
      }
    });
  }

  if (getChartsWanted().gauss && $('#graficaGauss')){
    chGauss = new Chart($('#graficaGauss').getContext('2d'), {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: 'Promedio',
          data,
          tension: .45,
          fill: false,
          borderColor: borders,
          pointBackgroundColor: baseColors,
          pointBorderColor: '#ffffff',
          pointBorderWidth: 1.5
        }]
      },
      options: baseOpts
    });
  }

  // === Tabla (siempre muestra lo filtrado; si promedio es null, muestra "—") ===
  const tbody = document.querySelector('#tablaDetalle tbody');
  if (tbody){
    tbody.innerHTML = '';
    rows.forEach(r=>{
      const n = toNum(r.promedio);
      const celda = (n === null) ? '—' : n.toFixed(2);
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${r.ciclo}</td><td>${r.programa}</td><td>${celda}</td>`;
      tbody.appendChild(tr);
    });
    if (!rows.length){
      const tr = document.createElement('tr');
      tr.innerHTML = `<td colspan="3" class="text-muted">Sin registros</td>`;
      tbody.appendChild(tr);
    }
  }
}

/* ========= Listeners ========= */
document.addEventListener('DOMContentLoaded', () => {
  // Acciones masivas
  document.getElementById('select-all-prog')?.addEventListener('click', ()=>{ document.querySelectorAll('.programa-checkbox').forEach(c => c.checked = true); dibujar(); });
  document.getElementById('clear-all-prog')?.addEventListener('click', ()=>{ document.querySelectorAll('.programa-checkbox').forEach(c => c.checked = false); dibujar(); });

  // Botones y cambios inmediatos
  document.getElementById('aplicarFiltros')?.addEventListener('click', dibujar);
  document.getElementById('resetFiltros')?.addEventListener('click', ()=>{
    const sel = document.getElementById('filtroAnio'); if (sel) sel.value = 'Todos';
    ['checkBarras','checkLinea','checkPastel','checkGauss'].forEach(id=>{ const el = document.getElementById(id); if (el) el.checked = true; });
    document.querySelectorAll('.programa-checkbox').forEach(c => c.checked = true);
    dibujar();
  });

  document.getElementById('filtroAnio')?.addEventListener('change', dibujar);
  document.querySelectorAll('.programa-checkbox').forEach(el => el.addEventListener('change', dibujar));
  document.querySelectorAll('.grafica-check').forEach(el => el.addEventListener('change', dibujar));

  // Primera carga
  dibujar();
});
