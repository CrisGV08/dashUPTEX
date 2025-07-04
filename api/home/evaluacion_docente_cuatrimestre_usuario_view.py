from django.shortcuts import render
from api.models import EvaluacionDocenteCuatrimestre, CicloPeriodo

def evaluacion_docente_cuatrimestre_usuario_view(request):
    # Obtener todos los ciclos disponibles
    periodos = CicloPeriodo.objects.all().order_by('id')

    # Obtener todos los datos de evaluación
    datos = EvaluacionDocenteCuatrimestre.objects.select_related('ciclo_periodo').order_by('ciclo_periodo__id')

    # Preparar etiquetas (nombres de ciclos) y promedios
    etiquetas = [str(item.ciclo_periodo) for item in datos]
    promedios = [float(item.promedio_general) for item in datos]

    context = {
        'periodos': periodos,
        'datos': datos,
        'etiquetas': etiquetas,
        'promedios': promedios,
    }

    return render(request, 'Evaluacion_docente_cuatrimestre_usuario.html', context)
