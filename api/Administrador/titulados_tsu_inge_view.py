# api/Administrador/titulados_tsu_inge_view.py
from django.shortcuts import render
from django.db.models import F, Q, Value as V
from django.db.models.functions import Coalesce
from django.core.paginator import Paginator

from api.models import (
    ProgramaEducativoAntiguo,
    ProgramaEducativoNuevo,
    ProgramaEducativo,   # catálogo (id, tipo)
    TituladosHistoricos,
)

# ----------------- helpers -----------------
def _y(x):
    try:
        return int(float(x))
    except Exception:
        return 0

def _has_field(model, name: str) -> bool:
    return any(f.name == name for f in model._meta.get_fields())

# ----------------- view -----------------
def titulados_tsu_inge_view(request):
    """
    Página: 'Titulados por TSU e Ingeniería'

    Filtros GET:
      - nivel=TSU|ING (default TSU)
      - anio=...     (múltiple)
      - programa=... (múltiple, por NOMBRE exacto)
      - buscar=...   (opcional, por NOMBRE icontains)
    """
    nivel = (request.GET.get("nivel") or "TSU").upper()
    nivel = "TSU" if nivel == "TSU" else "ING"  # normaliza a TSU/ING

    # -------- base: queryset ordenado --------
    qs = (
        TituladosHistoricos.objects
        .select_related("programa_antiguo", "programa_nuevo")
        .order_by("anio_ingreso", "anio_egreso", "programa_antiguo__id", "programa_nuevo__id")
    )

    # -------- filtro por nivel --------
    # Opción A: si existiera un campo 'semestre' en el modelo
    if _has_field(TituladosHistoricos, "semestre"):
        semestre_objetivo = 5 if nivel == "TSU" else 10
        qs = qs.filter(semestre=semestre_objetivo)
    else:
        # Opción B (robusta): usar catálogo ProgramaEducativo (id -> tipo)
        tec_ids = set(
            ProgramaEducativo.objects
            .filter(tipo__iexact="TECNICO")
            .values_list("id", flat=True)
        )
        ing_ids = set(
            ProgramaEducativo.objects
            .filter(tipo__iexact="INGENIERO")
            .values_list("id", flat=True)
        )

        if tec_ids or ing_ids:
            qs = qs.annotate(
                prog_id=Coalesce(F("programa_antiguo__id"), F("programa_nuevo__id"))
            )
            if nivel == "TSU" and tec_ids:
                qs = qs.filter(prog_id__in=tec_ids)
            elif nivel == "ING" and ing_ids:
                qs = qs.filter(prog_id__in=ing_ids)
        # Si el catálogo está vacío, no se filtra por nivel para evitar pantalla en blanco.

    # -------- filtros UI (años / programas / búsqueda) --------
    anios = request.GET.getlist("anio")
    if anios:
        anios_int = [a for a in (_y(x) for x in anios) if a]
        if anios_int:
            qs = qs.filter(anio_ingreso__in=anios_int)

    programas = request.GET.getlist("programa")
    if programas:
        qs = qs.filter(
            Q(programa_antiguo__nombre__in=programas) |
            Q(programa_nuevo__nombre__in=programas)
        )

    buscar = (request.GET.get("buscar") or "").strip()
    if buscar:
        qs = qs.filter(
            Q(programa_antiguo__nombre__icontains=buscar) |
            Q(programa_nuevo__nombre__icontains=buscar)
        )

    # -------- paginación --------
    try:
        per_page = max(1, min(500, int(request.GET.get("per_page", 50))))
    except Exception:
        per_page = 50
    page_number = request.GET.get("page", 1)
    paginator = Paginator(qs, per_page)
    registros_page = paginator.get_page(page_number)

    # -------- catálogos (sobre el conjunto ya filtrado por nivel/filtros) --------
    cat_anios = (
        qs.values_list("anio_ingreso", flat=True)
          .distinct().order_by("anio_ingreso")
    )
    cat_programas = (
        qs.annotate(
            programa_nombre=Coalesce(
                F("programa_antiguo__nombre"),
                F("programa_nuevo__nombre"),
                V("SIN PROGRAMA"),
            )
        )
        .values_list("programa_nombre", flat=True)
        .distinct()
        .order_by("programa_nombre")
    )

    # (opcionales) catálogos globales
    programas_antiguos = ProgramaEducativoAntiguo.objects.only("id", "nombre").order_by("nombre")
    programas_nuevos   = ProgramaEducativoNuevo.objects.only("id", "nombre").order_by("nombre")

    # -------- datos para gráficas --------
    datos_qs = (
        qs.annotate(
            programa_nombre=Coalesce(
                F("programa_antiguo__nombre"),
                F("programa_nuevo__nombre"),
                V("SIN PROGRAMA"),
            ),
            total_tit=Coalesce(F("titulados_hombres"), V(0)) + Coalesce(F("titulados_mujeres"), V(0)),
            total_dgp_calc=Coalesce(F("registrados_dgp_h"), V(0)) + Coalesce(F("registrados_dgp_m"), V(0)),
        )
        .values(
            "programa_nombre", "anio_ingreso", "anio_egreso",
            "titulados_hombres", "titulados_mujeres",
            "registrados_dgp_h", "registrados_dgp_m",
            "total_tit", "total_dgp_calc",
        )
    )

    datos_json = [
        {
            "programa": r["programa_nombre"] or "SIN PROGRAMA",
            "anio_ingreso": int(r["anio_ingreso"] or 0),
            "anio_egreso": int(r["anio_egreso"] or 0),
            "titulados_h": int(r["titulados_hombres"] or 0),
            "titulados_m": int(r["titulados_mujeres"] or 0),
            "dgp_h": int(r["registrados_dgp_h"] or 0),
            "dgp_m": int(r["registrados_dgp_m"] or 0),
            "total_titulados": int(r["total_tit"] or 0),
            "total_dgp": int(r["total_dgp_calc"] or 0),
        }
        for r in datos_qs
    ]

    return render(request, "titulados_tsu_inge.html", {
        "nivel": nivel,                         # 'TSU' o 'ING' para el toggle
        "registros": registros_page,            # tabla/paginación
        "paginator": paginator,
        "page_obj": registros_page,

        # selects basados en el dataset actual (nivel + filtros ya aplicados)
        "anios": cat_anios,
        "programas_disponibles": list(cat_programas),

        # (opcionales) catálogos globales
        "programas_antiguos": programas_antiguos,
        "programas_nuevos": programas_nuevos,

        # datos para JS (gráficas)
        "datos_json": datos_json,
    })
