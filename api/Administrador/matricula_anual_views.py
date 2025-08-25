from django.shortcuts import render
from collections import defaultdict
from api.models import NuevoIngreso, ProgramaEducativoAntiguo, ProgramaEducativoNuevo
import json

def matricula_por_anio_view(request):
    # Filtro desde GET
    tipo_programa = request.GET.get('tipo_programa', 'todos')

    registros = NuevoIngreso.objects.select_related(
        'ciclo_periodo', 'programa_antiguo', 'programa_nuevo'
    )

    datos_antiguos = defaultdict(lambda: {
        'Enero - Abril': 0,
        'Mayo - Agosto': 0,
        'Septiembre - Diciembre': 0
    })
    datos_nuevos = defaultdict(lambda: {
        'Enero - Abril': 0,
        'Mayo - Agosto': 0,
        'Septiembre - Diciembre': 0
    })
    anios_set = set()
    tabla_datos = []

    for reg in registros:
        ciclo = reg.ciclo_periodo
        anio = ciclo.ciclo.anio
        periodo = ciclo.periodo.nombre
        total = sum(filter(None, [
            reg.examen, reg.renoes, reg.uaem_gem, reg.pase_directo
        ]))
        anios_set.add(str(anio))

        if reg.programa_antiguo and tipo_programa in ['antiguo', 'todos']:
            nombre = reg.programa_antiguo.nombre
            key = f"{anio}-{nombre}"
            datos_antiguos[key][periodo] += total

        elif reg.programa_nuevo and tipo_programa in ['nuevo', 'todos']:
            nombre = reg.programa_nuevo.nombre
            key = f"{anio}-{nombre}"
            datos_nuevos[key][periodo] += total

    # Construcción de tabla
    for key, periodos in {**datos_antiguos, **datos_nuevos}.items():
        anio, programa = key.split('-', 1)
        sep_dic = periodos.get('Septiembre - Diciembre', 0)
        ene_abr = periodos.get('Enero - Abril', 0)
        may_ago = periodos.get('Mayo - Agosto', 0)
        total = sep_dic + ene_abr + may_ago

        tabla_datos.append({
            'anio': anio,
            'programa': programa,
            'sep_dic': sep_dic,
            'ene_abr': ene_abr,
            'may_ago': may_ago,
            'total': total
        })

    context = {
        'anios_lista': sorted(anios_set),
        'programas_antiguos_lista': json.dumps(
            list(ProgramaEducativoAntiguo.objects.values_list('nombre', flat=True))
        ),
        'programas_nuevos_lista': json.dumps(
            list(ProgramaEducativoNuevo.objects.values_list('nombre', flat=True))
        ),
        'data_antiguos_json': json.dumps(datos_antiguos),
        'data_nuevos_json': json.dumps(datos_nuevos),
        'tabla_datos': tabla_datos,
        'tipo_programa': tipo_programa,
    }

    return render(request, 'matricula_anual.html', context)
