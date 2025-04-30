from django.shortcuts import render
from django.db.models import Sum, F
from api.models import CicloPeriodo, ProgramaEducativoAntiguo, MatriculaPorCuatrimestre
import json

def matricula_cuatrimestre_usuario_view(request):
    ciclos = CicloPeriodo.objects.select_related('ciclo', 'periodo').order_by('ciclo__anio', 'periodo__clave')
    programas = ProgramaEducativoAntiguo.objects.all().order_by('nombre')

    filtro_ciclo = request.GET.get('ciclo')
    filtro_programa = request.GET.get('programa')

    registros = MatriculaPorCuatrimestre.objects.select_related('ciclo_periodo', 'programa_antiguo')
    if filtro_ciclo and filtro_ciclo != "Todos":
        registros = registros.filter(ciclo_periodo__id=filtro_ciclo)
    if filtro_programa and filtro_programa != "Todos":
        registros = registros.filter(programa_antiguo__id=filtro_programa)

    tabla = [
        {
            'programa': r.programa_antiguo.nombre if r.programa_antiguo else '',
            'periodo': f"{r.ciclo_periodo.periodo.nombre} {r.ciclo_periodo.ciclo.anio}",
            'cantidad': r.cantidad
        }
        for r in registros
    ]

    grafica_data = registros.values(
        anio=F('ciclo_periodo__ciclo__anio'),
        periodo=F('ciclo_periodo__periodo__clave')
    ).annotate(total=Sum('cantidad')).order_by('anio', 'periodo')

    datos_grafica = {
        'labels': [f"{g['anio']} - {g['periodo']}" for g in grafica_data],
        'valores': [g['total'] for g in grafica_data]
    }

    return render(request, "matricula_por_cuatrimestre_usuario.html", {
        'ciclos': ciclos,
        'programas': programas,
        'filtro_ciclo': filtro_ciclo,
        'filtro_programa': filtro_programa,
        'tabla': tabla,
        'datos_grafica': json.dumps(datos_grafica)
    })
