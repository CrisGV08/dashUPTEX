import csv
import json
import pandas as pd
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.db.models import Avg, Q
from api.models import (
    CicloEscolar, Periodo, CicloPeriodo,
    AprovechamientoAcademico, ProgramaEducativoAntiguo, ProgramaEducativoNuevo
)

def descargar_plantilla_aprovechamiento(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="plantilla_aprovechamiento.csv"'
    writer = csv.writer(response)
    writer.writerow(['ciclo_periodo', 'programa_id', 'promedio'])  # ahora dice programa_id

    ciclos = CicloPeriodo.objects.select_related('ciclo', 'periodo').order_by('ciclo__anio', 'periodo__clave')
    programas = list(ProgramaEducativoAntiguo.objects.all()) + list(ProgramaEducativoNuevo.objects.all())

    for ciclo in ciclos:
        for prog in programas:
            nombre = f"{ciclo.ciclo.anio} - {ciclo.periodo.clave}"
            writer.writerow([nombre, prog.id, ''])  # ahora usa prog.id

    return response

import io
import re
import math
import pandas as pd
from django.db import transaction
from django.shortcuts import redirect
from django.contrib import messages

def cargar_aprovechamiento(request):
    if request.method != 'POST':
        return redirect('aprovechamiento')

    archivo = request.FILES.get('archivo_csv')
    if not archivo:
        messages.error(request, "No se recibió ningún archivo.")
        return redirect('aprovechamiento')

    try:
        # ====== LECTURA ROBUSTA DEL CSV (convierte BYTES -> TEXTO) ======
        raw_bytes = archivo.read()             # -> bytes
        try:
            text = raw_bytes.decode('utf-8-sig')
        except UnicodeDecodeError:
            text = raw_bytes.decode('latin-1')

        # Usa un buffer de texto para pandas
        buffer = io.StringIO(text)

        # Autodetecta ; o , (engine='python' requiere texto, no bytes)
        df = pd.read_csv(buffer, sep=None, engine='python', na_filter=False)

        # Normaliza encabezados ANTES de validar
        df.columns = [c.strip().lower() for c in df.columns]

        # Acepta 'programa' o 'programa_id'
        prog_col = 'programa' if 'programa' in df.columns else ('programa_id' if 'programa_id' in df.columns else None)
        if not prog_col or not {'ciclo_periodo', prog_col, 'promedio'} <= set(df.columns):
            messages.error(request, "Columnas requeridas: ciclo_periodo, programa (o programa_id), promedio.")
            return redirect('aprovechamiento')

        guardados = 0
        rx_ciclo = re.compile(r'^\s*(\d{4})\s*[-–]\s*([A-ZÁÉÍÓÚÑ]\s*-\s*[A-ZÁÉÍÓÚÑ])\s*$')

        with transaction.atomic():
            for index, row in df.iterrows():
                try:
                    # ------ CicloPeriodo: "2025 - E-A"
                    ciclo_texto = str(row['ciclo_periodo']).strip()
                    m = rx_ciclo.match(ciclo_texto)
                    if not m:
                        raise ValueError("Formato inválido en 'ciclo_periodo' (usa '2025 - E-A').")

                    anio = int(m.group(1))
                    clave_periodo = m.group(2).replace(' ', '')

                    ciclo = CicloEscolar.objects.get(anio=anio)
                    periodo = Periodo.objects.get(clave=clave_periodo)
                    ciclo_periodo = CicloPeriodo.objects.get(ciclo=ciclo, periodo=periodo)

                    # ------ Programa: ID preferente; fallback por nombre
                    prog_raw = str(row[prog_col]).strip()

                    # 1) exacto por ID
                    pa = ProgramaEducativoAntiguo.objects.filter(id=prog_raw).first()
                    pn = ProgramaEducativoNuevo.objects.filter(id=prog_raw).first()
                    # 2) por nombre exacto (por si te mandan nombres)
                    if not (pa or pn):
                        pa = ProgramaEducativoAntiguo.objects.filter(nombre__iexact=prog_raw).first()
                        pn = ProgramaEducativoNuevo.objects.filter(nombre__iexact=prog_raw).first()

                    if not (pa or pn):
                        cand_pa = list(ProgramaEducativoAntiguo.objects.filter(id__istartswith=prog_raw))
                        cand_pn = list(ProgramaEducativoNuevo.objects.filter(id__istartswith=prog_raw))
                        candidatos = cand_pa + cand_pn
                        if len(candidatos) == 1:
                            c = candidatos[0]
                            if isinstance(c, ProgramaEducativoAntiguo):
                                pa, pn = c, None

                            else:
                                pa, pn = None, c
                        elif len(candidatos) > 1:
                            opts = ", ".join(f"{c.id} ({c.nombre})" for c in candidatos[:6])
                            raise ValueError(f"ID '{prog_raw}' es ambiguo. Coinciden: {opts}{'…' if len(candidatos)>6 else ''}")
                        
                    if not (pa or pn):
                     # Lista de algunos IDs válidos para ayudar
                        ids_validos = list(ProgramaEducativoAntiguo.objects.values_list('id', flat=True)[:6]) + \
                                      list(ProgramaEducativoNuevo.objects.values_list('id', flat=True)[:6])
                        muestra = ", ".join(ids_validos)
                        raise ValueError(f"Programa no encontrado: '{prog_raw}'. Ejemplos de IDs válidos: {muestra}")

                    programa_antiguo, programa_nuevo = pa, pn

                    # ------ Promedio
                    prom_raw = row.get('promedio', '')
                    if prom_raw in (None, '') or (isinstance(prom_raw, float) and math.isnan(prom_raw)):
                        raise ValueError("El campo 'promedio' está vacío.")
                    try:
                        promedio = float(str(prom_raw).replace(',', '.'))
                    except Exception:
                        raise ValueError(f"Promedio inválido: '{prom_raw}'.")

                    # ------ Upsert (usa solo el campo correspondiente)
                    lookup = dict(ciclo_periodo=ciclo_periodo,
                                  programa_antiguo=programa_antiguo if programa_antiguo else None,
                                  programa_nuevo=programa_nuevo if programa_nuevo else None)

                    AprovechamientoAcademico.objects.update_or_create(
                        **lookup,
                        defaults={'promedio': promedio},
                    )
                    guardados += 1

                except Exception as fila_err:
                    messages.error(request, f"Error en fila {index + 2}: {fila_err}")

        if guardados > 0:
            messages.success(request, f"{guardados} registros guardados correctamente.")
        else:
            messages.warning(request, "No se guardaron registros.")

    except Exception as e:
        messages.error(request, f"Error general al procesar el archivo: {e}")

    return redirect('aprovechamiento')




def aprovechamiento_view(request):
    mensaje = request.GET.get("mensaje")

    # Catálogos
    programas_antiguos = ProgramaEducativoAntiguo.objects.all()
    programas_nuevos = ProgramaEducativoNuevo.objects.all()

    # Opciones de ciclo en texto "YYYY - XX"
    ciclos_periodos = CicloPeriodo.objects.select_related('ciclo', 'periodo')
    opciones_ciclo = sorted(
        [f"{cp.ciclo.anio} - {cp.periodo.clave}" for cp in ciclos_periodos],
        reverse=True
    )

    # --- Filtros desde la URL ---
    # Programas (se mantiene igual)
    filtro_programas = request.GET.getlist("programas[]")

    # NUEVO: lista de ciclos seleccionados (chips multiselect)
    # Si no viene nada, tomamos ['Todos'] para mostrar todo.
    filtro_ciclos = request.GET.getlist("ciclos[]")
    if not filtro_ciclos:
        filtro_ciclos = ['Todos']

    # Query base
    registros = AprovechamientoAcademico.objects.select_related(
        'ciclo_periodo__ciclo', 'ciclo_periodo__periodo',
        'programa_antiguo', 'programa_nuevo'
    )

    # Aplica filtro de ciclos (si no está 'Todos')
    ciclos_seleccionados = [c for c in filtro_ciclos if c != 'Todos']
    if ciclos_seleccionados:
        objetos_ciclo = []
        for ctexto in ciclos_seleccionados:
            try:
                anio_str, periodo_clave = ctexto.split(" - ")
                obj = CicloPeriodo.objects.get(ciclo__anio=int(anio_str), periodo__clave=periodo_clave.strip())
                objetos_ciclo.append(obj)
            except (ValueError, CicloPeriodo.DoesNotExist):
                continue
        if objetos_ciclo:
            registros = registros.filter(ciclo_periodo__in=objetos_ciclo)

    # Aplica filtro de programas (igual que antes)
    if filtro_programas:
        q_antiguos = Q(programa_antiguo__id__in=filtro_programas)
        q_nuevos = Q(programa_nuevo__id__in=filtro_programas)
        registros = registros.filter(q_antiguos | q_nuevos)

    # Orden lógico
    registros = registros.order_by(
        'ciclo_periodo__ciclo__anio', 'ciclo_periodo__periodo__clave',
        'programa_antiguo__nombre', 'programa_nuevo__nombre'
    )

    # ¿Comparación multi-ciclo?
    multi_ciclo = (len(ciclos_seleccionados) != 1)  # 0 ó >1 ⇒ comparar

    # Armar datos para gráficas/tabla
    datos_graficas = {'programas': [], 'promedios': [], 'tipos': []}
    detalle_ciclos = []

    for r in registros:
        ciclo_txt = f"{r.ciclo_periodo.ciclo.anio} - {r.ciclo_periodo.periodo.clave}"

        if r.programa_antiguo:
            base = f"{r.programa_antiguo.nombre} (Antiguo)"
            tipo = "antiguo"
        else:
            base = f"{r.programa_nuevo.nombre} (Nuevo)"
            tipo = "nuevo"

        # Si hay varios ciclos seleccionados (o 'Todos'), añade el ciclo al label
        nombre_prog = f"{base} [{ciclo_txt}]" if multi_ciclo else base

        datos_graficas['programas'].append(nombre_prog)
        datos_graficas['promedios'].append(float(r.promedio))
        datos_graficas['tipos'].append(tipo)

        detalle_ciclos.append({
            'ciclo': ciclo_txt,
            'programa': nombre_prog,
            'promedio': r.promedio
        })

    return render(request, 'aprovechamiento.html', {
        'mensaje': mensaje,
        'anios': opciones_ciclo,                  # lista de ciclos en texto
        'programas_antiguos': programas_antiguos,
        'programas_nuevos': programas_nuevos,
        'datos_graficas': json.dumps(datos_graficas),
        'detalle_ciclos': detalle_ciclos,
        'filtros_aplicados': {
            'ciclos': filtro_ciclos,              # << para marcar checks
            'programas': filtro_programas
        }
    })
