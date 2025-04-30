# api/home/matricula_anual_usuario_view.py

from django.shortcuts import render
from collections import defaultdict
from api.models import NuevoIngreso, ProgramaEducativoAntiguo, ProgramaEducativoNuevo
import json

def matricula_anual_usuario_view(request):
    registros = NuevoIngreso.objects.select_related('ciclo_periodo', 'programa_antiguo', 'programa_nuevo')

    datos_antiguos = defaultdict(lambda: {'Enero - Abril': 0, 'Mayo - Agosto': 0, 'Septiembre - Diciembre': 0})
    datos_nuevos = defaultdict(lambda: {'Enero - Abril': 0, 'Mayo - Agosto': 0, 'Septiembre - Diciembre': 0})

    anios_set = set()

    for reg in registros:
        anio = reg.ciclo_periodo.ciclo.anio
        periodo = reg.ciclo_periodo.periodo.nombre
        total = (reg.examen or 0) + (reg.renoes or 0) + (reg.uaem_gem or 0) + (reg.pase_directo or 0)

        if reg.programa_antiguo:
            programa = reg.programa_antiguo.nombre
            key = f"{anio}-{programa}"
            datos_antiguos[key][periodo] += total
        elif reg.programa_nuevo:
            programa = reg.programa_nuevo.nombre
            key = f"{anio}-{programa}"
            datos_nuevos[key][periodo] += total

        anios_set.add(str(anio))

    programas_antiguos = list(ProgramaEducativoAntiguo.objects.values_list('nombre', flat=True))
    programas_nuevos = list(ProgramaEducativoNuevo.objects.values_list('nombre', flat=True))

    context = {
        'anios_lista': sorted(anios_set),
        'programas_antiguos_lista': sorted(programas_antiguos),
        'programas_nuevos_lista': sorted(programas_nuevos),
        'data_antiguos_json': json.dumps(datos_antiguos),
        'data_nuevos_json': json.dumps(datos_nuevos),
    }
    return render(request, 'matricula_anual_usuario.html', context)
