from django.shortcuts import render, redirect
from django.contrib import messages
from api.models import EvaluacionDocenteCuatrimestre, CicloPeriodo
import json

def evaluacion_docente_cuatrimestre_view(request):
    # Obtener todos los ciclos y años disponibles
    periodos_all = CicloPeriodo.objects.select_related('ciclo', 'periodo').all()
    anios_disponibles = sorted(set(p.ciclo.anio for p in periodos_all))

    # Obtener año seleccionado desde GET
    anio_seleccionado = request.GET.get("anio")

    if anio_seleccionado:
        periodos = CicloPeriodo.objects.select_related('ciclo', 'periodo') \
                    .filter(ciclo__anio=anio_seleccionado).order_by('id')[:3]
    else:
        periodos = periodos_all.order_by('id')

    # Guardar datos si se mandan por POST
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

    # Construir los datos para tabla y gráficas
    datos = []
    for ciclo in periodos:
        evaluacion = EvaluacionDocenteCuatrimestre.objects.filter(ciclo_periodo=ciclo).first()
        datos.append({
            'ciclo_periodo': ciclo,
            'promedio_general': evaluacion.promedio_general if evaluacion else ''
        })

    etiquetas = [str(d['ciclo_periodo']) for d in datos]
    promedios = [d['promedio_general'] or 0 for d in datos]

    context = {
        'periodos': periodos_all,
        'anios': anios_disponibles,
        'anio_seleccionado': anio_seleccionado,
        'datos': datos,
        'etiquetas': json.dumps(etiquetas),
        'promedios': json.dumps(promedios),
    }

    return render(request, 'Evaluacion_docente_cuatrimestre.html', context)
