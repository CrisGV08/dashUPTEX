# api/Administrador/titulados_historicos_view.py
import io
import pandas as pd
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, F, ExpressionWrapper, IntegerField

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

# ========= Helpers =========
def _i(x):
    try:
        return max(0, int(float(x)))
    except Exception:
        return 0

def _y(x):
    try:
        return int(float(x))
    except Exception:
        return 0

def _norm(x):
    return (str(x).strip() if x is not None else "")

def _apply_filters(request, qs):
    """Aplica filtros GET al queryset (sin modalidad)."""
    anios = request.GET.getlist("anio") or request.GET.getlist("anios")
    tipo  = request.GET.get("tipo_programa")  # 'antiguo' | 'nuevo' | None
    programas = request.GET.getlist("programa") or request.GET.getlist("programas")
    buscar = request.GET.get("buscar", "").strip()

    ingreso_min = request.GET.get("ingreso_min")
    ingreso_max = request.GET.get("ingreso_max")
    egreso_min  = request.GET.get("egreso_min")
    egreso_max  = request.GET.get("egreso_max")
    tit_min = request.GET.get("titulados_min")
    tit_max = request.GET.get("titulados_max")
    dgp_min = request.GET.get("dgp_min")
    dgp_max = request.GET.get("dgp_max")

    if anios:
        anios_int = []
        for a in anios:
            try:
                anios_int.append(int(a))
            except:
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

    if ingreso_min: qs = qs.filter(anio_ingreso__gte=_y(ingreso_min))
    if ingreso_max: qs = qs.filter(anio_ingreso__lte=_y(ingreso_max))
    if egreso_min:  qs = qs.filter(anio_egreso__gte=_y(egreso_min))
    if egreso_max:  qs = qs.filter(anio_egreso__lte=_y(egreso_max))

    tot_tit = ExpressionWrapper(F("titulados_hombres") + F("titulados_mujeres"), output_field=IntegerField())
    tot_dgp = ExpressionWrapper(F("registrados_dgp_h") + F("registrados_dgp_m"), output_field=IntegerField())
    qs = qs.annotate(_tot_titulados=tot_tit, _tot_dgp=tot_dgp)

    if tit_min: qs = qs.filter(_tot_titulados__gte=_i(tit_min))
    if tit_max: qs = qs.filter(_tot_titulados__lte=_i(tit_max))
    if dgp_min: qs = qs.filter(_tot_dgp__gte=_i(dgp_min))
    if dgp_max: qs = qs.filter(_tot_dgp__lte=_i(dgp_max))

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
    if pa: return "ANTIGUO", pa.id, pa, None
    pn = ProgramaEducativoNuevo.objects.filter(pk=key).first()
    if pn: return "NUEVO", pn.id, None, pn
    # luego por nombre (exacto case-insensitive)
    pa = ProgramaEducativoAntiguo.objects.filter(nombre__iexact=val).first()
    if pa: return "ANTIGUO", pa.id, pa, None
    pn = ProgramaEducativoNuevo.objects.filter(nombre__iexact=val).first()
    if pn: return "NUEVO", pn.id, None, pn
    return None, None, None, None

# ========= Vistas =========
def titulados_historicos_view(request):
    qs = (
        TituladosHistoricos.objects
        .select_related('programa_antiguo', 'programa_nuevo')
        .order_by('anio_ingreso', 'anio_egreso', 'programa_antiguo__id', 'programa_nuevo__id')
    )

    # Filtros server-side (sin modalidad)
    qs = _apply_filters(request, qs)

    # Catálogos para UI
    anios = (
        TituladosHistoricos.objects
        .values_list('anio_ingreso', flat=True).distinct().order_by('anio_ingreso')
    )
    programas_antiguos = ProgramaEducativoAntiguo.objects.all()
    programas_nuevos = ProgramaEducativoNuevo.objects.all()

    # JSON para gráficas (lista Python; NO json.dumps)
    datos_json = [
        {
            "programa": (
                r.programa_antiguo.nombre if r.programa_antiguo
                else r.programa_nuevo.nombre if r.programa_nuevo
                else "SIN PROGRAMA"
            ),
            "anio_ingreso": r.anio_ingreso,
            "anio_egreso": r.anio_egreso,
            "titulados_h": r.titulados_hombres,
            "titulados_m": r.titulados_mujeres,
            "dgp_h": r.registrados_dgp_h,
            "dgp_m": r.registrados_dgp_m,
            "total_titulados": r.titulados_hombres + r.titulados_mujeres,
            "total_dgp": r.registrados_dgp_h + r.registrados_dgp_m,
        }
        for r in qs
    ]

    # ============= Carga de Excel (POST al mismo endpoint) =============
    if request.method == 'POST' and request.FILES.get('archivo_excel'):
        archivo_excel = request.FILES['archivo_excel']
        try:
            df = pd.read_excel(archivo_excel, engine="openpyxl")
        except Exception as e:
            messages.error(request, f"❌ Error al leer el archivo Excel: {e}")
            return redirect('titulados_historicos')

        cols = set(df.columns.astype(str))
        modo_std    = all(c in cols for c in TH_COLS_STD)
        modo_legacy = all(c in cols for c in TH_COLS_LEGACY)

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
            df = df[TH_COLS_STD].copy()
            df["programa_tipo"] = df["programa_tipo"].astype(str).str.upper().str.strip()
            df["programa_id"]   = df["programa_id"].astype(str).str.strip()
            for c in ["anio_ingreso","anio_egreso"]:
                df[c] = df[c].apply(_y)
            for c in ["titulados_hombres","titulados_mujeres","registrados_dgp_h","registrados_dgp_m"]:
                df[c] = df[c].apply(_i)

            for i, r in df.iterrows():
                ix = i + 2
                tipo, pid = r["programa_tipo"], r["programa_id"]
                ai, ae = r["anio_ingreso"], r["anio_egreso"]
                th, tm, dh, dm = r["titulados_hombres"], r["titulados_mujeres"], r["registrados_dgp_h"], r["registrados_dgp_m"]

                if tipo not in ("ANTIGUO","NUEVO"):
                    add_err(ix, "programa_tipo debe ser 'ANTIGUO' o 'NUEVO'."); continue
                if not pid:
                    add_err(ix, "programa_id vacío."); continue
                if not (1990 <= ai <= 2100):
                    add_err(ix, f"año ingreso fuera de rango (1990–2100): {ai}."); continue
                if not (ai <= ae <= ai + 10):
                    add_err(ix, f"año egreso debe estar entre {ai} y {ai+10}."); continue

                pa, pn = _resolve_program(tipo, pid)
                if not (pa or pn):
                    add_err(ix, f"programa_id '{pid}' no existe en {tipo}."); continue

                clave = (tipo, pid, ai, ae)
                if clave in vistos:
                    add_err(ix, f"Duplicado en archivo (tipo,id,ingreso,egreso)=({tipo},{pid},{ai},{ae})."); continue
                vistos.add(clave)

                filas_ok.append({"pa": pa, "pn": pn, "ai": ai, "ae": ae, "th": th, "tm": tm, "dh": dh, "dm": dm})

        else:  # modo_legacy
            df = df[list(TH_COLS_LEGACY)].copy()
            df.rename(columns={
                "PROGRAMA EDUCATIVO":"prog",
                "AÑO INGRESO":"ai",
                "AÑO EGRESO":"ae",
                "TITULADOS H":"th",
                "TITULADOS M":"tm",
                "REG DGP H":"dh",
                "REG DGP M":"dm",
            }, inplace=True)
            df["ai"] = df["ai"].apply(_y)
            df["ae"] = df["ae"].apply(_y)
            for c in ["th","tm","dh","dm"]:
                df[c] = df[c].apply(_i)

            for i, r in df.iterrows():
                ix = i + 2
                tipo, pid, pa, pn = _resolve_program_from_legacy(r["prog"])
                ai, ae, th, tm, dh, dm = r["ai"], r["ae"], r["th"], r["tm"], r["dh"], r["dm"]

                if not (pa or pn):
                    add_err(ix, f"Programa '{r['prog']}' no encontrado por ID ni por nombre."); continue
                if not (1990 <= ai <= 2100):
                    add_err(ix, f"año ingreso fuera de rango (1990–2100): {ai}."); continue
                if not (ai <= ae <= ai + 10):
                    add_err(ix, f"año egreso debe estar entre {ai} y {ai+10}."); continue

                clave = (tipo, pid, ai, ae)
                if clave in vistos:
                    add_err(ix, f"Duplicado en archivo (tipo,id,ingreso,egreso)=({tipo},{pid},{ai},{ae})."); continue
                vistos.add(clave)

                filas_ok.append({"pa": pa, "pn": pn, "ai": ai, "ae": ae, "th": th, "tm": tm, "dh": dh, "dm": dm})

        if errores:
            for e in errores[:20]:
                messages.error(request, e)
            if len(errores) > 20:
                messages.error(request, f"…y {len(errores)-20} error(es) más.")
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
                if created: creados += 1
                else: actualizados += 1

        messages.success(request, f"✅ Listo: {creados} creados, {actualizados} actualizados. (Filas: {len(filas_ok)})")
        return redirect('titulados_historicos')

    # ========= Render =========
    return render(request, 'titulados_historicos.html', {
        'registros': qs,
        'anios': anios,
        'programas_antiguos': programas_antiguos,
        'programas_nuevos': programas_nuevos,
        'datos_json': datos_json,  # <-- lista Python, se serializa en el template con json_script
    })


def descargar_plantilla_titulados_historicos(request):
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
            tipo, pid, pnom = "NUEVO", (r.programa_nuevo.id if r.programa_nuevo else ""), (r.programa_nuevo.nombre if r.programa_nuevo else "")
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
        ["Columna","Descripción","Obligatorio","Ejemplo/Valores"],
        ["programa_tipo","Tipo de programa","Sí","ANTIGUO | NUEVO"],
        ["programa_id","PK texto del programa","Sí","ISC, IM, ..."],
        ["programa_nombre","Informativo","No","Ingeniería ..."],
        ["anio_ingreso","Año ingreso (1990–2100)","Sí","2018"],
        ["anio_egreso","Entre ingreso y +10 años","Sí","2021"],
        ["titulados_hombres","Entero ≥ 0","Sí","40"],
        ["titulados_mujeres","Entero ≥ 0","Sí","35"],
        ["registrados_dgp_h","Entero ≥ 0","Sí","30"],
        ["registrados_dgp_m","Entero ≥ 0","Sí","28"],
    ]
    df_info = pd.DataFrame(info[1:], columns=info[0])

    # Catálogo de programas
    cat = [{"tipo":"ANTIGUO","programa_id":p.id,"programa_nombre":p.nombre} for p in ProgramaEducativoAntiguo.objects.all()]
    cat += [{"tipo":"NUEVO","programa_id":p.id,"programa_nombre":p.nombre} for p in ProgramaEducativoNuevo.objects.all()]
    df_cat = pd.DataFrame(cat, columns=["tipo","programa_id","programa_nombre"])

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
