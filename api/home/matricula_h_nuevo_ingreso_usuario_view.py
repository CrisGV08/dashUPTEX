from django.shortcuts import render
from django.db.models import Sum
from api.models import MatriculaNuevoIngreso, CicloPeriodo

def matricula_h_nuevo_ingreso_usuario_view(request):
    # Obtener todos los registros
    registros = MatriculaNuevoIngreso.objects.select_related(
        'ciclo_periodo',
        'programa_antiguo',
        'programa_nuevo'
    )

    # Obtener etiquetas de ciclos (ordenadas)
    ciclos = CicloPeriodo.objects.order_by('ciclo__anio', 'periodo__clave')
    etiquetas_ciclos = [f"{cp.ciclo.anio} {cp.periodo.clave}" for cp in ciclos]

    # Inicializar datos
    totales_por_ciclo = []
    total_antiguos = 0
    total_nuevos = 0
    programas_totales = {}

    # Calcular matrícula total por ciclo
    for cp in ciclos:
        total_ciclo = registros.filter(ciclo_periodo=cp).aggregate(total=Sum('cantidad'))['total'] or 0
        totales_por_ciclo.append(total_ciclo)

    # Separar totales por modalidad
    total_antiguos = registros.filter(programa_antiguo__isnull=False).aggregate(total=Sum('cantidad'))['total'] or 0
    total_nuevos = registros.filter(programa_nuevo__isnull=False).aggregate(total=Sum('cantidad'))['total'] or 0

    # Acumular por programa educativo
    for registro in registros:
        nombre_programa = ''
        if registro.programa_antiguo:
            nombre_programa = registro.programa_antiguo.nombre
        elif registro.programa_nuevo:
            nombre_programa = registro.programa_nuevo.nombre
        else:
            continue

        if nombre_programa not in programas_totales:
            programas_totales[nombre_programa] = [0] * len(ciclos)

        index = list(ciclos).index(registro.ciclo_periodo)
        programas_totales[nombre_programa][index] += registro.cantidad

    # Preparar contexto
    datos_dashboard = {
        'labels': etiquetas_ciclos,
        'totales': totales_por_ciclo,
        'total_antiguos': total_antiguos,
        'total_nuevos': total_nuevos,
        'programas_totales': programas_totales,
    }

    return render(request, 'matricula_h_nuevo_ingreso_usuario.html', {
        'datos_dashboard': datos_dashboard
    })