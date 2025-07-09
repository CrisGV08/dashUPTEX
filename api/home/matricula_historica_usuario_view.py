from django.shortcuts import render
from collections import defaultdict
from api.models import CicloPeriodo, ProgramaEducativoAntiguo, ProgramaEducativoNuevo, MatriculaHistorica
import json

def matricula_historica_usuario_view(request):
    ciclos = list(CicloPeriodo.objects.select_related("ciclo", "periodo").order_by("ciclo__anio", "periodo__clave"))
    programas_antiguos = list(ProgramaEducativoAntiguo.objects.all())
    programas_nuevos = list(ProgramaEducativoNuevo.objects.all())

    registros = MatriculaHistorica.objects.all()
    totales_por_ciclo = defaultdict(int)
    programas_totales = defaultdict(lambda: [0] * len(ciclos))  # Para gráfica por carrera

    ciclo_id_map = {cp.id: idx for idx, cp in enumerate(ciclos)}

    for reg in registros:
        if reg.ciclo_periodo_id in ciclo_id_map:
            idx = ciclo_id_map[reg.ciclo_periodo_id]
            nombre = str(reg.programa_antiguo or reg.programa_nuevo)
            programas_totales[nombre][idx] += reg.cantidad
            totales_por_ciclo[reg.ciclo_periodo_id] += reg.cantidad

    labels_ciclos = [f"{cp.periodo.nombre} {cp.ciclo.anio}" for cp in ciclos]
    totales_lista = [totales_por_ciclo.get(cp.id, 0) for cp in ciclos]

    context = {
        "labels_json": json.dumps(labels_ciclos),
        "totales_json": json.dumps(totales_lista),
        "programas_json": json.dumps(programas_totales),
        "ciclos": ciclos,  # ✅ AHORA YA SE VEN EN EL SELECT
    }

    return render(request, "matricula_historica_usuario.html", context)
