# api/home/indicadores_generales_usuario_view.py
import json
from django.shortcuts import render
from api.models import IndicadoresGenerales, CicloPeriodo, MatriculaPorCuatrimestre
from django.db.models import Sum

def indicadores_generales_usuario_view(request):
    ciclos_periodos = CicloPeriodo.objects.select_related('ciclo', 'periodo')
    opciones_ciclo = sorted(
        [f"{cp.ciclo.anio} - {cp.periodo.clave}" for cp in ciclos_periodos],
        reverse=True
    )

    filtro = request.GET.get("filtro_anio")
    ciclos_objetivos = []

    if filtro and filtro != "Todos":
        try:
            anio_str, periodo_clave = filtro.split(" - ")
            ciclo = CicloPeriodo.objects.get(
                ciclo__anio=anio_str,
                periodo__clave=periodo_clave
            )
            ciclos_objetivos.append(ciclo)
        except CicloPeriodo.DoesNotExist:
            pass
    else:
        ciclos_objetivos = list(CicloPeriodo.objects.all())

    datos_graficas = {'desercion': 0, 'reprobacion': 0}
    detalle_ciclos = []

    registros = IndicadoresGenerales.objects.select_related(
        'ciclo_periodo__ciclo', 'ciclo_periodo__periodo'
    ).filter(ciclo_periodo__in=ciclos_objetivos)

    for r in registros:
        total = MatriculaPorCuatrimestre.objects.filter(
            ciclo_periodo=r.ciclo_periodo
        ).aggregate(total=Sum('cantidad'))['total'] or 0

        if total == 0:
            continue

        porcentaje_desercion = round((r.desertores / total) * 100, 2)
        porcentaje_reprobacion = round((r.reprobados / total) * 100, 2)

        datos_graficas['desercion'] += porcentaje_desercion
        datos_graficas['reprobacion'] += porcentaje_reprobacion

        detalle_ciclos.append({
            'ciclo': str(r.ciclo_periodo),
            'matricula': total,
            'desercion': r.desertores,
            'reprobacion': r.reprobados,
            'egresados': r.egresados,
            'porcentaje_desercion': porcentaje_desercion,
            'porcentaje_reprobacion': porcentaje_reprobacion
        })

    return render(request, 'indicadores_generales_usuario.html', {
        'anios': opciones_ciclo,
        'datos_graficas': datos_graficas,
        'datos_graficas_json': json.dumps(datos_graficas),  # 👈 para inyectar JSON real
        'detalle_ciclos': detalle_ciclos
    })
