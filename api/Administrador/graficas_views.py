from django.shortcuts import render
from api.models import NuevoIngreso, CicloPeriodo, ProgramaEducativoAntiguo, ProgramaEducativoNuevo
from collections import defaultdict
import json

def graficas_examen_view(request):
    ciclos = CicloPeriodo.objects.select_related('ciclo', 'periodo').all()
    programas_antiguos = ProgramaEducativoAntiguo.objects.all()
    programas_nuevos = ProgramaEducativoNuevo.objects.all()

    filtro_ciclo = request.GET.get('ciclo')
    filtro_programa = request.GET.get('programa')
    filtro_tipo = request.GET.get('tipo')

    registros = NuevoIngreso.objects.all()

    if filtro_ciclo and filtro_ciclo != "Todos":
        registros = registros.filter(ciclo_periodo__id=filtro_ciclo)

    if filtro_programa and filtro_programa != "Todos":
        registros = registros.filter(
            programa_antiguo__id=filtro_programa
        ) | registros.filter(
            programa_nuevo__id=filtro_programa
        )

    datos_por_anio = defaultdict(lambda: {'examen': 0, 'renoes': 0, 'uaem_gem': 0, 'pase_directo': 0})
    total_modalidad = {'examen': 0, 'renoes': 0, 'uaem_gem': 0, 'pase_directo': 0}

    for reg in registros:
        anio = reg.ciclo_periodo.ciclo.anio
        datos_por_anio[anio]['examen'] += reg.examen
        datos_por_anio[anio]['renoes'] += reg.renoes
        datos_por_anio[anio]['uaem_gem'] += reg.uaem_gem
        datos_por_anio[anio]['pase_directo'] += reg.pase_directo

        total_modalidad['examen'] += reg.examen
        total_modalidad['renoes'] += reg.renoes
        total_modalidad['uaem_gem'] += reg.uaem_gem
        total_modalidad['pase_directo'] += reg.pase_directo

    return render(request, 'graficas_examen.html', {
        'ciclos': ciclos,
        'programas': list(programas_antiguos) + list(programas_nuevos),
        'filtro_ciclo': filtro_ciclo,
        'filtro_programa': filtro_programa,
        'filtro_tipo': filtro_tipo,
        'datos_por_anio': json.dumps(datos_por_anio),
        'total_modalidad': json.dumps(total_modalidad),
    })
