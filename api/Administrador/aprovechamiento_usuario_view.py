# api/home/views.py  (o donde tengas tus vistas)
import json
from django.shortcuts import render
from api.models import (
    CicloPeriodo,
    AprovechamientoAcademico,
    ProgramaEducativoAntiguo,
    ProgramaEducativoNuevo,
)

def aprovechamiento_usuario_view(request):
    """
    Vista de usuario (solo consulta):
    - Envía ciclos en formato 'Año - Periodo' (p. ej. '2025 - E-A')
    - Envía Programas Educativos (Nuevos y Antiguos) para que el template los pinte
    - Envía el dataset plano para filtrado en el cliente
    """

    # === Ciclos: 'Año - Periodo' únicos y ordenados (año desc, periodo E-A > M-A > S-D) ===
    order_map = {'E-A': 3, 'M-A': 2, 'S-D': 1}
    ciclos_qs = (CicloPeriodo.objects
                 .select_related('ciclo', 'periodo')
                 .values('ciclo__anio', 'periodo__clave'))

    ciclos_unicos = {
        f"{c['ciclo__anio']} - {c['periodo__clave']}"
        for c in ciclos_qs
    }
    anios = sorted(
        ciclos_unicos,
        key=lambda s: (
            int(s.split(' - ')[0]),                      # año
            order_map.get(s.split(' - ')[1], 0)          # orden de periodo
        ),
        reverse=True
    )

    # === Programas educativos (para mostrar los checkboxes) ===
    programas_antiguos = ProgramaEducativoAntiguo.objects.all().order_by('nombre')
    programas_nuevos = ProgramaEducativoNuevo.objects.all().order_by('nombre')

    # === Registros completos (sin filtrar en backend) ===
    registros = (AprovechamientoAcademico.objects
                 .select_related('ciclo_periodo__ciclo', 'ciclo_periodo__periodo',
                                 'programa_antiguo', 'programa_nuevo'))

    detalle = []
    for r in registros:
        if r.programa_antiguo_id:
            programa_id = f"A-{r.programa_antiguo_id}"
            programa_nombre = f"{r.programa_antiguo.nombre} (Antiguo)"
        else:
            programa_id = f"N-{r.programa_nuevo_id}"
            programa_nombre = f"{r.programa_nuevo.nombre} (Nuevo)"

        detalle.append({
            "ciclo": str(r.ciclo_periodo),      # ej. "2025 - E-A"
            "programa_id": programa_id,         # ej. "A-12" o "N-5"
            "programa": programa_nombre,
            "promedio": float(r.promedio),
        })

    ctx = {
        "anios": anios,                                   # ahora sí: "Año - Periodo"
        "programas_antiguos": programas_antiguos,         # se pintan en el template
        "programas_nuevos": programas_nuevos,             # se pintan en el template
        "detalle_ciclos": detalle,
        "datos_graficas": json.dumps(detalle),            # lo usa el JS para filtrar
    }
    return render(request, "aprovechamiento_usuario.html", ctx)
