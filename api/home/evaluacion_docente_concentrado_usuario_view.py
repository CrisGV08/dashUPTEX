from django.shortcuts import render
from api.models import EvaluacionDocenteCuatrimestre
from collections import defaultdict

def evaluacion_docente_concentrado_usuario_view(request):
    evaluaciones = EvaluacionDocenteCuatrimestre.objects.select_related('ciclo_periodo')

    # Agrupar por año (extraído del string de ciclo)
    promedios_por_anio = defaultdict(list)
    for registro in evaluaciones:
        ciclo = str(registro.ciclo_periodo)  # Ejemplo: "2022-1"
        anio = ciclo.split('-')[0]           # Resultado: "2022"
        promedios_por_anio[anio].append(registro.promedio_general)

    # Calcular promedios por año
    promedios_agrupados = []
    for anio, promedios in promedios_por_anio.items():
        promedio_final = round(sum(promedios) / len(promedios), 2) if promedios else 0.0
        promedios_agrupados.append({
            'anio': anio,
            'promedio': promedio_final
        })

    # Ordenar cronológicamente
    promedios_agrupados.sort(key=lambda x: x['anio'])

    # Preparar para JS
    datos_js = {
        'anios': [item['anio'] for item in promedios_agrupados],
        'promedios': [item['promedio'] for item in promedios_agrupados],
    }

    return render(request, 'evaluacion_docente_concentrado_usuario.html', {
        'datos': promedios_agrupados,
        'datos_js': datos_js,
        'anios_validos': datos_js['anios'],
    })
