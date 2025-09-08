from django.shortcuts import render
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db import transaction
import json
from datetime import date

from api.models import (
    GeneracionCarrera,
    ProgramaEducativoAntiguo,
    ProgramaEducativoNuevo,
)

def _ym_to_date(ym: str) -> date | None:
    if not ym:
        return None
    try:
        y, m = ym.split("-")
        return date(int(y), int(m), 1)
    except Exception:
        return None

def _prog_name(g: GeneracionCarrera) -> str:
    if g.programa_antiguo_id:
        try:
            return g.programa_antiguo.nombre
        except ProgramaEducativoAntiguo.DoesNotExist:
            return g.programa_antiguo_id
    if g.programa_nuevo_id:
        try:
            return g.programa_nuevo.nombre
        except ProgramaEducativoNuevo.DoesNotExist:
            return g.programa_nuevo_id
    return ""

@login_required
def tit_his_view(request):
    carreras_antiguas = list(
        ProgramaEducativoAntiguo.objects.values("id", "nombre").order_by("nombre")
    )
    carreras_nuevas = list(
        ProgramaEducativoNuevo.objects.values("id", "nombre").order_by("nombre")
    )

    generaciones = GeneracionCarrera.objects.select_related(
        "programa_antiguo", "programa_nuevo"
    ).order_by("fecha_ingreso", "programa_antiguo__nombre", "programa_nuevo__nombre")

    generaciones_json = [
        {
            "programa": _prog_name(g),
            "anio": g.fecha_ingreso.year if g.fecha_ingreso else None,
            "tasa": g.tasa_titulacion,
        }
        for g in generaciones
    ]

    return render(
        request,
        "tit_his.html",
        {
            "page_title": "Titulados – Histórico (CRUD)",
            "generaciones": generaciones,
            "generaciones_json": json.dumps(generaciones_json, ensure_ascii=False),
            "carreras_antiguas": json.dumps(carreras_antiguas, ensure_ascii=False),
            "carreras_nuevas": json.dumps(carreras_nuevas, ensure_ascii=False),
        },
    )

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def tit_his_api(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("JSON inválido")

    items = payload.get("items", [])
    delete_ids = payload.get("delete_ids", [])

    if not isinstance(items, list):
        return HttpResponseBadRequest("Formato inválido: 'items' debe ser lista")
    if not isinstance(delete_ids, list):
        return HttpResponseBadRequest("Formato inválido: 'delete_ids' debe ser lista")

    guardados = []
    eliminados = 0

    with transaction.atomic():
        # Borrados SOLO si el usuario es staff (para minimizar riesgos)
        if request.user.is_staff and delete_ids:
            qs = GeneracionCarrera.objects.filter(pk__in=delete_ids)
            eliminados = qs.count()
            qs.delete()

        for it in items:
            pk = it.get("id")
            tipo = (it.get("tipo") or "").lower()
            programa_id = it.get("programa_id") or ""

            fi = _ym_to_date(it.get("fi"))
            fe = _ym_to_date(it.get("fe"))

            n = lambda k: int(it.get(k) or 0)
            ih, im = n("ih"), n("im")
            ch, cm = n("ch"), n("cm")
            rh, rm = n("rh"), n("rm")
            th, tm = n("th"), n("tm")
            dh, dm = n("dh"), n("dm")

            if tipo not in ("antiguo", "nuevo") or not programa_id:
                continue

            obj = GeneracionCarrera.objects.filter(pk=pk).first() if pk else GeneracionCarrera()

            if tipo == "antiguo":
                obj.programa_antiguo_id = programa_id
                obj.programa_nuevo = None
            else:
                obj.programa_nuevo_id = programa_id
                obj.programa_antiguo = None

            if fi: obj.fecha_ingreso = fi
            if fe: obj.fecha_egreso = fe

            obj.ingreso_hombres = ih
            obj.ingreso_mujeres = im
            obj.egresados_cohorte_h = ch
            obj.egresados_cohorte_m = cm
            obj.egresados_rezagados_h = rh
            obj.egresados_rezagados_m = rm
            obj.titulados_h = th
            obj.titulados_m = tm
            obj.registrados_dgp_h = dh
            obj.registrados_dgp_m = dm

            obj.save()
            guardados.append(obj.pk)

    return JsonResponse({"ok": True, "guardados": guardados, "eliminados": eliminados})
