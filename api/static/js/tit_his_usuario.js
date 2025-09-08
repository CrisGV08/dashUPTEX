/* global window, document, Choices, Chart, html2canvas, jspdf, ChartDataLabels */
(() => {
  'use strict';

  // Helpers
  const $  = (s, c=document)=>c.querySelector(s);
  const $$ = (s, c=document)=>Array.from(c.querySelectorAll(s));

  // Datos globales (catálogos)
  const ANTIGUAS = window.CARRERAS_ANTIGUAS || [];
  const NUEVAS   = window.CARRERAS_NUEVAS   || [];

  // Nodos
  const root      = $('#titHisRoot');
  const tableWrap = $('#tableWrap');
  const grid      = $('#grid');
  const chartEl   = $('#chartMain');

  // Estado
  let currentType = 'line';

  // ==== Utilidades ====
  const fmt = (v)=> (isFinite(v) ? Number(v) : 0);
  const tasaPct = (th,tm,ih,im)=>{
    const tit = fmt(th)+fmt(tm);
    const ing = fmt(ih)+fmt(im);
    return ing>0 ? (tit/ing)*100 : 0;
  };
  const tipoDePrograma = (id) => {
    const sid = String(id);
    if (ANTIGUAS.some(x=>String(x.id)===sid)) return 'antiguo';
    if (NUEVAS.some(x=>String(x.id)===sid))   return 'nuevo';
    return 'antiguo';
  };

  // ==== Cargar selects por fila + tasa ====
  function fillProgramaSelect(row){
    const sel = $('.programa', row);
    if (!sel) return;

    sel.innerHTML = '';
    sel.disabled = true;

    const ogA = document.createElement('optgroup'); ogA.label = 'Antiguo';
    ANTIGUAS.forEach(x=>{
      const o = document.createElement('option');
      o.value = x.id; o.textContent = `${x.id} — ${x.nombre}`;
      ogA.appendChild(o);
    });
    const ogN = document.createElement('optgroup'); ogN.label = 'Nuevo';
    NUEVAS.forEach(x=>{
      const o = document.createElement('option');
      o.value = x.id; o.textContent = `${x.id} — ${x.nombre}`;
      ogN.appendChild(o);
    });

    sel.appendChild(ogA); sel.appendChild(ogN);

    const init = $('.programa-init', row);
    if (init && init.dataset.id) sel.value = init.dataset.id;
    if (!sel.value && sel.options.length) sel.value = sel.options[0].value;
  }

  function updateRowTasa(row){
    const th = $('.th', row)?.value ?? 0;
    const tm = $('.tm', row)?.value ?? 0;
    const ih = $('.ih', row)?.value ?? 0;
    const im = $('.im', row)?.value ?? 0;
    const cell = $('.tasa', row);
    if (cell) cell.textContent = tasaPct(th,tm,ih,im).toFixed(2);
  }

  $$('#grid tbody tr').forEach(r=>{
    if (!r.classList.contains('empty')) { fillProgramaSelect(r); updateRowTasa(r); }
  });

  // ==== Filtros ====
  const chAnt = new Choices('#filAntiguo', { removeItemButton:true, shouldSort:true });
  const chNue = new Choices('#filNuevo',   { removeItemButton:true, shouldSort:true });
  chAnt.setChoices(ANTIGUAS.map(x=>({value:x.id,label:`${x.id} — ${x.nombre}`})), 'value','label', true);
  chNue.setChoices(NUEVAS.map(x=>({value:x.id,label:`${x.id} — ${x.nombre}`})), 'value','label', true);

  const yearPillsEl = $('#yearPills');
  const selectedYears = new Set();

  function collectYears(){
    const years = new Set();
    $$('#grid tbody tr').forEach(r=>{
      if (r.classList.contains('empty')) return;
      const v = $('.fi', r)?.value || '';
      if (/^\d{4}-\d{2}$/.test(v)) years.add(v.slice(0,4));
    });
    if (!years.size && Array.isArray(window.GENERACIONES)) {
      window.GENERACIONES.forEach(x=>{
        const y = x.anio || x.year || x.anio_ingreso;
        if (y) years.add(String(y));
      });
    }
    return Array.from(years).sort();
  }

  function buildYearPills(){
    const years = collectYears();
    yearPillsEl.innerHTML = '';
    selectedYears.clear();
    years.forEach(y=>{
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'pill active';
      b.dataset.year = y;
      b.textContent = y;
      yearPillsEl.appendChild(b);
      selectedYears.add(y);
    });
  }
  buildYearPills();

  yearPillsEl.addEventListener('click', (ev)=>{
    const btn = ev.target.closest('.pill');
    if (!btn) return;
    const y = btn.dataset.year;
    btn.classList.toggle('active');
    if (btn.classList.contains('active')) selectedYears.add(y);
    else selectedYears.delete(y);
    applyFilters();
  });

  const choicesValues = (inst)=>
    inst && inst._currentState ? inst._currentState.choices.filter(c=>!c.disabled && c.value).map(c=>String(c.value)) : [];

  $('#yearsAll')?.addEventListener('click', ()=>{
    yearPillsEl.querySelectorAll('.pill').forEach(p=>p.classList.add('active'));
    selectedYears.clear(); collectYears().forEach(y=>selectedYears.add(y));
    applyFilters();
  });
  $('#yearsNone')?.addEventListener('click', ()=>{
    yearPillsEl.querySelectorAll('.pill').forEach(p=>p.classList.remove('active'));
    selectedYears.clear();
    applyFilters();
  });
  $('#antAll')?.addEventListener('click', ()=>{
    const vals = choicesValues(chAnt);
    chAnt.removeActiveItems(); vals.forEach(v=>chAnt.setChoiceByValue(v));
    $('#filAntiguo').dispatchEvent(new Event('change'));
  });
  $('#antNone')?.addEventListener('click', ()=>{
    chAnt.removeActiveItems();
    $('#filAntiguo').dispatchEvent(new Event('change'));
  });
  $('#nueAll')?.addEventListener('click', ()=>{
    const vals = choicesValues(chNue);
    chNue.removeActiveItems(); vals.forEach(v=>chNue.setChoiceByValue(v));
    $('#filNuevo').dispatchEvent(new Event('change'));
  });
  $('#nueNone')?.addEventListener('click', ()=>{
    chNue.removeActiveItems();
    $('#filNuevo').dispatchEvent(new Event('change'));
  });

  const getSelAnt = () => (chAnt.getValue(true) || []).map(v => String(v));
  const getSelNue = () => (chNue.getValue(true) || []).map(v => String(v));

  function rowMatchesFilters(row){
    if (row.classList.contains('empty')) return false;

    // Año
    if (selectedYears.size){
      const v = $('.fi', row)?.value || '';
      const y = (/^\d{4}-\d{2}$/.test(v)) ? v.slice(0,4) : '';
      if (y && !selectedYears.has(y)) return false;
    }

    // Programa (tolerante a tipo)
    const progId = String($('.programa', row)?.value || '');
    const tipo   = tipoDePrograma(progId);
    const selA   = getSelAnt();
    const selN   = getSelNue();

    if (tipo==='antiguo' && selA.length && !selA.includes(progId)) return false;
    if (tipo==='nuevo'   && selN.length && !selN.includes(progId)) return false;

    return true;
  }

  function applyFilters(){
    let visibles = 0;
    $$('#grid tbody tr').forEach(row=>{
      if (row.classList.contains('empty')) return;
      const ok = rowMatchesFilters(row);
      row.style.display = ok ? '' : 'none';
      if (ok){ visibles++; updateRowTasa(row); }
    });
    const empty = $('#grid tbody tr.empty');
    if (empty) empty.style.display = visibles ? 'none' : '';
    syncChart();
  }

  $('#filAntiguo').addEventListener('change', applyFilters);
  $('#filNuevo').addEventListener('change', applyFilters);

  // ==== Gráfica ====
  if (window.ChartDataLabels) Chart.register(ChartDataLabels);
  const ctx = chartEl.getContext('2d');
  let chart = null;

  function visibleRowsData(){
    const rows = $$('#grid tbody tr').filter(r=> r.style.display!=='none' && !r.classList.contains('empty'));
    const labels=[], ingreso=[], egresados=[], tasa=[];
    rows.forEach(r=>{
      const code = ($('.programa', r)?.value || '').toString();
      const ym   = $('.fi', r)?.value || '';
      const mes  = ym.includes('-') ? ym.split('-')[1] : '';
      labels.push([code, mes]);

      const ih = fmt($('.ih', r)?.value), im = fmt($('.im', r)?.value);
      const ch = fmt($('.ch', r)?.value), cm = fmt($('.cm', r)?.value);
      const rh = fmt($('.rh', r)?.value), rm = fmt($('.rm', r)?.value);
      const th = fmt($('.th', r)?.value), tm = fmt($('.tm', r)?.value);

      const ingTot = ih + im;
      const egrTot = ch + cm + rh + rm;
      const rate   = ingTot > 0 ? ((th + tm) / ingTot) * 100 : 0;

      ingreso.push(ingTot);
      egresados.push(egrTot);
      tasa.push(Number(rate.toFixed(1)));
    });
    return { labels, ingreso, egresados, tasa };
  }

  function gaussianPoints(series){
    const vals = series.filter(v=>isFinite(v));
    if (!vals.length) return { x:[], y:[] };
    const mean = vals.reduce((a,b)=>a+b,0)/vals.length;
    const variance = vals.reduce((a,b)=>a+(b-mean)*(b-mean),0)/vals.length;
    let sigma = Math.sqrt(variance);
    if (!isFinite(sigma) || sigma === 0) sigma = 1e-3;
    const xMin = 0, xMax = 100, N = 80;
    const x = Array.from({length:N}, (_,i)=> xMin + (i*(xMax-xMin)/(N-1)));
    const y = x.map(xi => Math.exp(-0.5 * Math.pow((xi-mean)/sigma, 2)));
    const maxY = Math.max(...y) || 1;
    const yScaled = y.map(v=> v/maxY*100);
    return { x, y: yScaled };
  }

  function renderChart(){
    const { labels, ingreso, egresados, tasa } = visibleRowsData();
    if (chart) chart.destroy();

    if (currentType === 'pie') {
      chart = new Chart(ctx, {
        type: 'pie',
        data: { labels, datasets: [{ label: 'TASA DE TITULACIÓN', data: tasa }] },
        options: {
          responsive:true, maintainAspectRatio:false,
          plugins: { legend: { position:'top' },
            datalabels: { formatter: (v)=> `${v}%`, color:'#111827',
              backgroundColor:'rgba(255,255,255,.6)', borderRadius:2, padding:2, font:{ size:9 } } }
        }
      });
      return;
    }

    if (currentType === 'gauss') {
      const g = gaussianPoints(tasa);
      chart = new Chart(ctx, {
        type: 'line',
        data: { labels: g.x.map(v=>v.toFixed(0)), datasets: [{
          label:'Gauss (Tasa %)', data: g.y,
          borderColor:'#2563eb', backgroundColor:'rgba(37,99,235,.15)',
          borderWidth:2, tension:0.35, pointRadius:0
        }]},
        options: {
          responsive:true, maintainAspectRatio:false,
          scales:{ y:{ beginAtZero:true, max:100 }, x:{ ticks:{ autoSkip:true, maxRotation:0, font:{ size:9 } } } },
          plugins:{ legend:{ position:'top' } }
        }
      });
      return;
    }

    const isBar = (currentType === 'bar');
    chart = new Chart(ctx, {
      type: isBar ? 'bar' : 'line',
      data: {
        labels,
        datasets: [
          { label: 'TASA DE TITULACIÓN', data: tasa, yAxisID: 'yRate',
            type: isBar ? 'bar' : 'line',
            borderColor:'#2563eb',
            backgroundColor: isBar ? 'rgba(37,99,235,.35)' : 'rgba(37,99,235,.15)',
            borderWidth:2, tension:0.35, pointRadius: isBar ? 0 : 2 },
          { label: 'EGRESADOS', data: egresados, yAxisID: 'yCounts',
            type: isBar ? 'bar' : 'line',
            borderColor:'#ef4444',
            backgroundColor: isBar ? 'rgba(239,68,68,.35)' : 'rgba(239,68,68,.15)',
            borderWidth:2, tension:0.35, pointRadius: isBar ? 0 : 2 },
          { label: 'INGRESO', data: ingreso, yAxisID: 'yCounts',
            type: isBar ? 'bar' : 'line',
            borderColor:'#22c55e',
            backgroundColor: isBar ? 'rgba(34,197,94,.35)' : 'rgba(34,197,94,.15)',
            borderWidth:2, tension:0.35, pointRadius: isBar ? 0 : 2 }
        ]
      },
      options: {
        responsive:true, maintainAspectRatio:false,
        interaction:{ mode:'index', intersect:false },
        plugins:{ legend:{ position:'top', labels:{ boxWidth:18 } } },
        scales:{
          yCounts:{ type:'linear', position:'left', beginAtZero:true, grace:'5%' },
          yRate:{ type:'linear', position:'right', min:0, max:100, grid:{ drawOnChartArea:false },
                  ticks:{ callback:(v)=>`${v}%` } },
          x:{ ticks:{ autoSkip:false, maxRotation:0, font:{ size:9 } } }
        }
      }
    });
  }
  function syncChart(){ renderChart(); }

  $('#graphPills')?.addEventListener('click', (ev)=>{
    const btn = ev.target.closest('.pill');
    if (!btn) return;
    $$('.pill', $('#graphPills')).forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    currentType = btn.dataset.type || 'line';
    syncChart();
  });

  // Inicial
  applyFilters();
  setTimeout(syncChart, 0);

  // ==== PDF (sin recortes horizontales) ====
  async function downloadPDF(){
    const { jsPDF } = window.jspdf || {};
    if (!jsPDF) { alert('No se encontró jsPDF.'); return; }

    root.classList.add('pdf-mode');

    // Guardar estilos para restaurar
    const prevWrapWidth  = tableWrap.style.width;
    const prevGridWidth  = grid.style.width;
    const prevOverflow   = tableWrap.style.overflow;

    // Expandir a ancho completo del contenido
    const fullWidthPx = Math.max(grid.scrollWidth, tableWrap.scrollWidth);
    tableWrap.style.overflow = 'visible';
    tableWrap.style.width    = fullWidthPx + 'px';
    grid.style.width         = 'max-content';
    tableWrap.classList.add('fit-content-width');

    await new Promise(r => setTimeout(r, 200));

    const doc    = new jsPDF('l', 'mm', 'letter');
    const pageW  = doc.internal.pageSize.getWidth();
    const pageH  = doc.internal.pageSize.getHeight();
    const margin = 10;
    const contentW = pageW - margin*2;
    const usableH  = pageH - margin*2;

    // 1) Gráfica
    let cursorY = margin;
    try{
      const ratio   = chartEl.height / chartEl.width || 0.5;
      const chartH  = Math.min(usableH * 0.40, contentW * ratio);
      const chartImg = chartEl.toDataURL('image/png', 1.0);
      doc.addImage(chartImg, 'PNG', margin, cursorY, contentW, chartH);
      cursorY += chartH + 6;
    }catch(e){ console.warn('No se pudo pintar la gráfica en el PDF:', e); }

    // 2) Tabla (captura completa)
    const tableCanvas = await html2canvas(tableWrap, {
      scale: 2, useCORS: true, backgroundColor: '#ffffff',
      windowWidth: tableWrap.scrollWidth, windowHeight: tableWrap.scrollHeight
    });
    const pxPerMm  = tableCanvas.width / contentW;
    const tableMmH = tableCanvas.height / pxPerMm;

    const availMm = (pageH - margin) - cursorY;

    const addSlices = (canvas, startPx, slicePx, putOnThisPage=true)=>{
      let y = startPx;
      if (putOnThisPage && slicePx > 0){
        const c = document.createElement('canvas');
        c.width = canvas.width; c.height = slicePx;
        c.getContext('2d').drawImage(canvas, 0, y, canvas.width, slicePx, 0, 0, c.width, slicePx);
        doc.addImage(c.toDataURL('image/png',1.0), 'PNG', margin, cursorY, contentW, slicePx/pxPerMm);
        y += slicePx;
      }
      const middlePx = Math.floor(usableH * pxPerMm);
      while (y < canvas.height){
        const h = Math.min(middlePx || (canvas.height - y), canvas.height - y);
        const c = document.createElement('canvas');
        c.width = canvas.width; c.height = h;
        c.getContext('2d').drawImage(canvas, 0, y, canvas.width, h, 0, 0, c.width, h);
        doc.addPage();
        doc.addImage(c.toDataURL('image/png',1.0), 'PNG', margin, margin, contentW, h/pxPerMm);
        y += h;
      }
    };

    if (tableMmH > availMm + 0.5) {
      const firstSlicePx = Math.floor(availMm * pxPerMm);
      addSlices(tableCanvas, 0, firstSlicePx, true);
    } else {
      doc.addImage(tableCanvas.toDataURL('image/png',1.0), 'PNG', margin, cursorY, contentW, tableMmH);
    }

    doc.save('titulados_reporte.pdf');

    // Restaurar estilos
    tableWrap.classList.remove('fit-content-width');
    grid.style.width        = prevGridWidth;
    tableWrap.style.width   = prevWrapWidth;
    tableWrap.style.overflow= prevOverflow;
    root.classList.remove('pdf-mode');
  }

  $('#btnPdf')?.addEventListener('click', downloadPDF);
})();
