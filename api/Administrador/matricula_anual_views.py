# api/Administrador/matricula_anual_views.py
from django.shortcuts import render
from django.db.models import Q
from collections import defaultdict
import json

from api.models import (
    NuevoIngreso,
    ProgramaEducativoAntiguo,
    ProgramaEducativoNuevo,
)

PERIODOS = ("Enero - Abril", "Mayo - Agosto", "Septiembre - Diciembre")


def matricula_por_anio_view(request):
    """
    Matrícula Anual (admin): aplica filtros a gráficas y TABLA.
    Filtros esperados (GET):
      - filtroAnio (múltiple)
      - cuatrimestre ("Todos" | nombre exacto)
      - tipo_programa: "antiguo" | "nuevo" | "todos"
      - filtroCarreras (múltiple, IDs)
    Renderiza: templates/matricula_anual.html
    """

    # ---------- Lectura de filtros ----------
    filtro_anios = request.GET.getlist("filtroAnio")              # múltiple
    filtro_cuatrimestre = request.GET.get("cuatrimestre", "Todos")
    tipo_programa = request.GET.get("tipo_programa", "todos")     # antiguo|nuevo|todos
    filtro_carreras = request.GET.getlist("filtroCarreras")       # múltiple (IDs)

    # ---------- Query base ----------
    registros = NuevoIngreso.objects.select_related(
        "ciclo_periodo__ciclo", "ciclo_periodo__periodo",
        "programa_antiguo", "programa_nuevo"
    )

    # Año (multi)
    if filtro_anios and "Todos" not in filtro_anios:
        registros = registros.filter(ciclo_periodo__ciclo__anio__in=filtro_anios)

    # Cuatrimestre
    if filtro_cuatrimestre and filtro_cuatrimestre != "Todos":
        registros = registros.filter(ciclo_periodo__periodo__nombre=filtro_cuatrimestre)

    # Tipo de programa
    if tipo_programa == "antiguo":
        registros = registros.filter(programa_antiguo__isnull=False)
    elif tipo_programa == "nuevo":
        registros = registros.filter(programa_nuevo__isnull=False)
    # "todos": no se filtra por nulls

    # Carreras (IDs válidos tanto en antiguo como en nuevo)
    if filtro_carreras and "Todos" not in filtro_carreras:
        registros = registros.filter(
            Q(programa_antiguo__id__in=filtro_carreras) |
            Q(programa_nuevo__id__in=filtro_carreras)
        )

    # ---------- Agregación por (año, programa) y por periodo ----------
    datos_antiguos = defaultdict(lambda: {p: 0 for p in PERIODOS})
    datos_nuevos  = defaultdict(lambda: {p: 0 for p in PERIODOS})
    anios_set = set()
    programas_antiguos_nombres = set()
    programas_nuevos_nombres = set()

    for reg in registros:
        ciclo = reg.ciclo_periodo
        anio = str(ciclo.ciclo.anio)
        periodo = ciclo.periodo.nombre
        total_reg = (reg.examen or 0) + (reg.renoes or 0) + (reg.uaem_gem or 0) + (reg.pase_directo or 0)
        anios_set.add(anio)

        if reg.programa_antiguo and tipo_programa in ("antiguo", "todos"):
            nombre = reg.programa_antiguo.nombre
            key = f"{anio}-{nombre}"
            if periodo in datos_antiguos[key]:
                datos_antiguos[key][periodo] += total_reg
            programas_antiguos_nombres.add(nombre)

        elif reg.programa_nuevo and tipo_programa in ("nuevo", "todos"):
            nombre = reg.programa_nuevo.nombre
            key = f"{anio}-{nombre}"
            if periodo in datos_nuevos[key]:
                datos_nuevos[key][periodo] += total_reg
            programas_nuevos_nombres.add(nombre)

    # ---------- Construcción de la TABLA (ya filtrada) ----------
    tabla_datos = []
    combinado = {**datos_antiguos, **datos_nuevos}
    for key, periodos in combinado.items():
        anio, programa = key.split("-", 1)
        ene_abr = periodos.get("Enero - Abril", 0)
        may_ago = periodos.get("Mayo - Agosto", 0)
        sep_dic = periodos.get("Septiembre - Diciembre", 0)
        total = ene_abr + may_ago + sep_dic

        tabla_datos.append({
            "anio": anio,
            "programa": programa,
            "ene_abr": ene_abr,
            "may_ago": may_ago,
            "sep_dic": sep_dic,
            "total": total
        })

    # Orden por año y programa
    tabla_datos.sort(key=lambda r: (int(r["anio"]), r["programa"]))

    # ---------- Catálogo de carreras para el select ----------
    if tipo_programa == "nuevo":
        programas_catalogo = ProgramaEducativoNuevo.objects.all().order_by("nombre")
    elif tipo_programa == "antiguo":
        programas_catalogo = ProgramaEducativoAntiguo.objects.all().order_by("nombre")
    else:
        programas_catalogo = list(ProgramaEducativoAntiguo.objects.all().order_by("nombre")) + \
                             list(ProgramaEducativoNuevo.objects.all().order_by("nombre"))

    # ---------- Contexto ----------
    context = {
        # combos
        "anios_lista": sorted(anios_set),
        "programas_catalogo": programas_catalogo,

        # filtros seleccionados (para mantener selección)
        "filtro_anios_sel": filtro_anios,
        "filtro_cuatrimestre_sel": filtro_cuatrimestre,
        "tipo_programa": tipo_programa,
        "filtro_carreras_sel": filtro_carreras,

        # datos para JS de gráficas (si los usas)
        "programas_antiguos_lista": json.dumps(sorted(programas_antiguos_nombres)),
        "programas_nuevos_lista": json.dumps(sorted(programas_nuevos_nombres)),
        "data_antiguos_json": json.dumps(datos_antiguos),
        "data_nuevos_json": json.dumps(datos_nuevos),

        # tabla (lo que itera tu template)
        "tabla_datos": tabla_datos,
    }

    return render(request, "matricula_anual.html", context)
