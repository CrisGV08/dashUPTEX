from django.shortcuts import render
from api.models import EvaluacionDocenteCuatrimestre
from collections import defaultdict

def evaluacion_docente_concentrado_view(request):
    # Obtener todos los registros de evaluación docente cuatrimestral
    evaluaciones = EvaluacionDocenteCuatrimestre.objects.select_related('ciclo_periodo')

    # Agrupar por año (ej: "2021" de "2021-1")
    promedios_por_anio = defaultdict(list)
    for registro in evaluaciones:
        ciclo = str(registro.ciclo_periodo)  # Ej: "2021-1"
        anio = ciclo.split('-')[0]           # Ej: "2021"
        promedios_por_anio[anio].append(registro.promedio_general)

    # Calcular promedio final por año
    promedios_agrupados = []
    for anio, promedios in promedios_por_anio.items():
        promedio_final = round(sum(promedios) / len(promedios), 2) if promedios else 0.0
        promedios_agrupados.append({
            'anio': anio,
            'promedio': promedio_final
        })

    # Ordenar por año
    promedios_agrupados.sort(key=lambda x: x['anio'])

    # Datos para JS
    datos_js = {
        'anios': [item['anio'] for item in promedios_agrupados],
        'promedios': [item['promedio'] for item in promedios_agrupados],
    }

    return render(request, 'evaluacion_docente_concentrado.html', {
        'datos': promedios_agrupados,
        'datos_js': datos_js,
        'anios_validos': datos_js['anios'],
    })
