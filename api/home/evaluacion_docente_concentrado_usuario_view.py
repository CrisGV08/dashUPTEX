from django.shortcuts import render
from api.models import EvaluacionDocenteCuatrimestre
from collections import defaultdict
import json

def evaluacion_docente_concentrado_usuario_view(request):
    # Año seleccionado (default 2025)
    anio_sel = request.GET.get('anio', '2025')

    # Traer registros con ciclo/periodo
    evaluaciones = EvaluacionDocenteCuatrimestre.objects.select_related(
        'ciclo_periodo__ciclo', 'ciclo_periodo__periodo'
    )

    # Años disponibles (para poblar el select en el front)
    anios_validos_set = set()
    for r in evaluaciones:
        anios_validos_set.add(str(r.ciclo_periodo.ciclo.anio))
    anios_validos_json = json.dumps(sorted(anios_validos_set))

    # Agrupar por año (FILTRADO por el año seleccionado)
    promedios_por_anio = defaultdict(list)
    for registro in evaluaciones:
        anio = str(registro.ciclo_periodo.ciclo.anio)
        if anio != str(anio_sel):
            continue
        if registro.promedio_general is not None:
            promedios_por_anio[anio].append(registro.promedio_general)

    # Calcular promedio final del año seleccionado
    promedios_agrupados = []
    for anio, promedios in promedios_por_anio.items():
        promedio_final = round(sum(promedios) / len(promedios), 2) if promedios else 0.0
        promedios_agrupados.append({'anio': anio, 'promedio': promedio_final})

    # Si no hay datos, devolvemos fila con 0.00 para ese año
    if not promedios_agrupados:
        promedios_agrupados.append({'anio': str(anio_sel), 'promedio': 0.0})

    # Promedio general total (sobre lo filtrado, aquí será 1 año)
    total_promedios = sum(item['promedio'] for item in promedios_agrupados)
    cantidad_anios = len(promedios_agrupados)
    promedio_general_total = round(total_promedios / cantidad_anios, 2) if cantidad_anios > 0 else 0.0

    # Datos para gráficas del front (solo el año seleccionado)
    datos_js = {
        'anios': [item['anio'] for item in promedios_agrupados],
        'promedios': [item['promedio'] for item in promedios_agrupados],
    }

    return render(request, 'evaluacion_docente_concentrado_usuario.html', {
        'datos': promedios_agrupados,
        'datos_js': datos_js,
        'promedio_general_total': promedio_general_total,
        # para el filtro en el front (como examen admisión)
        'anio_sel': str(anio_sel),
        'anios_validos_json': anios_validos_json,
    })
