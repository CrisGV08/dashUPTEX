from django.shortcuts import render
from api.models import EvaluacionDocenteCuatrimestre
from collections import defaultdict
import json

def evaluacion_docente_concentrado_view(request):
    # Año seleccionado (default 2025)
    anio_sel = request.GET.get('anio', '2025')

    # Traer evaluaciones con ciclo y periodo
    evaluaciones = EvaluacionDocenteCuatrimestre.objects.select_related(
        'ciclo_periodo__ciclo',
        'ciclo_periodo__periodo'
    )

    # Conjunto de años disponibles (para poblar en el front)
    anios_validos_set = set()
    for r in evaluaciones:
        anios_validos_set.add(str(r.ciclo_periodo.ciclo.anio))
    anios_validos = sorted(anios_validos_set)
    # JSON para incrustar en data-atributo
    anios_validos_json = json.dumps(anios_validos)

    # ---- AGRUPACIÓN filtrada por año seleccionado (como te dejé antes) ----
    promedios_por_anio = defaultdict(list)
    for registro in evaluaciones:
        anio = str(registro.ciclo_periodo.ciclo.anio)
        if anio != str(anio_sel):
            continue
        if registro.promedio_general is not None:
            promedios_por_anio[anio].append(registro.promedio_general)

    promedios_agrupados = []
    for anio, proms in promedios_por_anio.items():
        promedio_final = round(sum(proms) / len(proms), 2) if proms else 0.0
        promedios_agrupados.append({'anio': anio, 'promedio': promedio_final})

    if not promedios_agrupados:
        promedios_agrupados.append({'anio': str(anio_sel), 'promedio': 0.0})

    promedios_agrupados.sort(key=lambda x: x['anio'])

    total_promedios = sum(item['promedio'] for item in promedios_agrupados)
    cantidad_anios = len(promedios_agrupados)
    promedio_general_total = round(total_promedios / cantidad_anios, 2) if cantidad_anios > 0 else 0.0

    datos_js = {
        'anios': [item['anio'] for item in promedios_agrupados],
        'promedios': [item['promedio'] for item in promedios_agrupados],
    }

    return render(request, 'evaluacion_docente_concentrado.html', {
        'datos': promedios_agrupados,
        'datos_js': datos_js,
        'promedio_general_total': promedio_general_total,

        # Para el filtro de año "construido" desde la plantilla (como examen admisión)
        'anio_sel': str(anio_sel),
        'anios_validos_json': anios_validos_json,
    })
