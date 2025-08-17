from django.shortcuts import render, redirect
from collections import defaultdict
from api.models import CicloPeriodo, ProgramaEducativoAntiguo, ProgramaEducativoNuevo, MatriculaHistorica
import json

def matricula_historica(request):
    # Filtrar ciclos por año si se envía en GET
    anio_seleccionado = request.GET.get('anio')

    if anio_seleccionado:
        ciclos = list(CicloPeriodo.objects.select_related("ciclo", "periodo")
                      .filter(ciclo__anio=anio_seleccionado)
                      .order_by("periodo__clave"))
    else:
        ciclos = list(CicloPeriodo.objects.select_related("ciclo", "periodo")
                      .order_by("ciclo__anio", "periodo__clave"))

    programas_antiguos = list(ProgramaEducativoAntiguo.objects.all())
    programas_nuevos = list(ProgramaEducativoNuevo.objects.all())

    registros = MatriculaHistorica.objects.all()
    datos = defaultdict(dict)
    totales_por_ciclo = defaultdict(int)
    programas_totales = defaultdict(lambda: [0]*len(ciclos))

    ciclo_id_map = {cp.id: idx for idx, cp in enumerate(ciclos)}

    for reg in registros:
        programa_id = f"antiguo_{reg.programa_antiguo_id}" if reg.programa_antiguo_id else f"nuevo_{reg.programa_nuevo_id}"
        datos[programa_id][reg.ciclo_periodo_id] = reg.cantidad
        totales_por_ciclo[reg.ciclo_periodo_id] += reg.cantidad

        if reg.ciclo_periodo_id in ciclo_id_map:
            index = ciclo_id_map[reg.ciclo_periodo_id]
            nombre = str(reg.programa_antiguo or reg.programa_nuevo)
            programas_totales[nombre][index] += reg.cantidad

    labels_ciclos = [f"{cp.periodo.nombre} {cp.ciclo.anio}" for cp in ciclos]
    totales_dict = {
        f"{cp.periodo.nombre} {cp.ciclo.anio}": totales_por_ciclo.get(cp.id, 0)
        for cp in ciclos
    }

    # Obtener años únicos disponibles
    todos_ciclos = CicloPeriodo.objects.select_related("ciclo").all()
    anios_disponibles = sorted(set(cp.ciclo.anio for cp in todos_ciclos))

    context = {
        "ciclos": ciclos,
        "programas_antiguos": programas_antiguos,
        "programas_nuevos": programas_nuevos,
        "datos": datos,
        "totales_por_ciclo": totales_por_ciclo,
        "labels_json": json.dumps(labels_ciclos),
        "totales_json": json.dumps(totales_dict),
        "programas_json": json.dumps(programas_totales),
        "anios": anios_disponibles,
        "anio_seleccionado": anio_seleccionado,
    }

    return render(request, "matricula_historica.html", context)
