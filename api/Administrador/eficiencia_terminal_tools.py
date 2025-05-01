import pandas as pd
from api.models import EficienciaTerminal, CicloEscolar, Periodo, CicloPeriodo, ProgramaEducativoAntiguo, ProgramaEducativoNuevo

def procesar_excel_eficiencia_terminal(archivo):
    try:
        df = pd.read_excel(archivo)

        # Validar que tenga las columnas necesarias
        columnas_requeridas = ['Ciclo', 'Periodo', 'Programa', 'Tipo Programa', 'Matrícula Ingreso', 'Egresados']
        if not all(col in df.columns for col in columnas_requeridas):
            return False, "❌ El archivo no tiene las columnas correctas. Revise la plantilla."

        for _, fila in df.iterrows():
            ciclo_anio = int(fila['Ciclo'])
            periodo_nombre = fila['Periodo']
            programa_nombre = fila['Programa']
            tipo = fila['Tipo Programa']
            ingreso = int(fila['Matrícula Ingreso'])
            egresados = int(fila['Egresados'])

            # Obtener o crear ciclo
            ciclo, _ = CicloEscolar.objects.get_or_create(anio=ciclo_anio)
            # Obtener periodo
            periodo = Periodo.objects.filter(nombre=periodo_nombre).first()
            if not periodo:
                return False, f"❌ Periodo '{periodo_nombre}' no encontrado."

            # Obtener ciclo-periodo
            cp = CicloPeriodo.objects.filter(ciclo=ciclo, periodo=periodo).first()
            if not cp:
                return False, f"❌ Ciclo-Periodo para {ciclo_anio} - {periodo_nombre} no encontrado."

            # Identificar si es programa antiguo o nuevo
            prog_antiguo = prog_nuevo = None
            if tipo.lower() == 'antiguo':
                prog_antiguo = ProgramaEducativoAntiguo.objects.filter(id=programa_nombre).first()
                if not prog_antiguo:
                    return False, f"❌ Programa educativo antiguo '{programa_nombre}' no encontrado."
            elif tipo.lower() == 'nuevo':
                prog_nuevo = ProgramaEducativoNuevo.objects.filter(id=programa_nombre).first()
                if not prog_nuevo:
                    return False, f"❌ Programa educativo nuevo '{programa_nombre}' no encontrado."
            else:
                return False, f"❌ Tipo de programa inválido: '{tipo}'. Use 'Antiguo' o 'Nuevo'."

            # Crear o actualizar registro
            EficienciaTerminal.objects.update_or_create(
                ciclo_periodo=cp,
                programa_antiguo=prog_antiguo,
                programa_nuevo=prog_nuevo,
                defaults={
                    'matricula_ingreso': ingreso,
                    'egresados': egresados,
                }
            )

        return True, "✅ Datos cargados correctamente."

    except Exception as e:
        return False, f"❌ Error al procesar el archivo: {str(e)}"

import openpyxl
from django.http import HttpResponse

def descargar_plantilla_eficiencia(request):
    from openpyxl import Workbook
    from api.models import ProgramaEducativoAntiguo, ProgramaEducativoNuevo, CicloPeriodo

    wb = Workbook()
    ws = wb.active
    ws.title = "Eficiencia Terminal"

    # Encabezados
    ws.append(["Ciclo", "Periodo", "Programa", "Tipo Programa", "Matrícula Ingreso", "Egresados"])

    # Programas Antiguos
    antiguos = ProgramaEducativoAntiguo.objects.all()
    nuevos = ProgramaEducativoNuevo.objects.all()
    ciclos = CicloPeriodo.objects.select_related("ciclo", "periodo").all()

    for cp in ciclos:
        anio = cp.ciclo.anio
        periodo_nombre = cp.periodo.nombre

        for prog in antiguos:
            ws.append([anio, periodo_nombre, prog.id, "Antiguo", "", ""])
        for prog in nuevos:
            ws.append([anio, periodo_nombre, prog.id, "Nuevo", "", ""])

    # Respuesta HTTP
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="PLANTILLA_EFICIENCIA_TERMINAL.xlsx"'
    wb.save(response)
    return response

