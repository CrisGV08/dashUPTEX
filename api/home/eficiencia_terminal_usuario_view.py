# api/home/eficiencia_terminal_usuario_view.py
from django.shortcuts import render
from api.models import EficienciaTerminal

def eficiencia_terminal_usuario_view(request):
    qs = (
        EficienciaTerminal.objects
        .select_related(
            "programa_antiguo", "programa_nuevo",
            "ciclo_periodo__ciclo", "ciclo_periodo__periodo"
        )
    )

    # Años disponibles para el filtro (e.g. 2024, 2023...)
    anios = sorted(
        qs.values_list("ciclo_periodo__ciclo__anio", flat=True).distinct(),
        reverse=True
    )

    # Filtro por año (opcional)
    filtro_anio = request.GET.get("filtro_anio", "Todos")
    if filtro_anio and filtro_anio != "Todos":
        qs = qs.filter(ciclo_periodo__ciclo__anio=filtro_anio)

    # Construir tabla y acumular totales para la gráfica
    detalle_ciclos = []
    total_matricula = 0
    total_egresados = 0

    for e in qs:
        programa = e.programa_antiguo.nombre if e.programa_antiguo else (e.programa_nuevo.nombre if e.programa_nuevo else "N/D")
        anio = e.ciclo_periodo.ciclo.anio
        periodo = e.ciclo_periodo.periodo.clave
        matricula = e.matricula_ingreso or 0
        egresados = e.egresados or 0
        porcentaje = round((egresados / matricula) * 100, 2) if matricula else 0

        detalle_ciclos.append({
            "ciclo": f"{anio} - {periodo}",
            "programa": programa,
            "matricula_ingreso": matricula,
            "egresados": egresados,
            "porcentaje": porcentaje,
        })

        total_matricula += matricula
        total_egresados += egresados

    # Valor único que usarán las gráficas de usuario
    eficiencia_global = round((total_egresados / total_matricula) * 100, 2) if total_matricula else 0

    ctx = {
        "anios": anios,
        "detalle_ciclos": detalle_ciclos,
        "datos_graficas": {"eficiencia": eficiencia_global},
    }
    return render(request, "eficiencia_terminal_usuario.html", ctx)
