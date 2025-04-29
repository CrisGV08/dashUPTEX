from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.http import urlencode
from api.models import (
    CicloEscolar, Periodo, CicloPeriodo,
    ProgramaEducativoAntiguo, ProgramaEducativoNuevo, NuevoIngreso
)
from django.db.models import Sum

def examen_admision_view(request):
    mensaje = request.GET.get("mensaje")

    if request.method == 'POST' and 'crear_ciclo' in request.POST:
        periodos_definidos = [
            ('E-A', 'Enero - Abril'),
            ('M-A', 'Mayo - Agosto'),
            ('S-D', 'Septiembre - Diciembre')
        ]

        ultimo_ciclo = CicloEscolar.objects.order_by('-anio').first()
        anio_actual = int(ultimo_ciclo.anio) if ultimo_ciclo else 2025

        ciclo_actual, _ = CicloEscolar.objects.get_or_create(anio=anio_actual)
        periodos_actuales = CicloPeriodo.objects.filter(
            ciclo=ciclo_actual
        ).values_list('periodo__clave', flat=True)

        siguiente_periodo = None
        for clave, nombre in periodos_definidos:
            if clave not in periodos_actuales:
                siguiente_periodo = (clave, nombre)
                break

        if siguiente_periodo:
            clave, nombre = siguiente_periodo
            periodo, _ = Periodo.objects.get_or_create(clave=clave, defaults={'nombre': nombre})
            CicloPeriodo.objects.get_or_create(ciclo=ciclo_actual, periodo=periodo)
            mensaje_creado = f"✅ Se creó el ciclo {ciclo_actual.anio} periodo {nombre}"
        else:
            nuevo_anio = anio_actual + 1
            nuevo_ciclo, _ = CicloEscolar.objects.get_or_create(anio=nuevo_anio)
            clave, nombre = periodos_definidos[0]
            periodo, _ = Periodo.objects.get_or_create(clave=clave, defaults={'nombre': nombre})
            CicloPeriodo.objects.get_or_create(ciclo=nuevo_ciclo, periodo=periodo)
            mensaje_creado = f"✅ Se creó el ciclo {nuevo_anio} periodo {nombre}"

        # 🔥 Redirigimos y preservamos el filtro si existe
        filtro_anio = request.GET.get('filtro_anio', '')
        params = {'mensaje': mensaje_creado}
        if filtro_anio:
            params['filtro_anio'] = filtro_anio

        query_string = urlencode(params)
        url = reverse('examen_admision')
        return redirect(f"{url}?{query_string}")

    # Lo demás sigue igual
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
            ciclo_periodo = CicloPeriodo.objects.select_related("ciclo", "periodo").get(
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

            registros = NuevoIngreso.objects.select_related('programa_antiguo', 'programa_nuevo').filter(
                ciclo_periodo=ciclo_periodo
            )

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

    return render(request, 'examen_admision.html', {
        'mensaje': mensaje,
        'programas_antiguos': programas_antiguos,
        'programas_nuevos': programas_nuevos,
        'anios': opciones_ciclo,
        'datos_graficas': datos_graficas,
        'detalle_programas': detalle_programas
    })
