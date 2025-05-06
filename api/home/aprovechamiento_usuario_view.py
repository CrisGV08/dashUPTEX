from django.shortcuts import render
from django.db.models import Avg
from api.models import AprovechamientoAcademico, CicloPeriodo

def aprovechamiento_usuario_view(request):
    filtro_anio = request.GET.get('filtro_anio')

    registros = AprovechamientoAcademico.objects.all()
    if filtro_anio and filtro_anio != "Todos":
        registros = registros.filter(ciclo_periodo__ciclo__anio=filtro_anio)

    detalle_programas = []
    programas = []
    promedios_hist = []

    for r in registros:
        nombre = r.programa_antiguo.nombre if r.programa_antiguo else r.programa_nuevo.nombre
        if nombre not in programas:
            promedio = registros.filter(
                programa_antiguo=r.programa_antiguo,
                programa_nuevo=r.programa_nuevo
            ).aggregate(avg=Avg('promedio'))['avg'] or 0
            programas.append(nombre)
            promedios_hist.append(round(promedio, 2))
            detalle_programas.append({'programa': nombre, 'promedio': round(promedio, 2)})

    ciclos = []
    promedios_ciclo = []
    ciclos_cp = registros.values_list('ciclo_periodo__id', flat=True).distinct()
    cps = CicloPeriodo.objects.filter(id__in=ciclos_cp).order_by('ciclo__anio', 'periodo__clave')
    for cp in cps:
        etiqueta = f"{cp.ciclo.anio} {cp.periodo.clave}"
        promedio = registros.filter(ciclo_periodo=cp).aggregate(avg=Avg('promedio'))['avg'] or 0
        ciclos.append(etiqueta)
        promedios_ciclo.append(round(promedio, 2))

    anios = AprovechamientoAcademico.objects.values_list('ciclo_periodo__ciclo__anio', flat=True).distinct().order_by('ciclo_periodo__ciclo__anio')

    context = {
        'anios': anios,
        'detalle_programas': detalle_programas,
        'programas': programas,
        'promedios_hist': promedios_hist,
        'ciclos': ciclos,
        'promedios_ciclo': promedios_ciclo,
    }

    return render(request, 'aprovechamiento_usuario.html', context)