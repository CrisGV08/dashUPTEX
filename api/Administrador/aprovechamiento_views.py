from django.shortcuts import render, redirect
from api.models import (
    CicloEscolar, Periodo, CicloPeriodo,
    ProgramaEducativoAntiguo, ProgramaEducativoNuevo, AprovechamientoAcademico
)
from django.db.models import Avg
import pandas as pd

def aprovechamiento_view(request):
    mensaje = None

    if request.method == 'POST' and request.FILES.get('excel_file'):
        archivo = request.FILES['excel_file']
        df = pd.read_excel(archivo)
        errores = []

        for i, row in df.iterrows():
            nombre_prog = row['Programa Educativo']
            prog = ProgramaEducativoAntiguo.objects.filter(nombre=nombre_prog).first()
            tipo = 'programa_antiguo'
            if not prog:
                prog = ProgramaEducativoNuevo.objects.filter(nombre=nombre_prog).first()
                tipo = 'programa_nuevo'
            if not prog:
                errores.append(f"Fila {i+2}: Programa no encontrado: {nombre_prog}")
                continue

            for col in df.columns[1:]:
                if pd.isna(row[col]):
                    continue
                try:
                    clave, anio = col.split()
                    ciclo = CicloEscolar.objects.get(anio=int(anio))
                    periodo = Periodo.objects.get(clave=clave)
                    ciclo_periodo = CicloPeriodo.objects.get(ciclo=ciclo, periodo=periodo)

                    AprovechamientoAcademico.objects.update_or_create(
                        ciclo_periodo=ciclo_periodo,
                        **{tipo: prog},
                        defaults={'promedio': row[col]}
                    )
                except Exception as e:
                    errores.append(f"Fila {i+2}, Columna {col}: {str(e)}")

        if errores:
            mensaje = "\u274c Errores encontrados:<br>" + "<br>".join(errores)
        else:
            mensaje = "\u2705 Archivo procesado y datos guardados correctamente."

    programas_antiguos = ProgramaEducativoAntiguo.objects.all()
    programas_nuevos = ProgramaEducativoNuevo.objects.all()

    ciclos_periodos = CicloPeriodo.objects.select_related('ciclo', 'periodo')
    opciones_ciclo = sorted(
        [f"{cp.ciclo.anio} - {cp.periodo.clave}" for cp in ciclos_periodos],
        reverse=True
    )

    detalle_programas = []
    programas = []
    promedios_hist = []
    ciclos = []
    promedios_ciclo = []

    filtro = request.GET.get("filtro_anio")

    registros = AprovechamientoAcademico.objects.select_related(
        'programa_antiguo', 'programa_nuevo', 'ciclo_periodo__ciclo', 'ciclo_periodo__periodo'
    )

    if filtro and filtro != "Todos":
        try:
            anio_str, periodo_clave = filtro.split(" - ")
            registros = registros.filter(
                ciclo_periodo__ciclo__anio=anio_str,
                ciclo_periodo__periodo__clave=periodo_clave
            )
        except:
            pass

    if registros.exists():
        for r in registros:
            nombre_programa = r.programa_antiguo.nombre if r.programa_antiguo else r.programa_nuevo.nombre
            detalle_programas.append({
                'programa': nombre_programa,
                'promedio': float(r.promedio)
            })
            programas.append(nombre_programa)
            promedios_hist.append(float(r.promedio))

        ciclos_distintos = registros.values_list(
            'ciclo_periodo__periodo__clave',
            'ciclo_periodo__ciclo__anio'
        ).distinct()

        ciclos = [f"{clave} {anio}" for clave, anio in ciclos_distintos]

        for clave, anio in ciclos_distintos:
            promedio_ciclo = registros.filter(
                ciclo_periodo__periodo__clave=clave,
                ciclo_periodo__ciclo__anio=anio
            ).aggregate(avg=Avg('promedio'))['avg'] or 0
            promedios_ciclo.append(round(promedio_ciclo, 2))

    return render(request, 'aprovechamiento.html', {
        'mensaje': mensaje,
        'programas_antiguos': programas_antiguos,
        'programas_nuevos': programas_nuevos,
        'programas': programas,
        'promedios_hist': promedios_hist,
        'anios': opciones_ciclo,
        'ciclos': ciclos,
        'promedios_ciclo': promedios_ciclo,
        'detalle_programas': detalle_programas
    })
