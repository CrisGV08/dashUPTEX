from django.shortcuts import render, redirect
from api.models import EvaluacionDocenteCuatrimestre, CicloPeriodo
from django.contrib import messages
import json

def evaluacion_docente_cuatrimestre_view(request):
    periodos = CicloPeriodo.objects.all()

    # Guardar desde formulario de tabla
    if request.method == 'POST':
        if 'guardar_tabla' in request.POST:
            ciclo_ids = request.POST.getlist('ciclo_ids')
            promedios = request.POST.getlist('promedios')

            for ciclo_id, promedio in zip(ciclo_ids, promedios):
                if ciclo_id and promedio:
                    try:
                        ciclo = CicloPeriodo.objects.get(id=ciclo_id)
                        EvaluacionDocenteCuatrimestre.objects.update_or_create(
                            ciclo_periodo=ciclo,
                            defaults={'promedio_general': float(promedio)}
                        )
                    except Exception as e:
                        print(f"Error al guardar ciclo {ciclo_id}: {e}")

            messages.success(request, "✅ Cambios guardados correctamente.")
            return redirect('evaluacion_docente_cuatrimestre')

        else:
            # Guardar desde formulario superior
            ciclo_id = request.POST.get('ciclo_periodo')
            promedio = request.POST.get('promedio_general')

            if ciclo_id and promedio:
                try:
                    ciclo = CicloPeriodo.objects.get(id=ciclo_id)
                    EvaluacionDocenteCuatrimestre.objects.update_or_create(
                        ciclo_periodo=ciclo,
                        defaults={'promedio_general': float(promedio)}
                    )
                    messages.success(request, "✅ Promedio registrado correctamente.")
                except Exception as e:
                    messages.error(request, f"❌ Error al guardar: {e}")

            return redirect('evaluacion_docente_cuatrimestre')

    # Mostrar datos
    datos = EvaluacionDocenteCuatrimestre.objects.select_related('ciclo_periodo__ciclo').order_by('ciclo_periodo__ciclo__anio')

    etiquetas = [str(d.ciclo_periodo) for d in datos]
    promedios = [d.promedio_general for d in datos]

    context = {
        'periodos': periodos,
        'datos': datos,
        'etiquetas': json.dumps(etiquetas),
        'promedios': json.dumps(promedios),
    }
    return render(request, 'Evaluacion_docente_cuatrimestre.html', context)
