import pandas as pd
import csv
import os
from io import BytesIO
from datetime import datetime

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django import forms

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

from api.models import ProgramaEducativoAntiguo, ProgramaEducativoNuevo

# --- Formularios ---
class SubirCarrerasForm(forms.Form):
    archivo = forms.FileField(
        label="Archivo CSV",
        widget=forms.ClearableFileInput(attrs={"accept": ".csv"}),
        required=False
    )

class AgregarProgramaNuevoForm(forms.ModelForm):
    class Meta:
        model = ProgramaEducativoNuevo
        fields = ["id", "nombre"]
        labels = {
            "id": "ID de la carrera",
            "nombre": "Nombre del programa educativo",
        }


# --- Plantilla CSV antiguos ---
def generar_plantilla_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="programas_educativos_antiguos.csv"'

    writer = csv.writer(response)
    writer.writerow(["id", "nombre"])
    for programa in ProgramaEducativoAntiguo.objects.all().order_by("id"):
        writer.writerow([programa.id, programa.nombre])

    return response


# --- Plantilla CSV nuevos ---
def generar_plantilla_nuevos_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="programas_educativos_nuevos.csv"'

    writer = csv.writer(response)
    writer.writerow(["id", "nombre"])
    for programa in ProgramaEducativoNuevo.objects.all().order_by("id"):
        writer.writerow([programa.id, programa.nombre])

    return response


# --- Exportar ambas tablas a PDF ---
def exportar_carreras_pdf(request):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elementos = []
    estilos = getSampleStyleSheet()

    # Logo
    logo_path = os.path.join(settings.BASE_DIR, "static", "imagenes", "uptex_logo.png")
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=130, height=60)
        elementos.append(logo)
        elementos.append(Spacer(1, 12))

    # Título y fecha
    fecha_actual = datetime.now().strftime("%d/%m/%Y")
    titulo = Paragraph(f"<b>Materias Nuevas y Antiguas</b><br/><font size=10>Fecha: {fecha_actual}</font>", estilos["Title"])
    elementos.append(titulo)
    elementos.append(Spacer(1, 20))

    # Antiguos
    elementos.append(Paragraph("📘 Programas Educativos Antiguos", estilos['Heading2']))
    data_antiguos = [["ID", "Nombre"]]
    for carrera in ProgramaEducativoAntiguo.objects.all().order_by("id"):
        data_antiguos.append([carrera.id, carrera.nombre])
    tabla_antiguos = Table(data_antiguos, colWidths=[100, 350])
    tabla_antiguos.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER')
    ]))
    elementos.append(tabla_antiguos)
    elementos.append(Spacer(1, 20))

    # Nuevos
    elementos.append(Paragraph("📗 Programas Educativos Nuevos", estilos['Heading2']))
    data_nuevos = [["ID", "Nombre"]]
    for carrera in ProgramaEducativoNuevo.objects.all().order_by("id"):
        data_nuevos.append([carrera.id, carrera.nombre])
    tabla_nuevos = Table(data_nuevos, colWidths=[100, 350])
    tabla_nuevos.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER')
    ]))
    elementos.append(tabla_nuevos)

    doc.build(elementos)
    buffer.seek(0)

    return HttpResponse(buffer, content_type='application/pdf', headers={
        'Content-Disposition': 'attachment; filename="carreras_programas.pdf"'
    })


# --- Vista principal ---
def subir_carreras_view(request):
    form_antiguos = SubirCarrerasForm()
    form_nuevos = SubirCarrerasForm()
    nuevo_form = AgregarProgramaNuevoForm()

    if request.method == "POST":
        if "subir_antiguos" in request.POST:
            form_antiguos = SubirCarrerasForm(request.POST, request.FILES)
            if form_antiguos.is_valid():
                archivo = form_antiguos.cleaned_data["archivo"]
                try:
                    df = pd.read_csv(archivo)
                    df.columns = df.columns.str.lower().str.strip()
                    requeridas = {"id", "nombre"}
                    if not requeridas.issubset(df.columns):
                        faltantes = requeridas - set(df.columns)
                        messages.error(request, f"❌ Columnas faltantes: {', '.join(faltantes)}")
                    else:
                        nuevas, actualizadas = 0, 0
                        for _, fila in df.iterrows():
                            obj, creado = ProgramaEducativoAntiguo.objects.update_or_create(
                                id=str(fila["id"]).strip(),
                                defaults={"nombre": fila["nombre"].strip()}
                            )
                            nuevas += creado
                            actualizadas += not creado
                        messages.success(request, f"✅ {nuevas} nuevas y {actualizadas} actualizadas.")
                except Exception as e:
                    messages.error(request, f"❌ Error al procesar el archivo: {e}")
            return redirect("subir_carreras")

        elif "subir_nuevos" in request.POST:
            form_nuevos = SubirCarrerasForm(request.POST, request.FILES)
            if form_nuevos.is_valid():
                archivo = form_nuevos.cleaned_data["archivo"]
                try:
                    df = pd.read_csv(archivo)
                    df.columns = df.columns.str.lower().str.strip()
                    requeridas = {"id", "nombre"}
                    if not requeridas.issubset(df.columns):
                        faltantes = requeridas - set(df.columns)
                        messages.error(request, f"❌ Columnas faltantes: {', '.join(faltantes)}")
                    else:
                        nuevas, actualizadas = 0, 0
                        for _, fila in df.iterrows():
                            obj, creado = ProgramaEducativoNuevo.objects.update_or_create(
                                id=str(fila["id"]).strip(),
                                defaults={"nombre": fila["nombre"].strip()}
                            )
                            nuevas += creado
                            actualizadas += not creado
                        messages.success(request, f"✅ {nuevas} nuevas y {actualizadas} actualizadas.")
                except Exception as e:
                    messages.error(request, f"❌ Error al procesar el archivo: {e}")
            return redirect("subir_carreras")

        elif "agregar_nuevo_manual" in request.POST:
            nuevo_form = AgregarProgramaNuevoForm(request.POST)
            if nuevo_form.is_valid():
                nuevo_form.save()
                messages.success(request, "✅ Programa nuevo agregado correctamente.")
            else:
                messages.error(request, "❌ Error al agregar manualmente.")
            return redirect("subir_carreras")

    antiguos = ProgramaEducativoAntiguo.objects.all().order_by("id")
    nuevos = ProgramaEducativoNuevo.objects.all().order_by("id")

    return render(request, "Subir_carreras.html", {
        "form_antiguos": form_antiguos,
        "form_nuevos": form_nuevos,
        "nuevo_form": nuevo_form,
        "antiguos": antiguos,
        "nuevos": nuevos,
    })
