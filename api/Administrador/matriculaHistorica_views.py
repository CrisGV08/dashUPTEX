from django.shortcuts import render, redirect
from django.contrib import messages
from collections import defaultdict
from django.db import transaction
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

    # === GUARDAR DATOS SI HAY POST ===
    if request.method == "POST":
        try:
            with transaction.atomic():
                for ciclo in ciclos:
                    for programa in programas_antiguos:
                        input_name = f"celda_antiguo_{programa.id}_{ciclo.id}"
                        valor = request.POST.get(input_name)
                        if valor is not None:
                            cantidad = int(valor) if valor.strip() != "" else 0
                            MatriculaHistorica.objects.update_or_create(
                                ciclo_periodo=ciclo,
                                programa_antiguo=programa,
                                defaults={"cantidad": cantidad}
                            )

                    for programa in programas_nuevos:
                        input_name = f"celda_nuevo_{programa.id}_{ciclo.id}"
                        valor = request.POST.get(input_name)
                        if valor is not None:
                            cantidad = int(valor) if valor.strip() != "" else 0
                            MatriculaHistorica.objects.update_or_create(
                                ciclo_periodo=ciclo,
                                programa_nuevo=programa,
                                defaults={"cantidad": cantidad}
                            )

            messages.success(request, "✅ Los datos fueron guardados exitosamente.")
            return redirect('matricula_historica')  # Asegúrate que esta sea la URL correcta

        except Exception as e:
            messages.error(request, f"❌ Error al guardar los datos: {e}")

    # === CARGAR DATOS PARA VISUALIZACIÓN ===
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
