from django.shortcuts import render
from api.models import GeneracionCarrera

import json

def titulados_historicos_actual_usuario_view(request):
    generaciones = GeneracionCarrera.objects.select_related(
        'programa_antiguo', 'programa_nuevo'
    ).order_by('fecha_ingreso')

    generaciones_json = json.dumps([
        {
            "nombre_programa": g.programa_antiguo.nombre if g.programa_antiguo else g.programa_nuevo.nombre,
            "anio": g.fecha_ingreso.year,
            "tasa_titulacion": g.tasa_titulacion
        }
        for g in generaciones
    ])

    return render(request, "titulados_historicos_actual_usuario.html", {
        "generaciones": generaciones,
        "generaciones_json": generaciones_json
    })
