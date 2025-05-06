from django.shortcuts import render
from django.db.models import Sum
from api.models import IndicadoresGenerales

def indicadores_generales_usuario_view(request):
    filtro_anio = request.GET.get('filtro_anio')

    if filtro_anio and filtro_anio != "Todos":
        indicadores = IndicadoresGenerales.objects.filter(ciclo_periodo__ciclo__anio=filtro_anio)
    else:
        indicadores = IndicadoresGenerales.objects.all()

    anios = IndicadoresGenerales.objects.values_list('ciclo_periodo__ciclo__anio', flat=True).distinct().order_by('ciclo_periodo__ciclo__anio')

    ciclos = []
    datos_matricula = []
    datos_desercion = []
    datos_reprobacion = []
    datos_egresados = []

    for i in indicadores.order_by('ciclo_periodo__ciclo__anio', 'ciclo_periodo__periodo__clave'):
        cp = i.ciclo_periodo
        etiqueta = f"{cp.ciclo.anio} {cp.periodo.clave}"
        ciclos.append(etiqueta)
        datos_matricula.append(i.matricula_total)
        datos_desercion.append(i.desertores)
        datos_reprobacion.append(i.reprobados)
        datos_egresados.append(i.egresados)

    context = {
        'anios': anios,
        'indicadores': indicadores,
        'datos_matricula': datos_matricula,
        'datos_desercion': datos_desercion,
        'datos_reprobacion': datos_reprobacion,
        'datos_egresados': datos_egresados,
        'ciclos_mostrar': ciclos
    }

    return render(request, 'indicadores_generales_usuario.html', context)