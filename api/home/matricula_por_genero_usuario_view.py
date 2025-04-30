from django.shortcuts import render
from api.models import CicloPeriodo, MatriculaPorGenero
import json

def matricula_por_genero_usuario_view(request):
    ciclos = CicloPeriodo.objects.select_related("ciclo", "periodo").order_by("ciclo__anio", "periodo__clave")
    datos = {mg.ciclo_periodo_id: mg for mg in MatriculaPorGenero.objects.all()}

    labels = []
    hombres = []
    mujeres = []
    totales = []
    total_global_hombres = 0
    total_global_mujeres = 0

    for cp in ciclos:
        etiqueta = f"{cp.periodo.nombre} {cp.ciclo.anio}"
        labels.append(etiqueta)

        registro = datos.get(cp.id)
        h = registro.hombres if registro else 0
        m = registro.mujeres if registro else 0

        hombres.append(h)
        mujeres.append(m)
        totales.append(h + m)
        total_global_hombres += h
        total_global_mujeres += m

    datos_grafica_json = json.dumps({
        "labels": labels,
        "hombres": hombres,
        "mujeres": mujeres,
        "totales": totales,
        "pie_labels": ["Hombres", "Mujeres"],
        "pie_data": [total_global_hombres, total_global_mujeres]
    })

    return render(request, "matricula_por_genero_usuario.html", {
        "datos_grafica_json": datos_grafica_json
    })
