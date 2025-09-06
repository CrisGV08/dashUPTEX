# api/home/views.py
import json
from django.shortcuts import render
from api.models import AprovechamientoAcademico

def aprovechamiento_usuario_view(request):
    """
    Vista de usuario: usa EXACTAMENTE el mismo dataset que Admin (AprovechamientoAcademico)
    y construye los filtros a partir de los datos reales. No depende de json_script.
    """
    qs = (AprovechamientoAcademico.objects
          .select_related('ciclo_periodo__ciclo',
                          'ciclo_periodo__periodo',
                          'programa_antiguo', 'programa_nuevo'))

    detalle = []
    for r in qs:
        # Ciclo "YYYY - CLAVE"
        anio  = getattr(getattr(r.ciclo_periodo, 'ciclo',   None), 'anio',  None)
        clave = getattr(getattr(r.ciclo_periodo, 'periodo', None), 'clave', None)
        ciclo = f"{anio} - {clave}" if (anio and clave) else "Sin ciclo"

        # Programa A-<id> / N-<id> / U-<rowid> si no hay relación
        if r.programa_antiguo_id:
            programa_id = f"A-{r.programa_antiguo_id}"
            programa_nombre = r.programa_antiguo.nombre
            programa_tipo = 'A'
        elif r.programa_nuevo_id:
            programa_id = f"N-{r.programa_nuevo_id}"
            programa_nombre = r.programa_nuevo.nombre
            programa_tipo = 'N'
        else:
            programa_id = f"U-{r.id}"
            programa_nombre = "Programa sin nombre"
            programa_tipo = 'U'

        detalle.append({
            "ciclo": ciclo,
            "programa_id": programa_id,
            "programa_tipo": programa_tipo,   # A / N / U
            "programa": programa_nombre,
            "promedio": None if r.promedio is None else float(r.promedio),
        })

    # Filtros desde el MISMO dataset
    order_map = {'E-A': 3, 'M-A': 2, 'S-D': 1}
    ciclos = sorted(
        {d["ciclo"] for d in detalle if d["ciclo"] != "Sin ciclo"},
        key=lambda s: (int(s.split(' - ')[0]), order_map.get(s.split(' - ')[1], 0)),
        reverse=True
    )

    # Programas únicos por tipo (A/N) presentes en los datos
    vistos = set()
    progs_A, progs_N = [], []
    for d in detalle:
        pid = d["programa_id"]
        if pid in vistos:
            continue
        vistos.add(pid)
        item = {"id": pid, "nombre": d["programa"]}
        if d["programa_tipo"] == 'A':
            progs_A.append(item)
        elif d["programa_tipo"] == 'N':
            progs_N.append(item)
        # Los 'U' no se listan en checkboxes
    progs_A.sort(key=lambda x: x["nombre"].lower())
    progs_N.sort(key=lambda x: x["nombre"].lower())

    ctx = {
        "anios": ciclos,
        "programas_antiguos": progs_A,
        "programas_nuevos": progs_N,
        "detalle_ciclos": detalle,                                # tabla inicial
        "datos_graficas_json": json.dumps(detalle, ensure_ascii=False),  # para JS
    }
    return render(request, "aprovechamiento_usuario.html", ctx)
