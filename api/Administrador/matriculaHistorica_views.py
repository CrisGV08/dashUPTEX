from django.shortcuts import render, redirect
from collections import defaultdict
from api.models import CicloPeriodo, ProgramaEducativoAntiguo, ProgramaEducativoNuevo, MatriculaHistorica
import json

def matricula_historica(request):
    if request.method == 'POST':
        for key, value in request.POST.items():
            if key.startswith('celda_antiguo_') or key.startswith('celda_nuevo_'):
                try:
                    if value.strip() == '':
                        continue

                    cantidad = int(value)
                    partes = key.split('_')
                    tipo = partes[1]
                    programa_id = partes[2]
                    ciclo_id = partes[3]

                    filtros = {'ciclo_periodo_id': ciclo_id}
                    if tipo == 'antiguo':
                        filtros['programa_antiguo_id'] = programa_id
                        filtros['programa_nuevo_id'] = None
                    else:
                        filtros['programa_nuevo_id'] = programa_id
                        filtros['programa_antiguo_id'] = None

                    MatriculaHistorica.objects.update_or_create(
                        **filtros,
                        defaults={'cantidad': cantidad}
                    )
                except Exception as e:
                    print(f"Error procesando {key}: {e}")

    ciclos = list(CicloPeriodo.objects.select_related("ciclo", "periodo").order_by("ciclo__anio", "periodo__clave"))
    programas_antiguos = list(ProgramaEducativoAntiguo.objects.all())
    programas_nuevos = list(ProgramaEducativoNuevo.objects.all())

    registros = MatriculaHistorica.objects.all()
    datos = defaultdict(dict)
    totales_por_ciclo = defaultdict(int)
    programas_totales = defaultdict(lambda: [0]*len(ciclos))  # Para gráfica por carrera

    ciclo_id_map = {cp.id: idx for idx, cp in enumerate(ciclos)}

    for reg in registros:
        programa_id = reg.programa_antiguo_id or reg.programa_nuevo_id
        datos[programa_id][reg.ciclo_periodo_id] = reg.cantidad
        totales_por_ciclo[reg.ciclo_periodo_id] += reg.cantidad

        if reg.ciclo_periodo_id in ciclo_id_map:
            index = ciclo_id_map[reg.ciclo_periodo_id]
            nombre = str(reg.programa_antiguo or reg.programa_nuevo)
            programas_totales[nombre][index] += reg.cantidad

    labels_ciclos = [f"{cp.periodo.nombre} {cp.ciclo.anio}" for cp in ciclos]
    totales_lista = [totales_por_ciclo.get(cp.id, 0) for cp in ciclos]

    context = {
        "ciclos": ciclos,
        "programas_antiguos": programas_antiguos,
        "programas_nuevos": programas_nuevos,
        "datos": datos,
        "totales_por_ciclo": totales_por_ciclo,
        "labels_json": json.dumps(labels_ciclos),
        "totales_json": json.dumps(totales_lista),
        "programas_json": json.dumps(programas_totales),
    }

    return render(request, "matricula_historica.html", context)
