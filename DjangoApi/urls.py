from django.contrib import admin
from django.urls import path
from api.home.home_views import home_view, home_calificaciones, home_aprobados, home_reprobados, home_promedios, home_mapa
from api.login.login_views import login_view, logout_view
from api.Administrador.administrador_views import administrador_view, subir_calificaciones, gestionar_usuarios, generar_plantilla_csv
from api.views import egresados_view

from api.Administrador.examen_views import examen_admision_view  # ✅ Importación correcta
from api.Administrador.csv_views import (
    descargar_plantilla_nuevo_ingreso,
    subir_csv_nuevo_ingreso
)
from api.Administrador import matriculagenero_views

# 👇 NUEVO: Importamos las vistas de matrícula por cuatrimestre.
from api.Administrador.matricula_cuatrimestre_views import (
    importar_matricula_cuatrimestres,
    matricula_por_cuatrimestre_view,
    descargar_plantilla_matricula_cuatrimestre,
    subir_csv_matricula_cuatrimestre
)

from django.conf import settings
from django.conf.urls.static import static

# ✅ Correcto
from api.Administrador.matriculaHistorica_views import matricula_historica

# ✅ Importaciones para Matrícula H. Nuevo Ingreso
from api.Administrador.Matricula_H_Nuevo_Ingreso_view import (
    matricula_h_nuevo_ingreso_view,
    descargar_plantilla_matricula_h_nuevo_ingreso
)

# ✅ Importaciones de Titulados Histórico Actual
from api.Administrador.titulados_historico_actual_view import (
    titulados_historico_actual_view,
    descargar_plantilla_titulados_historico_actual
)

urlpatterns = [
    # Vistas públicas
    path('', home_view, name='index'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),

    path('calificaciones/', home_calificaciones, name='calificaciones'),
    path('aprobados/', home_aprobados, name='aprobados'),
    path('reprobados/', home_reprobados, name='reprobados'),
    path('promedios/', home_promedios, name='promedios'),
    path('mapa/', home_mapa, name='mapa'),

    # Vistas de administrador
    path('administrador/', administrador_view, name='administrador'),
    path('administrador/subir-calificaciones/', subir_calificaciones, name='subir_calificaciones'),
    path('administrador/egresados/', egresados_view, name='egresados'),
    path('administrador/gestionar-usuarios/', gestionar_usuarios, name='gestionar_usuarios'),
    path('administrador/generar-plantilla/', generar_plantilla_csv, name='generar_plantilla_csv'),

    path('administrador/descargar-plantilla-nuevo-ingreso/', descargar_plantilla_nuevo_ingreso, name='descargar_plantilla_nuevo_ingreso'),
    path('administrador/subir-csv-nuevo-ingreso/', subir_csv_nuevo_ingreso, name='subir_csv_nuevo_ingreso'),
   
    # ✅ Examen Admisión
    path('administrador/examen-admision/', examen_admision_view, name='examen_admision'),
    path('administrador/matricula-genero/', matriculagenero_views.matriculagenero, name='matricula_por_genero'),
    path('administrador/matricula-historica/', matricula_historica, name='matricula_historica'),

    # ✅ NUEVAS RUTAS: Matrícula por Cuatrimestre
    path('administrador/matricula-cuatrimestre/', matricula_por_cuatrimestre_view, name='matricula_por_cuatrimestre'),
    path('administrador/importar-matricula-cuatrimestres/', importar_matricula_cuatrimestres, name='importar_matricula_cuatrimestres'),
    path('administrador/descargar-plantilla-cuatrimestre/', descargar_plantilla_matricula_cuatrimestre, name='descargar_plantilla_cuatrimestre'),
    path('administrador/subir-csv-cuatrimestre/', subir_csv_matricula_cuatrimestre, name='subir_csv_cuatrimestre'),

    # ✅ Matrícula H. Nuevo Ingreso
    path('administrador/matricula-h-nuevo-ingreso/', matricula_h_nuevo_ingreso_view, name='matricula_h_nuevo_ingreso'),
    path('administrador/descargar-plantilla-matricula-h-nuevo-ingreso/', descargar_plantilla_matricula_h_nuevo_ingreso, name='descargar_plantilla_matricula_h_nuevo_ingreso'),

    # ✅ Rutas para Titulados Histórico Actual
    path('administrador/titulados-historico-actual/', titulados_historico_actual_view, name='titulados_historico_actual'),
    path('administrador/descargar-plantilla-titulados-historico-actual/', descargar_plantilla_titulados_historico_actual, name='descargar_plantilla_titulados_historico_actual'),
]

# Archivos estáticos en modo debug.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
