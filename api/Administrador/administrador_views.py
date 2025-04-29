import os
import csv
import pandas as pd
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
from django.conf import settings

# ========== SUBIR CALIFICACIONES ==========
def subir_calificaciones(request):
    if 'usuario_id' not in request.session:
        return redirect('login')

    if request.method == 'POST' and request.FILES.get('archivo_excel'):
        excel_file = request.FILES['archivo_excel']
        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'excels'))
        filename = fs.save(excel_file.name, excel_file)
        file_path = fs.path(filename)

        try:
            df = pd.read_excel(file_path)
            print(df.head())  # Debug
            return HttpResponse("Archivo Excel cargado con éxito.")
        except Exception as e:
            return HttpResponse(f"Error al procesar el archivo: {e}")

    return render(request, 'subir_calificaciones.html')

# ========== VISTA PRINCIPAL ==========
def administrador_view(request):
    if 'usuario_id' not in request.session:
        return redirect('login')
    return render(request, 'base_admin.html')

# ========== GESTIÓN DE USUARIOS ==========
def gestionar_usuarios(request):
    if 'usuario_id' not in request.session:
        return redirect('login')
    return HttpResponse('Gestión de usuarios')

# ========== GENERAR PLANTILLA CSV ==========
def generar_plantilla_csv(request):
    if request.method == "POST":
        campos_seleccionados = request.POST.getlist('campos')

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="plantilla.csv"'

        writer = csv.writer(response)
        writer.writerow(campos_seleccionados)  # Solo encabezados

        return response

    return HttpResponse("Método no permitido", status=405)



