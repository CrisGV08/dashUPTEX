# api/Administrador/titulados_historicos_view.py
import io
import csv
import pandas as pd

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, F, ExpressionWrapper, IntegerField, Value as V
from django.db.models.functions import Coalesce
from django.core.paginator import Paginator
from django.utils.encoding import smart_str

from api.models import (
    ProgramaEducativoAntiguo,
    ProgramaEducativoNuevo,
    TituladosHistoricos,
)

# ========= Columnas aceptadas (SIN modalidad) =========
TH_COLS_STD = [
    "programa_tipo",          # 'ANTIGUO' | 'NUEVO'
    "programa_id",            # PK texto (ej. 'ISC')
    "programa_nombre",        # informativo
    "anio_ingreso",
    "anio_egreso",
    "titulados_hombres",
    "titulados_mujeres",
    "registrados_dgp_h",
    "registrados_dgp_m",
]

TH_COLS_LEGACY = [
    "PROGRAMA EDUCATIVO",     # puede ser ID o nombre
    "AÑO INGRESO",
    "AÑO EGRESO",
    "TITULADOS H",
    "TITULADOS M",
    "REG DGP H",
    "REG DGP M",
]

MAX_UPLOAD_MB = 10  # límite de subida


# ========= Helpers =========
def _i(x):
    """Entero >= 0 seguro."""
    try:
        return max(0, int(float(x)))
    except Exception:
        return 0


def _y(x):
    """Año entero seguro."""
    try:
        return int(float(x))
    except Exception:
        return 0


def _norm(x):
    return (str(x).strip() if x is not None else "")


def _norm_headers(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza encabezados (mayúsculas/trim) para tolerar variaciones."""
    cp = df.copy()
    cp.columns = [str(c).strip().upper() for c in cp.columns]
    return cp


def _apply_filters(request, qs):
    """
    Aplica filtros GET al queryset (sin modalidad).
    Soporta:
      - ?anio=...&anio=...   o ?anios=...
      - ?tipo_programa=antiguo|nuevo
      - ?programa=... (múltiple)
      - ?buscar=texto
      - rangos: ingreso_min/max, egreso_min/max
      - rangos totales: titulados_min/max, dgp_min/max
    """
    anios = request.GET.getlist("anio") or request.GET.getlist("anios")
    tipo = request.GET.get("tipo_programa")  # 'antiguo' | 'nuevo' | None
    programas = request.GET.getlist("programa") or request.GET.getlist("programas")
    buscar = request.GET.get("buscar", "").strip()

    ingreso_min = request.GET.get("ingreso_min")
    ingreso_max = request.GET.get("ingreso_max")
    egreso_min = request.GET.get("egreso_min")
    egreso_max = request.GET.get("egreso_max")
    tit_min = request.GET.get("titulados_min")
    tit_max = request.GET.get("titulados_max")
    dgp_min = request.GET.get("dgp_min")
    dgp_max = request.GET.get("dgp_max")

    if anios:
        anios_int = []
        for a in anios:
            try:
                anios_int.append(int(a))
            except Exception:
                pass
        if anios_int:
            qs = qs.filter(anio_ingreso__in=anios_int)

    if tipo == "antiguo":
        qs = qs.filter(programa_antiguo__isnull=False)
    elif tipo == "nuevo":
        qs = qs.filter(programa_nuevo__isnull=False)

    if programas:
        qs = qs.filter(
            Q(programa_antiguo__nombre__in=programas) |
            Q(programa_nuevo__nombre__in=programas)
        )

    if buscar:
        qs = qs.filter(
            Q(programa_antiguo__nombre__icontains=buscar) |
            Q(programa_nuevo__nombre__icontains=buscar)
        )

    if ingreso_min:
        qs = qs.filter(anio_ingreso__gte=_y(ingreso_min))
    if ingreso_max:
        qs = qs.filter(anio_ingreso__lte=_y(ingreso_max))
    if egreso_min:
        qs = qs.filter(anio_egreso__gte=_y(egreso_min))
    if egreso_max:
        qs = qs.filter(anio_egreso__lte=_y(egreso_max))

    tot_tit = ExpressionWrapper(
        F("titulados_hombres") + F("titulados_mujeres"), output_field=IntegerField()
    )
    tot_dgp = ExpressionWrapper(
        F("registrados_dgp_h") + F("registrados_dgp_m"), output_field=IntegerField()
    )
    qs = qs.annotate(_tot_titulados=tot_tit, _tot_dgp=tot_dgp)

    if tit_min:
        qs = qs.filter(_tot_titulados__gte=_i(tit_min))
    if tit_max:
        qs = qs.filter(_tot_titulados__lte=_i(tit_max))
    if dgp_min:
        qs = qs.filter(_tot_dgp__gte=_i(dgp_min))
    if dgp_max:
        qs = qs.filter(_tot_dgp__lte=_i(dgp_max))

    return qs


def _resolve_program(tipo, pid):
    if tipo == "ANTIGUO":
        pa = ProgramaEducativoAntiguo.objects.filter(pk=pid).first()
        return pa, None
    if tipo == "NUEVO":
        pn = ProgramaEducativoNuevo.objects.filter(pk=pid).first()
        return None, pn
    return None, None


def _resolve_program_from_legacy(val):
    key = _norm(val).upper()
    # primero por ID
    pa = ProgramaEducativoAntiguo.objects.filter(pk=key).first()
    if pa:
        return "ANTIGUO", pa.id, pa, None
    pn = ProgramaEducativoNuevo.objects.filter(pk=key).first()
    if pn:
        return "NUEVO", pn.id, None, pn
    # luego por nombre (exacto case-insensitive)
    pa = ProgramaEducativoAntiguo.objects.filter(nombre__iexact=val).first()
    if pa:
        return "ANTIGUO", pa.id, pa, None
    pn = ProgramaEducativoNuevo.objects.filter(nombre__iexact=val).first()
    if pn:
        return "NUEVO", pn.id, None, pn
    return None, None, None, None


def _valida_rangos(ai: int, ae: int, fila_ix: int, errores: list, span: int = 10) -> bool:
    """Valida rangos de años (ingreso 1990–2100; egreso entre ingreso y +span)."""
    if not (1990 <= ai <= 2100):
        errores.append(f"Fila {fila_ix}: año ingreso fuera de rango (1990–2100): {ai}.")
        return False
    if not (ai <= ae <= ai + span):
        errores.append(f"Fila {fila_ix}: año egreso debe estar entre {ai} y {ai + span}.")
        return False
    return True


# ========= Vistas =========
def titulados_historicos_view(request):
    """
    - Lista con filtros (server-side)
    - Paginación
    - Datos para gráficas (via annotate + values)
    - Carga de Excel (POST al mismo endpoint)
    """
    qs = (
        TituladosHistoricos.objects
        .select_related('programa_antiguo', 'programa_nuevo')
        .order_by('anio_ingreso', 'anio_egreso', 'programa_antiguo__id', 'programa_nuevo__id')
    )

    # Filtros server-side
    qs = _apply_filters(request, qs)

    # Paginación (cambia 50 si deseas otra cantidad)
    page_number = request.GET.get("page", 1)
    paginator = Paginator(qs, 50)
    registros_page = paginator.get_page(page_number)

    # Catálogos para UI (ligeros)
    anios = (
        TituladosHistoricos.objects
        .values_list('anio_ingreso', flat=True).distinct().order_by('anio_ingreso')
    )
    programas_antiguos = ProgramaEducativoAntiguo.objects.only("id", "nombre").order_by("nombre")
    programas_nuevos = ProgramaEducativoNuevo.objects.only("id", "nombre").order_by("nombre")

    # Datos para gráficas (ya filtrado), calculados en DB
    datos_qs = (
        qs.annotate(
            programa_nombre=Coalesce(F('programa_antiguo__nombre'),
                                     F('programa_nuevo__nombre'),
                                     V('SIN PROGRAMA')),
            total_titulados=F('titulados_hombres') + F('titulados_mujeres'),
            total_dgp=F('registrados_dgp_h') + F('registrados_dgp_m'),
        )
        .values(
            'programa_nombre', 'anio_ingreso', 'anio_egreso',
            'titulados_hombres', 'titulados_mujeres',
            'registrados_dgp_h', 'registrados_dgp_m',
            'total_titulados', 'total_dgp'
        )
    )
    datos_json = [
        {
            "programa": r["programa_nombre"],
            "anio_ingreso": r["anio_ingreso"],
            "anio_egreso": r["anio_egreso"],
            "titulados_h": r["titulados_hombres"],
            "titulados_m": r["titulados_mujeres"],
            "dgp_h": r["registrados_dgp_h"],
            "dgp_m": r["registrados_dgp_m"],
            "total_titulados": r["total_titulados"],
            "total_dgp": r["total_dgp"],
        }
        for r in datos_qs
    ]

    # ============= Carga de Excel (POST al mismo endpoint) =============
    f = request.FILES.get('archivo_excel')
    if request.method == 'POST' and f:
        # Validaciones rápidas
        if f.size > MAX_UPLOAD_MB * 1024 * 1024:
            messages.error(request, f"El archivo excede {MAX_UPLOAD_MB}MB.")
            return redirect('titulados_historicos')
        if not f.name.lower().endswith('.xlsx'):
            messages.error(request, "Sube un .xlsx (Excel moderno).")
            return redirect('titulados_historicos')

        try:
            df = pd.read_excel(f, engine="openpyxl")
            df = _norm_headers(df)
        except Exception as e:
            messages.error(request, f"❌ Error al leer el archivo Excel: {e}")
            return redirect('titulados_historicos')

        cols = set(df.columns)
        modo_std = set(c.upper() for c in TH_COLS_STD).issubset(cols)
        modo_legacy = set(c.upper() for c in TH_COLS_LEGACY).issubset(cols)

        if not (modo_std or modo_legacy):
            messages.error(
                request,
                "Formato de columnas no reconocido.\n"
                f"- Estándar: {', '.join(TH_COLS_STD)}\n"
                f"- Legado: {', '.join(TH_COLS_LEGACY)}"
            )
            return redirect('titulados_historicos')

        errores, filas_ok, vistos = [], [], set()
        def add_err(ix, msg): errores.append(f"Fila {ix}: {msg}")

        if modo_std:
            # Reasignamos a los nombres esperados (ya están en mayúsculas)
            cols_map = {c.upper(): c for c in df.columns}
            # Tomar solo columnas de interés
            use_cols = [cols_map[c.upper()] for c in TH_COLS_STD]
            df = df[use_cols].copy()
            # Re-nombrar a canon
            df.columns = TH_COLS_STD

            df["programa_tipo"] = df["programa_tipo"].astype(str).str.upper().str.strip()
            df["programa_id"] = df["programa_id"].astype(str).str.strip()
            for c in ["anio_ingreso", "anio_egreso"]:
                df[c] = df[c].apply(_y)
            for c in ["titulados_hombres", "titulados_mujeres", "registrados_dgp_h", "registrados_dgp_m"]:
                df[c] = df[c].apply(_i)

            for i, r in df.iterrows():
                ix = i + 2
                tipo, pid = r["programa_tipo"], r["programa_id"]
                ai, ae = r["anio_ingreso"], r["anio_egreso"]
                th, tm, dh, dm = r["titulados_hombres"], r["titulados_mujeres"], r["registrados_dgp_h"], r["registrados_dgp_m"]

                if tipo not in ("ANTIGUO", "NUEVO"):
                    add_err(ix, "programa_tipo debe ser 'ANTIGUO' o 'NUEVO'."); continue
                if not pid:
                    add_err(ix, "programa_id vacío."); continue
                if not _valida_rangos(ai, ae, ix, errores):
                    continue

                pa, pn = _resolve_program(tipo, pid)
                if not (pa or pn):
                    add_err(ix, f"programa_id '{pid}' no existe en {tipo}."); continue

                clave = (tipo, pid, ai, ae)
                if clave in vistos:
                    add_err(ix, f"Duplicado en archivo (tipo,id,ingreso,egreso)=({tipo},{pid},{ai},{ae})."); continue
                vistos.add(clave)

                filas_ok.append({
                    "pa": pa, "pn": pn, "ai": ai, "ae": ae,
                    "th": th, "tm": tm, "dh": dh, "dm": dm
                })
        else:
            # LEGACY
            # Reducimos a columnas y renombramos a corto
            cols_map = {c.upper(): c for c in df.columns}
            use_cols = [cols_map[c.upper()] for c in TH_COLS_LEGACY]
            df = df[use_cols].copy()
            df.rename(columns={
                "PROGRAMA EDUCATIVO": "prog",
                "AÑO INGRESO": "ai",
                "AÑO EGRESO": "ae",
                "TITULADOS H": "th",
                "TITULADOS M": "tm",
                "REG DGP H": "dh",
                "REG DGP M": "dm",
            }, inplace=True)

            df["ai"] = df["ai"].apply(_y)
            df["ae"] = df["ae"].apply(_y)
            for c in ["th", "tm", "dh", "dm"]:
                df[c] = df[c].apply(_i)

            for i, r in df.iterrows():
                ix = i + 2
                tipo, pid, pa, pn = _resolve_program_from_legacy(r["prog"])
                ai, ae, th, tm, dh, dm = r["ai"], r["ae"], r["th"], r["tm"], r["dh"], r["dm"]

                if not (pa or pn):
                    add_err(ix, f"Programa '{r['prog']}' no encontrado por ID ni por nombre.")
                    continue
                if not _valida_rangos(ai, ae, ix, errores):
                    continue

                clave = (tipo, pid, ai, ae)
                if clave in vistos:
                    add_err(ix, f"Duplicado en archivo (tipo,id,ingreso,egreso)=({tipo},{pid},{ai},{ae}).")
                    continue
                vistos.add(clave)

                filas_ok.append({
                    "pa": pa, "pn": pn, "ai": ai, "ae": ae,
                    "th": th, "tm": tm, "dh": dh, "dm": dm
                })

        if errores:
            for e in errores[:20]:
                messages.error(request, e)
            if len(errores) > 20:
                messages.error(request, f"…y {len(errores) - 20} error(es) más.")
            return redirect('titulados_historicos')

        creados = actualizados = 0
        with transaction.atomic():
            for r in filas_ok:
                defaults = {
                    "titulados_hombres": r["th"],
                    "titulados_mujeres": r["tm"],
                    "registrados_dgp_h": r["dh"],
                    "registrados_dgp_m": r["dm"],
                    "programa_antiguo": r["pa"] if r["pa"] else None,
                    "programa_nuevo": r["pn"] if r["pn"] else None,
                }
                if r["pa"]:
                    _, created = TituladosHistoricos.objects.update_or_create(
                        anio_ingreso=r["ai"], anio_egreso=r["ae"], programa_antiguo=r["pa"],
                        defaults=defaults
                    )
                else:
                    _, created = TituladosHistoricos.objects.update_or_create(
                        anio_ingreso=r["ai"], anio_egreso=r["ae"], programa_nuevo=r["pn"],
                        defaults=defaults
                    )
                if created:
                    creados += 1
                else:
                    actualizados += 1

        messages.success(
            request,
            f"✅ Listo: {creados} creados, {actualizados} actualizados. (Filas procesadas: {len(filas_ok)})"
        )
        return redirect('titulados_historicos')

    # ========= Render =========
    return render(request, 'titulados_historicos.html', {
        'registros': registros_page,               # Page object para tabla
        'anios': anios,
        'programas_antiguos': programas_antiguos,
        'programas_nuevos': programas_nuevos,
        'datos_json': datos_json,                  # lista Python; usa json_script en el template
        'paginator': paginator,
        'page_obj': registros_page,
    })


def descargar_plantilla_titulados_historicos(request):
    """
    Genera un Excel con:
      - Hoja TituladosHistoricos (datos existentes)
      - Hoja Instrucciones
      - Hoja CatalogoProgramas
    """
    qs = (
        TituladosHistoricos.objects
        .select_related("programa_antiguo", "programa_nuevo")
        .order_by("anio_ingreso", "anio_egreso", "programa_antiguo__id", "programa_nuevo__id")
    )

    rows = []
    for r in qs:
        if r.programa_antiguo:
            tipo, pid, pnom = "ANTIGUO", r.programa_antiguo.id, r.programa_antiguo.nombre
        else:
            tipo, pid, pnom = "NUEVO", (r.programa_nuevo.id if r.programa_nuevo else ""), (
                r.programa_nuevo.nombre if r.programa_nuevo else ""
            )
        rows.append({
            "programa_tipo": tipo,
            "programa_id": pid,
            "programa_nombre": pnom,
            "anio_ingreso": r.anio_ingreso,
            "anio_egreso": r.anio_egreso,
            "titulados_hombres": r.titulados_hombres,
            "titulados_mujeres": r.titulados_mujeres,
            "registrados_dgp_h": r.registrados_dgp_h,
            "registrados_dgp_m": r.registrados_dgp_m,
        })

    df = pd.DataFrame(rows, columns=TH_COLS_STD) if rows else pd.DataFrame(columns=TH_COLS_STD)

    # Hoja de instrucciones
    info = [
        ["Columna", "Descripción", "Obligatorio", "Ejemplo/Valores"],
        ["programa_tipo", "Tipo de programa", "Sí", "ANTIGUO | NUEVO"],
        ["programa_id", "PK texto del programa", "Sí", "ISC, IM, ..."],
        ["programa_nombre", "Informativo", "No", "Ingeniería ..."],
        ["anio_ingreso", "Año ingreso (1990–2100)", "Sí", "2018"],
        ["anio_egreso", "Entre ingreso y +10 años", "Sí", "2021"],
        ["titulados_hombres", "Entero ≥ 0", "Sí", "40"],
        ["titulados_mujeres", "Entero ≥ 0", "Sí", "35"],
        ["registrados_dgp_h", "Entero ≥ 0", "Sí", "30"],
        ["registrados_dgp_m", "Entero ≥ 0", "Sí", "28"],
    ]
    df_info = pd.DataFrame(info[1:], columns=info[0])

    # Catálogo de programas
    cat = [{"tipo": "ANTIGUO", "programa_id": p.id, "programa_nombre": p.nombre}
           for p in ProgramaEducativoAntiguo.objects.all()]
    cat += [{"tipo": "NUEVO", "programa_id": p.id, "programa_nombre": p.nombre}
            for p in ProgramaEducativoNuevo.objects.all()]
    df_cat = pd.DataFrame(cat, columns=["tipo", "programa_id", "programa_nombre"])

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="TituladosHistoricos")
        df_info.to_excel(w, index=False, sheet_name="Instrucciones")
        df_cat.to_excel(w, index=False, sheet_name="CatalogoProgramas")
    buf.seek(0)

    resp = HttpResponse(
        buf.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    resp["Content-Disposition"] = 'attachment; filename="titulados_historicos.xlsx"'
    return resp


def exportar_titulados_csv(request):
    """
    Exporta a CSV los registros con los **mismos filtros** aplicados.
    Agrega en urls.py: path('administrador/titulados-historicos/exportar-csv/', exportar_titulados_csv, name='exportar_titulados_csv')
    """
    qs = (
        TituladosHistoricos.objects
        .select_related('programa_antiguo', 'programa_nuevo')
        .order_by('anio_ingreso', 'anio_egreso', 'programa_antiguo__id', 'programa_nuevo__id')
    )
    qs = _apply_filters(request, qs)

    resp = HttpResponse(content_type='text/csv; charset=utf-8')
    resp['Content-Disposition'] = 'attachment; filename="titulados_historicos_filtrado.csv"'
    writer = csv.writer(resp)
    writer.writerow(["Programa", "Año ingreso", "Año egreso", "Tit H", "Tit M",
                     "DGP H", "DGP M", "Total Tit", "Total DGP"])
    for r in qs:
        prog = r.programa_antiguo.nombre if r.programa_antiguo else (
            r.programa_nuevo.nombre if r.programa_nuevo else "SIN PROGRAMA"
        )
        writer.writerow([
            smart_str(prog),
            r.anio_ingreso,
            r.anio_egreso,
            r.titulados_hombres,
            r.titulados_mujeres,
            r.registrados_dgp_h,
            r.registrados_dgp_m,
            r.titulados_hombres + r.titulados_mujeres,
            r.registrados_dgp_h + r.registrados_dgp_m
        ])
    return resp
