from django.shortcuts import render, redirect
from api.models import CicloPeriodo, MatriculaPorGenero
import json

def matriculagenero(request):
    mensaje = None

    # Guardar datos si viene un POST
    if request.method == "POST":
        for key, value in request.POST.items():
            if key.startswith("hombres_") or key.startswith("mujeres_"):
                _, pk = key.split("_")
                try:
                    hombres = int(request.POST.get(f"hombres_{pk}", 0))
                    mujeres = int(request.POST.get(f"mujeres_{pk}", 0))
                    ciclo_periodo = CicloPeriodo.objects.get(pk=pk)

                    registro, _ = MatriculaPorGenero.objects.get_or_create(ciclo_periodo=ciclo_periodo)
                    registro.hombres = hombres
                    registro.mujeres = mujeres
                    registro.save()
                except Exception as e:
                    mensaje = f"Error al guardar datos: {e}"
        if not mensaje:
            mensaje = "✅ Datos guardados correctamente"
        return redirect("matricula_por_genero")

    # Obtener todos los ciclos/periodos ordenados
    ciclos = CicloPeriodo.objects.select_related("ciclo", "periodo").order_by("ciclo__anio", "periodo__clave")

    # Obtener registros existentes
    datos = {mg.ciclo_periodo_id: mg for mg in MatriculaPorGenero.objects.all()}

    # Preparar datos para las gráficas
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
        if registro:
            h = registro.hombres
            m = registro.mujeres
        else:
            h = 0
            m = 0

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

    return render(request, "matricula_por_genero.html", {
        "ciclos": ciclos,
        "datos": datos,
        "mensaje": mensaje,
        "datos_grafica_json": datos_grafica_json
    })
