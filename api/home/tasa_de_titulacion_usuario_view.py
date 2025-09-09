# api/Usuario/tasa_de_titulacion_usuario_view.py
from django.shortcuts import render
from django.db.models.functions import ExtractYear
import json  # <-- necesario para serializar a JSON

from api.models import (
    GeneracionCarrera,
    ProgramaEducativoAntiguo,
    ProgramaEducativoNuevo,
)

# -------- Helpers ----------
def _i(v):
    try:
        return int(v or 0)
    except Exception:
        return 0

def _pct(n, d):
    n = float(_i(n)); d = float(_i(d))
    return round((n / d) * 100.0, 2) if d > 0 else 0.0


def build_tasa_usuario_context(request):
    """
    Construye el contexto de la vista de usuario SIN depender de una URL propia.
    Puedes llamarla desde otra view (dashboard) y renderizar el template.
    """
    qs = (
        GeneracionCarrera.objects
        .select_related("programa_antiguo", "programa_nuevo")
        .annotate(anio_ingreso=ExtractYear("fecha_ingreso"),
                  anio_egreso=ExtractYear("fecha_egreso"))
        .order_by("anio_ingreso", "anio_egreso")
    )

    # --- Transformar rows a la estructura que usa el JS ---
    datos = []
    anios_set = set()

    for r in qs:
        # año: usa fecha_ingreso si existe; si no, fecha_egreso
        anio = r.anio_ingreso or r.anio_egreso
        if not anio:
            continue
        anios_set.add(int(anio))

        if r.programa_antiguo_id:
            tipo = "ANTIGUO"
            prog_id = r.programa_antiguo.id
            prog_nombre = r.programa_antiguo.nombre
        elif r.programa_nuevo_id:
            tipo = "NUEVO"
            prog_id = r.programa_nuevo.id
            prog_nombre = r.programa_nuevo.nombre
        else:
            continue

        matricula = _i(r.ingreso_hombres) + _i(r.ingreso_mujeres)
        egresados = (
            _i(r.egresados_cohorte_h) + _i(r.egresados_cohorte_m) +
            _i(r.egresados_rezagados_h) + _i(r.egresados_rezagados_m)
        )
        titulados = _i(r.titulados_h) + _i(r.titulados_m)

        datos.append({
            "programa": prog_nombre,
            "programa_id": prog_id,
            "tipo": tipo,
            "anio_ingreso": int(anio),
            "matricula": matricula,
            "egresados": egresados,
            "titulados": titulados,
            "eficiencia_terminal": _pct(egresados, matricula),
            "tasa_titulacion": _pct(titulados, matricula),
        })

    # Catálogos para selects (ambos tipos)
    programas_antiguos = ProgramaEducativoAntiguo.objects.all().order_by("nombre")
    programas_nuevos = ProgramaEducativoNuevo.objects.all().order_by("nombre")

    context = {
        "datos_json": json.dumps(datos, ensure_ascii=False),  # <-- AHORA sí es JSON
        "anios": sorted(anios_set),
        "programas_antiguos": programas_antiguos,
        "programas_nuevos": programas_nuevos,
    }
    return context


# --- OPCIONAL: vista directa (por si luego la quieres montar con URL) ---
def tasa_de_titulacion_usuario_view(request):
    """
    Vista de usuario. Si no la expones en urls.py, puedes:
    - Llamar a build_tasa_usuario_context(request) desde tu dashboard y
      hacer render al template 'tasa_de_titulacion_usuario.html'
    """
    context = build_tasa_usuario_context(request)
    return render(request, "tasa_de_titulacion_usuario.html", context)
