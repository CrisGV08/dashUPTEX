import json
from django.shortcuts import render
from django.db.models import Sum, F

from api.models import (
    CicloPeriodo,
    ProgramaEducativoAntiguo, ProgramaEducativoNuevo,
    MatriculaPorCuatrimestre,
)

def matricula_cuatrimestre_usuario_view(request):
    """
    Vista de usuario: filtros (ciclo, tipo_programa, programa), tabla
    y 4 gráficas (barras/línea multi-serie por programa, pastel por participación,
    gauss del total suavizado). Incluye catálogos para repoblar selects vía JS.
    """
    # ——— Catálogo de ciclos ———
    ciclos = (CicloPeriodo.objects
              .select_related('ciclo', 'periodo')
              .order_by('ciclo__anio', 'periodo__clave'))

    # ——— Filtros ———
    filtro_ciclo    = request.GET.get('ciclo')
    tipo_programa   = request.GET.get('tipo_programa', 'antiguo')  # default
    filtro_programa = request.GET.get('programa')

    # ——— Catálogo de programas según tipo ———
    if tipo_programa == 'nuevo':
        programas = ProgramaEducativoNuevo.objects.all().order_by('nombre')
    else:
        programas = ProgramaEducativoAntiguo.objects.all().order_by('nombre')

    # ——— Query base ———
    registros = (MatriculaPorCuatrimestre.objects
                 .select_related('ciclo_periodo__ciclo', 'ciclo_periodo__periodo',
                                 'programa_antiguo', 'programa_nuevo'))

    if filtro_ciclo and filtro_ciclo != "Todos":
        registros = registros.filter(ciclo_periodo__id=filtro_ciclo)

    if filtro_programa and filtro_programa != "Todos":
        if tipo_programa == 'nuevo':
            registros = registros.filter(programa_nuevo__id=filtro_programa)
        else:
            registros = registros.filter(programa_antiguo__id=filtro_programa)

    # ——— Tabla ———
    tabla = []
    for r in registros:
        nombre_prog = r.programa_nuevo.nombre if r.programa_nuevo else (r.programa_antiguo.nombre if r.programa_antiguo else '')
        tabla.append({
            'programa': nombre_prog,
            'periodo': f"{r.ciclo_periodo.periodo.nombre} {r.ciclo_periodo.ciclo.anio}",
            'cantidad': int(r.cantidad or 0),
        })

    # ——— Datos para GRÁFICAS (multi-series por programa) ———
    # Agrupa por periodo y programa
    agg = (registros.values(
                anio=F('ciclo_periodo__ciclo__anio'),
                periodo=F('ciclo_periodo__periodo__clave'),
                prog_ant=F('programa_antiguo__nombre'),
                prog_nvo=F('programa_nuevo__nombre'),
            )
            .annotate(total=Sum('cantidad'))
            .order_by('anio', 'periodo', 'prog_ant', 'prog_nvo'))

    # Si pidieron "nuevo" y no hay datos, caer a "antiguo"
    if not agg.exists() and tipo_programa == 'nuevo':
        tipo_programa = 'antiguo'
        programas = ProgramaEducativoAntiguo.objects.all().order_by('nombre')
        registros = (MatriculaPorCuatrimestre.objects
                     .select_related('ciclo_periodo__ciclo', 'ciclo_periodo__periodo',
                                     'programa_antiguo', 'programa_nuevo'))
        if filtro_ciclo and filtro_ciclo != "Todos":
            registros = registros.filter(ciclo_periodo__id=filtro_ciclo)
        if filtro_programa and filtro_programa != "Todos":
            registros = registros.filter(programa_antiguo__id=filtro_programa)
        agg = (registros.values(
                    anio=F('ciclo_periodo__ciclo__anio'),
                    periodo=F('ciclo_periodo__periodo__clave'),
                    prog_ant=F('programa_antiguo__nombre'),
                    prog_nvo=F('programa_nuevo__nombre'),
               )
               .annotate(total=Sum('cantidad'))
               .order_by('anio', 'periodo', 'prog_ant', 'prog_nvo'))

        # reconstruye tabla con el queryset final por si cambió
        tabla = []
        for r in registros:
            nombre_prog = r.programa_nuevo.nombre if r.programa_nuevo else (r.programa_antiguo.nombre if r.programa_antiguo else '')
            tabla.append({
                'programa': nombre_prog,
                'periodo': f"{r.ciclo_periodo.periodo.nombre} {r.ciclo_periodo.ciclo.anio}",
                'cantidad': int(r.cantidad or 0),
            })

    # Eje X (periodos en orden)
    etiquetas_periodo = []
    for row in agg:
        etq = f"{row['anio']} - {row['periodo']}"
        if etq not in etiquetas_periodo:
            etiquetas_periodo.append(etq)

    # Programas (nombres)
    nombres_programa = []
    for row in agg:
        nom = row['prog_ant'] or row['prog_nvo'] or ''
        if nom and nom not in nombres_programa:
            nombres_programa.append(nom)

    # Mapa programa -> valores por periodo
    series_map = {p: [0] * len(etiquetas_periodo) for p in nombres_programa}
    idx_x = {etq: i for i, etq in enumerate(etiquetas_periodo)}
    for row in agg:
        etq = f"{row['anio']} - {row['periodo']}"
        nom = row['prog_ant'] or row['prog_nvo'] or ''
        if not nom:
            continue
        series_map[nom][idx_x[etq]] = int(row['total'] or 0)

    # Totales por programa (para pie)
    totales_por_programa = {p: sum(vals) for p, vals in series_map.items()}

    datos_grafica = {
        'labels': etiquetas_periodo,
        'series': [{'label': p, 'data': series_map[p]} for p in nombres_programa],
        'pie_labels': list(totales_por_programa.keys()),
        'pie_values': list(totales_por_programa.values()),
    }

    # ——— Total general (para el <tfoot> de la tabla) ———
    total_general = registros.aggregate(total=Sum('cantidad'))['total'] or 0

    # ——— Catálogos para repoblar sin recargar (JS) ———
    cat_antiguos = list(ProgramaEducativoAntiguo.objects.values('id', 'nombre').order_by('nombre'))
    cat_nuevos   = list(ProgramaEducativoNuevo.objects.values('id', 'nombre').order_by('nombre'))

    ctx = {
        'ciclos': ciclos,
        'programas': programas,
        'filtro_ciclo': filtro_ciclo,
        'tipo_programa': tipo_programa,
        'filtro_programa': filtro_programa,
        'tabla': tabla,

        # JSON para las gráficas (multi-series)
        'datos_grafica': json.dumps(datos_grafica),

        # Total general para el tfoot
        'total_general': total_general,

        # Catálogos para repoblar selects vía JS
        'cat_antiguos': json.dumps(cat_antiguos),
        'cat_nuevos': json.dumps(cat_nuevos),
    }
    return render(request, "matricula_por_cuatrimestre_usuario.html", ctx)
