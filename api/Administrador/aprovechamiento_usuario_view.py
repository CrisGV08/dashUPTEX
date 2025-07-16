import json
from django.shortcuts import render
from api.models import AprovechamientoAcademico, CicloPeriodo

def aprovechamiento_usuario_view(request):
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
            ciclo = CicloPeriodo.objects.get(ciclo__anio=anio_str, periodo__clave=periodo_clave)
            ciclos_objetivos.append(ciclo)
        except CicloPeriodo.DoesNotExist:
            pass
    else:
        ciclos_objetivos = list(CicloPeriodo.objects.all())

    datos_graficas = {
        'programas': [],
        'promedios': []
    }
    detalle_ciclos = []

    registros = AprovechamientoAcademico.objects.select_related(
        'ciclo_periodo__ciclo', 'ciclo_periodo__periodo',
        'programa_antiguo', 'programa_nuevo'
    ).filter(ciclo_periodo__in=ciclos_objetivos)

    for r in registros:
        nombre_prog = r.programa_antiguo.nombre if r.programa_antiguo else r.programa_nuevo.nombre
        datos_graficas['programas'].append(nombre_prog)
        datos_graficas['promedios'].append(float(r.promedio))
        detalle_ciclos.append({
            'ciclo': str(r.ciclo_periodo),
            'programa': nombre_prog,
            'promedio': r.promedio
        })

    return render(request, 'aprovechamiento_usuario.html', {
        'anios': opciones_ciclo,
        'datos_graficas': json.dumps(datos_graficas),
        'detalle_ciclos': detalle_ciclos
    })
