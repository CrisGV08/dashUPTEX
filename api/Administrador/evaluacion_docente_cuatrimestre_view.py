from django.shortcuts import render, redirect
from api.models import EvaluacionDocenteCuatrimestre, CicloPeriodo
from django.contrib import messages
import json

def evaluacion_docente_cuatrimestre_view(request):
    periodos = CicloPeriodo.objects.all()
    datos = EvaluacionDocenteCuatrimestre.objects.select_related('ciclo_periodo__ciclo').order_by('ciclo_periodo__ciclo__anio')

    if request.method == 'POST':
        ciclo_id = request.POST.get('ciclo_periodo')
        promedio = request.POST.get('promedio_general')

        if ciclo_id and promedio:
            ciclo = CicloPeriodo.objects.get(id=ciclo_id)
            EvaluacionDocenteCuatrimestre.objects.update_or_create(
                ciclo_periodo=ciclo,
                defaults={'promedio_general': float(promedio)}
            )
            messages.success(request, "✅ Promedio registrado correctamente.")
            return redirect('evaluacion_docente_cuatrimestre')

    etiquetas = [str(d.ciclo_periodo) for d in datos]
    promedios = [d.promedio_general for d in datos]

    context = {
        'periodos': periodos,
        'datos': datos,
        'etiquetas': json.dumps(etiquetas),
        'promedios': json.dumps(promedios)
    }
    return render(request, 'Evaluacion_docente_cuatrimestre.html', context)



