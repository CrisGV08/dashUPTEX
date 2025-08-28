import os
import csv
import json
import pandas as pd
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
from django.conf import settings
from django.urls import reverse
from django.db.models import Sum, F
from django.db.models.functions import Coalesce

from api.models import (
    CicloEscolar, Periodo, CicloPeriodo,
    ProgramaEducativoAntiguo, ProgramaEducativoNuevo,
    MatriculaPorCuatrimestre
)


def importar_matricula_cuatrimestres(request):
    if 'usuario_id' not in request.session:
        return redirect('login')

    archivo = os.path.join(settings.MEDIA_ROOT, "excels", "Indicadores historicos 07-02-25.xlsx")
    excel = pd.ExcelFile(archivo)

    hojas = ["Matricula 20-21", "Matricula 21-22", "Matricula 22-23", "Matricula 23-24", "Matricula 24-25"]

    carreras_antiguas = [
        "Ingenieria en sistemas electronicos",
        "Ingenieria en Mecatronica",
        "Ingenieria en sistemas Computacionales",
        "Ingenieria en logistica",
        "Licenciatura en Administracion",
        "Licenciatura en Comercio Internacional y aduanas",
    ]
    carreras_normalizadas = [c.lower() for c in carreras_antiguas]

    periodos_map = {
        "Sep-Dic": ("S-D", 0),
        "Ene-Abr": ("E-A", 1),
        "May-Ago": ("M-A", 1),
        "May- Ago": ("M-A", 1),
    }

    registros = 0

    for hoja in hojas:
        df = excel.parse(hoja).dropna(how="all")
        for _, row in df.iterrows():
            nombre = str(row.get("Unnamed: 1", "")).strip().lower()
            if nombre not in carreras_normalizadas:
                continue

            programa = ProgramaEducativoAntiguo.objects.filter(nombre__icontains=nombre).first()
            if not programa:
                continue

            for col in df.columns:
                for etiqueta, (clave_periodo, offset) in periodos_map.items():
                    if etiqueta in str(col):
                        try:
                            anio_base = hoja.replace("Matricula ", "").split("-")[0]
                            anio = int(anio_base) + offset
                            ciclo, _ = CicloEscolar.objects.get_or_create(anio=anio)
                            periodo, _ = Periodo.objects.get_or_create(clave=clave_periodo, defaults={"nombre": etiqueta})
                            ciclo_periodo, _ = CicloPeriodo.objects.get_or_create(ciclo=ciclo, periodo=periodo)
                            cantidad = int(row[col])
                            MatriculaPorCuatrimestre.objects.update_or_create(
                                ciclo_periodo=ciclo_periodo,
                                programa_antiguo=programa,
                                defaults={"cantidad": cantidad}
                            )
                            registros += 1
                        except Exception:
                            continue

    print(f"✅ {registros} registros cargados en MatriculaPorCuatrimestre.")
    return redirect("matricula_por_cuatrimestre")


def matricula_por_cuatrimestre_view(request):
    ciclos = (CicloPeriodo.objects
              .select_related('ciclo', 'periodo')
              .order_by('ciclo__anio', 'periodo__clave'))

    # Filtros
    tipo_programa = request.GET.get('tipo_programa', 'antiguo')  # default
    filtro_ciclo = request.GET.get('ciclo')
    filtro_programa = request.GET.get('programa')

    # Catálogo de programas según tipo
    if tipo_programa == 'nuevo':
        programas = ProgramaEducativoNuevo.objects.all().order_by('nombre')
    else:
        programas = ProgramaEducativoAntiguo.objects.all().order_by('nombre')

    # Base queryset
    base_qs = (MatriculaPorCuatrimestre.objects
               .select_related('ciclo_periodo__ciclo',
                               'ciclo_periodo__periodo',
                               'programa_antiguo'))

    if filtro_ciclo and filtro_ciclo != "Todos":
        base_qs = base_qs.filter(ciclo_periodo__id=filtro_ciclo)

    # Aplica filtro de programa según tipo
    qs = base_qs
    if filtro_programa and filtro_programa != "Todos":
        if tipo_programa == 'nuevo':
            qs = qs.filter(programa_nuevo__id=filtro_programa)
        else:
            qs = qs.filter(programa_antiguo__id=filtro_programa)

    # Dataset base para gráficas (agrupado por periodo y programa)
    grafica_qs = (qs.values(
                    anio=F('ciclo_periodo__ciclo__anio'),
                    periodo=F('ciclo_periodo__periodo__clave'),
                    prog_ant=F('programa_antiguo__nombre'),
                    prog_nvo=F('programa_nuevo__nombre'),
                  )
                  .annotate(total=Sum('cantidad'))
                  .order_by('anio', 'periodo', 'prog_ant', 'prog_nvo'))

    sin_datos = not grafica_qs.exists()
    aviso_tipo_programa = None

    # Fallback: si pidieron "nuevo" y no hay datos, usar "antiguo"
    if sin_datos and tipo_programa == 'nuevo':
        aviso_tipo_programa = "No hay datos para 'Programa nuevo'. Se muestran los de 'Programa antiguo'."
        tipo_programa = 'antiguo'
        programas = ProgramaEducativoAntiguo.objects.all().order_by('nombre')

        qs = base_qs
        if filtro_programa and filtro_programa != "Todos":
            qs = qs.filter(programa_antiguo__id=filtro_programa)

        grafica_qs = (qs.values(
                        anio=F('ciclo_periodo__ciclo__anio'),
                        periodo=F('ciclo_periodo__periodo__clave'),
                        prog_ant=F('programa_antiguo__nombre'),
                        prog_nvo=F('programa_nuevo__nombre'),
                      )
                      .annotate(total=Sum('cantidad'))
                      .order_by('anio', 'periodo', 'prog_ant', 'prog_nvo'))
        sin_datos = not grafica_qs.exists()

    # --------- TABLA (sobre el queryset final) ----------
    tabla = [
        {
            'programa': (r.programa_antiguo.nombre if r.programa_antiguo else
                         (getattr(r, 'programa_nuevo', None).nombre
                          if getattr(r, 'programa_nuevo', None) else '')),
            'periodo': f"{r.ciclo_periodo.periodo.nombre} {r.ciclo_periodo.ciclo.anio}",
            'cantidad': int(r.cantidad or 0),
        }
        for r in qs
    ]

    # --------- SERIES POR MATERIA/PROGRAMA ----------
    # 1) Eje X (periodos en orden)
    etiquetas_periodo = []
    for row in grafica_qs:
        etiqueta = f"{row['anio']} - {row['periodo']}"
        if etiqueta not in etiquetas_periodo:
            etiquetas_periodo.append(etiqueta)

    # 2) Nombres de programa (antiguo/nuevo según exista en datos)
    programas_nombres = []
    for row in grafica_qs:
        nombre = row['prog_ant'] or row['prog_nvo'] or ''
        if nombre and nombre not in programas_nombres:
            programas_nombres.append(nombre)

    # 3) Mapa (programa -> valores por periodo)
    series_map = {p: [0] * len(etiquetas_periodo) for p in programas_nombres}
    idx_periodo = {etq: i for i, etq in enumerate(etiquetas_periodo)}
    for row in grafica_qs:
        etiqueta = f"{row['anio']} - {row['periodo']}"
        nombre = row['prog_ant'] or row['prog_nvo'] or ''
        if not nombre:
            continue
        i = idx_periodo[etiqueta]
        series_map[nombre][i] = int(row['total'] or 0)

    # 4) Totales por programa (para pie)
    totales_por_programa = {p: sum(vals) for p, vals in series_map.items()}

    # 5) Estructura final para el frontend (multi-series)
    datos_grafica = {
        'labels': etiquetas_periodo,
        'series': [{'label': p, 'data': series_map[p]} for p in programas_nombres],
        'pie_labels': list(totales_por_programa.keys()),
        'pie_values': list(totales_por_programa.values()),
    }

    # Total general del queryset final
    total_general = qs.aggregate(total=Sum('cantidad'))['total'] or 0

    # Debug (opcional)
    print("DBG MPC -> periodos:", len(etiquetas_periodo))
    print("DBG MPC -> programas:", len(programas_nombres))
    print("DBG MPC -> total_general:", total_general)

    return render(request, "matricula_por_cuatrimestre.html", {
        'ciclos': ciclos,
        'programas': programas,
        'filtro_ciclo': filtro_ciclo,
        'filtro_programa': filtro_programa,
        'tipo_programa': tipo_programa,
        'tabla': tabla,
        'datos_grafica': json.dumps(datos_grafica),
        'total_general': total_general,
        'aviso_tipo_programa': aviso_tipo_programa,
        'sin_datos': sin_datos,
    })


def descargar_plantilla_matricula_cuatrimestre(request):
    ciclo_periodo = CicloPeriodo.objects.order_by('-id').first()

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="plantilla_matricula_cuatrimestre.csv"'

    writer = csv.writer(response)
    writer.writerow(['ciclo_periodo_id', 'programa_antiguo_id', 'cantidad'])

    for programa in ProgramaEducativoAntiguo.objects.all():
        writer.writerow([ciclo_periodo.id if ciclo_periodo else '', programa.id, 0])

    return response


def subir_csv_matricula_cuatrimestre(request):
    if request.method == 'POST' and request.FILES.get('archivo_csv'):
        archivo = request.FILES['archivo_csv']
        decoded = archivo.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded)

        errores = 0
        guardados = 0

        for i, fila in enumerate(reader, start=1):
            try:
                ciclo_id = int(fila['ciclo_periodo_id'])
                programa_id = fila['programa_antiguo_id']
                cantidad = int(fila['cantidad'])

                ciclo = CicloPeriodo.objects.get(id=ciclo_id)
                programa = ProgramaEducativoAntiguo.objects.get(id=programa_id)

                MatriculaPorCuatrimestre.objects.update_or_create(
                    ciclo_periodo=ciclo,
                    programa_antiguo=programa,
                    defaults={'cantidad': cantidad}
                )
                guardados += 1
            except Exception as e:
                errores += 1
                print(f"Fila {i} error: {e}")

        if guardados:
            messages.success(request, f"✅ {guardados} registros guardados.")
        if errores:
            messages.error(request, f"⚠️ {errores} errores encontrados.")

        return HttpResponseRedirect(reverse('matricula_por_cuatrimestre'))

    messages.error(request, "Debes subir un archivo CSV válido.")
    return HttpResponseRedirect(reverse('matricula_por_cuatrimestre'))
