# api/home/examen_usuario_view.py

from django.shortcuts import render
from api.models import (
    CicloPeriodo, ProgramaEducativoAntiguo, ProgramaEducativoNuevo, NuevoIngreso
)
from django.db.models import Sum

def examen_admision_usuario_view(request):
    programas_antiguos = ProgramaEducativoAntiguo.objects.all()
    programas_nuevos = ProgramaEducativoNuevo.objects.all()

    ciclos_periodos = CicloPeriodo.objects.select_related('ciclo', 'periodo')
    opciones_ciclo = sorted(
        [f"{cp.ciclo.anio} - {cp.periodo.clave}" for cp in ciclos_periodos],
        reverse=True
    )

    datos_graficas = {}
    detalle_programas = []

    filtro = request.GET.get("filtro_anio")
    if filtro and filtro != "Todos":
        try:
            anio_str, periodo_clave = filtro.split(" - ")
            ciclo_periodo = CicloPeriodo.objects.get(
                ciclo__anio=anio_str, periodo__clave=periodo_clave
            )

            datos = NuevoIngreso.objects.filter(ciclo_periodo=ciclo_periodo).aggregate(
                examen=Sum('examen'),
                renoes=Sum('renoes'),
                uaem_gem=Sum('uaem_gem'),
                pase_directo=Sum('pase_directo')
            )
            if any(datos.values()):
                datos_graficas = datos

            registros = NuevoIngreso.objects.filter(ciclo_periodo=ciclo_periodo).select_related('programa_antiguo', 'programa_nuevo')
            for r in registros:
                nombre_programa = r.programa_antiguo.nombre if r.programa_antiguo else r.programa_nuevo.nombre
                detalle_programas.append({
                    'programa': nombre_programa,
                    'examen': r.examen,
                    'renoes': r.renoes,
                    'uaem_gem': r.uaem_gem,
                    'pase_directo': r.pase_directo
                })
        except CicloPeriodo.DoesNotExist:
            pass

    return render(request, 'examen_admision_usuario.html', {
        'anios': opciones_ciclo,
        'datos_graficas': datos_graficas,
        'detalle_programas': detalle_programas,
        'programas_antiguos': programas_antiguos,
        'programas_nuevos': programas_nuevos
    })
