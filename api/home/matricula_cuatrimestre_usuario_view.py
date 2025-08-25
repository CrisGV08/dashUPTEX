import json
from django.shortcuts import render, redirect
from django.db.models import Sum, F

from api.models import (
    CicloPeriodo,
    ProgramaEducativoAntiguo, ProgramaEducativoNuevo,
    MatriculaPorCuatrimestre,
)

def matricula_cuatrimestre_usuario_view(request):
    """
    Vista de usuario: mismos filtros (ciclo, tipo_programa, programa),
    sin subir/descargar CSV. Muestra tabla y 4 gráficas.
    """
    # ——— Catálogo de ciclos (ordenado) ———
    ciclos = (CicloPeriodo.objects
              .select_related('ciclo', 'periodo')
              .order_by('ciclo__anio', 'periodo__clave'))

    # ——— Lectura de filtros ———
    filtro_ciclo     = request.GET.get('ciclo')
    tipo_programa    = request.GET.get('tipo_programa', 'antiguo')  # default usuario: antiguo
    filtro_programa  = request.GET.get('programa')

    # ——— Catálogo de programas según tipo ———
    if tipo_programa == 'nuevo':
        programas = ProgramaEducativoNuevo.objects.all().order_by('nombre')
    else:
        programas = ProgramaEducativoAntiguo.objects.all().order_by('nombre')

    # ——— Query base ———
    registros = (MatriculaPorCuatrimestre.objects
                 .select_related('ciclo_periodo__ciclo', 'ciclo_periodo__periodo',
                                 'programa_antiguo', 'programa_nuevo'))

    # Ciclo
    if filtro_ciclo and filtro_ciclo != "Todos":
        registros = registros.filter(ciclo_periodo__id=filtro_ciclo)

    # Programa (según tipo)
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
            'cantidad': r.cantidad or 0
        })

    # ——— Datos para gráficas ———
    grafica_data = (registros.values(
                        anio=F('ciclo_periodo__ciclo__anio'),
                        periodo=F('ciclo_periodo__periodo__clave'))
                    .annotate(total=Sum('cantidad'))
                    .order_by('anio', 'periodo'))

    datos_grafica = {
        'labels': [f"{g['anio']} - {g['periodo']}" for g in grafica_data],
        'valores': [g['total'] for g in grafica_data]
    }

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
        'datos_grafica': json.dumps(datos_grafica),

        # << NUEVO: JSON válido para usar en JS >>
        'cat_antiguos': json.dumps(cat_antiguos),
        'cat_nuevos': json.dumps(cat_nuevos),
    }
    return render(request, "matricula_por_cuatrimestre_usuario.html", ctx)
