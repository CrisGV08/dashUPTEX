# api/Administrador/matricula_anual_views.py

from django.shortcuts import render
from collections import defaultdict
from api.models import NuevoIngreso, ProgramaEducativoAntiguo, ProgramaEducativoNuevo
import json

def matricula_por_anio_view(request):
    registros = NuevoIngreso.objects.select_related(
        'ciclo_periodo', 'programa_antiguo', 'programa_nuevo'
    )

    datos_antiguos = defaultdict(lambda: {'Enero - Abril': 0, 'Mayo - Agosto': 0, 'Septiembre - Diciembre': 0})
    datos_nuevos = defaultdict(lambda: {'Enero - Abril': 0, 'Mayo - Agosto': 0, 'Septiembre - Diciembre': 0})
    anios_set = set()

    for reg in registros:
        ciclo = reg.ciclo_periodo
        anio = ciclo.ciclo.anio
        periodo = ciclo.periodo.nombre
        total = sum(filter(None, [reg.examen, reg.renoes, reg.uaem_gem, reg.pase_directo]))

        if reg.programa_antiguo:
            key = f"{anio}-{reg.programa_antiguo.nombre}"
            datos_antiguos[key][periodo] += total
        elif reg.programa_nuevo:
            key = f"{anio}-{reg.programa_nuevo.nombre}"
            datos_nuevos[key][periodo] += total

        anios_set.add(str(anio))

    context = {
        'anios_lista': sorted(anios_set),
        'programas_antiguos_lista': sorted(ProgramaEducativoAntiguo.objects.values_list('nombre', flat=True)),
        'programas_nuevos_lista': sorted(ProgramaEducativoNuevo.objects.values_list('nombre', flat=True)),
        'data_antiguos_json': json.dumps(datos_antiguos),
        'data_nuevos_json': json.dumps(datos_nuevos),
    }

    return render(request, 'matricula_anual.html', context)
