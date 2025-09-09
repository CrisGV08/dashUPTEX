import json, calendar
from datetime import date
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_GET
from django.db.models import Q, F, Sum

from api.models import (
    TituladosTSUIng,
    ProgramaEducativoAntiguo,
    ProgramaEducativoNuevo,
)

# ---------- PAGE ----------
def titulados_tsu_inge_view(request):
    # template en api/templates/titulados_tsu_inge.html
    return render(request, "titulados_tsu_inge.html", {})


# ---------- PROGRAMAS ----------
@require_GET
def tsui_programas_api(request):
    """
    ?tipo=antiguo|nuevo
    """
    t = (request.GET.get("tipo") or "").lower()
    if t == "antiguo":
        items = list(ProgramaEducativoAntiguo.objects.values("id", "nombre").order_by("nombre"))
    elif t == "nuevo":
        items = list(ProgramaEducativoNuevo.objects.values("id", "nombre").order_by("nombre"))
    else:
        items = []
    return JsonResponse({"ok": True, "items": items})


# ---------- LISTADO con filtros ----------
@require_GET
def tsui_api(request):
    qs = TituladosTSUIng.objects.all()

    # Filtros
    nivel = request.GET.get("nivel")  # 'TSU' | 'ING' | 'TODOS'
    if nivel in ("TSU", "ING"):
        qs = qs.filter(nivel=nivel)

    prog_tipo = request.GET.get("prog_tipo")  # 'antiguo' | 'nuevo'
    if prog_tipo == "antiguo":
        qs = qs.filter(programa_antiguo__isnull=False)
    elif prog_tipo == "nuevo":
        qs = qs.filter(programa_nuevo__isnull=False)

    programa_id = request.GET.get("programa")  # id del programa
    if programa_id:
        qs = qs.filter(Q(programa_antiguo_id=programa_id) | Q(programa_nuevo_id=programa_id))

    anio_ing = request.GET.get("anio_ing")  # exacto
    anio_egr = request.GET.get("anio_egr")
    if anio_ing:
        qs = qs.filter(fecha_ingreso__year=int(anio_ing))
    if anio_egr:
        qs = qs.filter(fecha_egreso__year=int(anio_egr))

    qs = qs.order_by("fecha_ingreso", "nivel")

    items = []
    for r in qs:
        items.append({
            "id": r.id,
            "nivel": r.nivel,
            "programa": r.programa_nombre(),
            "programa_id": r.programa_id(),
            "prog_tipo": "antiguo" if r.programa_antiguo_id else "nuevo",
            "ingreso": r.fecha_ingreso.strftime("%m-%Y"),
            "egreso": r.fecha_egreso.strftime("%m-%Y"),
            "ing_h": r.ingreso_hombres,
            "ing_m": r.ingreso_mujeres,
            "eg_coh_h": r.egresados_cohorte_h,
            "eg_coh_m": r.egresados_cohorte_m,
            "eg_rez_h": r.egresados_rezagados_h,
            "eg_rez_m": r.egresados_rezagados_m,
            "tit_h": r.titulados_h,
            "tit_m": r.titulados_m,
            "dgp_h": r.registrados_dgp_h,
            "dgp_m": r.registrados_dgp_m,
            "tasa": r.tasa_titulacion,
        })

    # Agregado para la gráfica (tasa por nivel)
    agg = (
        qs.values("nivel")
          .annotate(ing=Sum(F("ingreso_hombres") + F("ingreso_mujeres")),
                    tit=Sum(F("titulados_h") + F("titulados_m")))
    )
    tasas = {"TSU": 0.0, "ING": 0.0}
    for a in agg:
        ing = a["ing"] or 0
        tit = a["tit"] or 0
        tasas[a["nivel"]] = round((tit / ing) * 100, 2) if ing else 0.0

    return JsonResponse({"ok": True, "items": items, "tasas": tasas})


# ---------- CREAR ----------
@require_http_methods(["POST"])
def tsui_create(request):
    try:
        data = json.loads(request.body.decode('utf-8'))

        nivel = data["nivel"]                # 'TSU' | 'ING'
        prog_tipo = data["prog_tipo"]        # 'antiguo' | 'nuevo'
        programa_id = data["programa"]       # pk del programa

        anio_ing = int(data["anio_ing"]);  mes_ing = int(data["mes_ing"])
        anio_egr = int(data["anio_egr"]);  mes_egr = int(data["mes_egr"])

        last_day = calendar.monthrange(anio_egr, mes_egr)[1]
        fecha_ing = date(anio_ing, mes_ing, 1)
        fecha_egr = date(anio_egr, mes_egr, last_day)

        kwargs = dict(
            nivel=nivel,
            fecha_ingreso=fecha_ing,
            fecha_egreso=fecha_egr,

            ingreso_hombres=int(data.get("ing_h", 0)),
            ingreso_mujeres=int(data.get("ing_m", 0)),

            egresados_cohorte_h=int(data.get("eg_coh_h", 0)),
            egresados_cohorte_m=int(data.get("eg_coh_m", 0)),

            egresados_rezagados_h=int(data.get("eg_rez_h", 0)),
            egresados_rezagados_m=int(data.get("eg_rez_m", 0)),

            titulados_h=int(data.get("tit_h", 0)),
            titulados_m=int(data.get("tit_m", 0)),

            registrados_dgp_h=int(data.get("dgp_h", 0)),
            registrados_dgp_m=int(data.get("dgp_m", 0)),
        )

        if prog_tipo == "antiguo":
            kwargs["programa_antiguo"] = ProgramaEducativoAntiguo.objects.get(pk=programa_id)
        elif prog_tipo == "nuevo":
            kwargs["programa_nuevo"] = ProgramaEducativoNuevo.objects.get(pk=programa_id)
        else:
            return JsonResponse({"ok": False, "error": "prog_tipo inválido (antiguo|nuevo)."}, status=400)

        obj = TituladosTSUIng.objects.create(**kwargs)
        return JsonResponse({"ok": True, "id": obj.id})

    except (KeyError, ValueError) as e:
        return JsonResponse({"ok": False, "error": f"Payload inválido: {e}"}, status=400)
    except (ProgramaEducativoAntiguo.DoesNotExist, ProgramaEducativoNuevo.DoesNotExist):
        return JsonResponse({"ok": False, "error": "Programa no encontrado."}, status=404)
    except Exception as e:
        return JsonResponse({"ok": False, "error": "No se pudo guardar.", "detail": str(e)}, status=400)


# ---------- UPDATE / DELETE ----------
@require_http_methods(["PUT", "PATCH", "DELETE"])
def tsui_update_delete(request, pk: int):
    try:
        obj = TituladosTSUIng.objects.get(pk=pk)
    except TituladosTSUIng.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Registro no encontrado."}, status=404)

    if request.method == "DELETE":
        obj.delete()
        return JsonResponse({"ok": True})

    # PUT/PATCH
    try:
        data = json.loads(request.body.decode('utf-8'))

        if "nivel" in data:
            obj.nivel = data["nivel"]

        if "prog_tipo" in data and "programa" in data:
            if data["prog_tipo"] == "antiguo":
                obj.programa_nuevo = None
                obj.programa_antiguo = ProgramaEducativoAntiguo.objects.get(pk=data["programa"])
            elif data["prog_tipo"] == "nuevo":
                obj.programa_antiguo = None
                obj.programa_nuevo = ProgramaEducativoNuevo.objects.get(pk=data["programa"])

        # Fechas
        if {"anio_ing", "mes_ing"} <= data.keys():
            obj.fecha_ingreso = date(int(data["anio_ing"]), int(data["mes_ing"]), 1)
        if {"anio_egr", "mes_egr"} <= data.keys():
            ld = calendar.monthrange(int(data["anio_egr"]), int(data["mes_egr"]))[1]
            obj.fecha_egreso = date(int(data["anio_egr"]), int(data["mes_egr"]), ld)

        # Campos numéricos (si vienen)
        for fld in ["ingreso_hombres","ingreso_mujeres","egresados_cohorte_h","egresados_cohorte_m",
                    "egresados_rezagados_h","egresados_rezagados_m","titulados_h","titulados_m",
                    "registrados_dgp_h","registrados_dgp_m"]:
            if fld in data:
                setattr(obj, fld, int(data[fld]))

        obj.full_clean()
        obj.save()
        return JsonResponse({"ok": True})
    except Exception as e:
        return JsonResponse({"ok": False, "error": "No se pudo actualizar.", "detail": str(e)}, status=400)
