from django.shortcuts import render
from api.models import EficienciaTerminal, CicloPeriodo
from django.db.models import Sum

def eficiencia_terminal_usuario_view(request):
    ciclos_periodos = CicloPeriodo.objects.select_related('ciclo', 'periodo')
    opciones_ciclo = sorted(
        [f"{cp.ciclo.anio} - {cp.periodo.clave}" for cp in ciclos_periodos],
        reverse=True
    )

    filtros = request.GET.getlist("filtro_anio")
    ciclos_objetivos = []

    if filtros and "Todos" not in filtros:
        for filtro in filtros:
            try:
                anio_str, periodo_clave = filtro.split(" - ")
                ciclo = CicloPeriodo.objects.select_related("ciclo", "periodo").get(
                    ciclo__anio=anio_str, periodo__clave=periodo_clave
                )
                ciclos_objetivos.append(ciclo)
            except CicloPeriodo.DoesNotExist:
                continue
    else:
        ciclos_objetivos = list(CicloPeriodo.objects.all())

    datos_graficas = {'eficiencia': 0}
    detalle_ciclos = []

    if ciclos_objetivos:
        registros = EficienciaTerminal.objects.select_related(
            'ciclo_periodo__ciclo', 'ciclo_periodo__periodo',
            'programa_antiguo', 'programa_nuevo'
        ).filter(ciclo_periodo__in=ciclos_objetivos)

        for r in registros:
            eficiencia = r.porcentaje_eficiencia
            datos_graficas['eficiencia'] += eficiencia

            detalle_ciclos.append({
                'ciclo': str(r.ciclo_periodo),
                'programa': r.programa_antiguo.nombre if r.programa_antiguo else r.programa_nuevo.nombre,
                'matricula_ingreso': r.matricula_ingreso,
                'egresados': r.egresados,
                'porcentaje': eficiencia
            })

    return render(request, 'eficiencia_terminal_usuario.html', {
        'anios': opciones_ciclo,
        'datos_graficas': datos_graficas,
        'detalle_ciclos': detalle_ciclos
    })
