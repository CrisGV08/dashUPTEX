# DjangoApi/urls.py
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

# Auth
from api.login.login_views import login_view, logout_view

# ----- Home (público) -----
from api.home.home_views import (
    home_view, home_calificaciones, home_aprobados,
    home_reprobados, home_promedios, home_mapa
)
from api.home.examen_usuario_view import examen_admision_usuario_view
from api.home.matricula_historica_usuario_view import matricula_historica_usuario_view
from api.home.matricula_por_genero_usuario_view import matricula_por_genero_usuario_view
from api.home.matricula_anual_usuario_view import matricula_anual_usuario_view
from api.home.matricula_cuatrimestre_usuario_view import matricula_cuatrimestre_usuario_view
from api.home.matricula_h_nuevo_ingreso_usuario_view import matricula_h_nuevo_ingreso_usuario_view
from api.home.aprovechamiento_usuario_view import aprovechamiento_usuario_view
from api.home.indicadores_generales_usuario_view import indicadores_generales_usuario_view
from api.home.eficiencia_terminal_usuario_view import eficiencia_terminal_usuario_view
from api.home.titulados_historicos_actual_usuario_view import titulados_historicos_actual_usuario_view
from api.home.evaluacion_docente_cuatrimestre_usuario_view import evaluacion_docente_cuatrimestre_usuario_view
from api.home.evaluacion_docente_concentrado_usuario_view import evaluacion_docente_concentrado_usuario_view
from api.home.tit_his_usuario import tit_his_usuario_view

# ----- Administrador -----
from api.Administrador.administrador_views import (
    administrador_view, subir_calificaciones, gestionar_usuarios, generar_plantilla_csv
)
from api.views import egresados_view
from api.Administrador.examen_views import examen_admision_view
from api.Administrador.csv_views import (
    descargar_plantilla_nuevo_ingreso, subir_csv_nuevo_ingreso
)
from api.Administrador import matriculagenero_views
from api.Administrador.matriculaHistorica_views import matricula_historica
from api.Administrador.matricula_anual_views import matricula_por_anio_view
from api.Administrador.matricula_cuatrimestre_views import (
    matricula_por_cuatrimestre_view,
    descargar_plantilla_matricula_cuatrimestre,
    subir_csv_matricula_cuatrimestre
)
from api.Administrador.eficiencia3anios_views import eficiencia_3anios_view
from api.Administrador.aprovechamiento_views import (
    aprovechamiento_view,
    descargar_plantilla_aprovechamiento,
    cargar_aprovechamiento,
)
from api.Administrador.indicadores_generales_view import (
    reprobacion_desercion_view,
    cargar_indicadores_generales,
    descargar_plantilla_indicadores
)
from api.Administrador.eficiencia_terminal_view import (
    eficiencia_terminal_view,
    descargar_plantilla_eficiencia_terminal,
    cargar_eficiencia_terminal,
)
from api.Administrador.Matricula_H_Nuevo_Ingreso_view import (
    matricula_h_nuevo_ingreso_view, descargar_plantilla_matricula_h_nuevo_ingreso
)
from api.Administrador.titulados_historico_actual_view import (
    titulados_historico_actual_view,
    descargar_plantilla_titulados_historico_actual
)
from api.Administrador.evaluacion_docente_cuatrimestre_view import evaluacion_docente_cuatrimestre_view
from api.Administrador.evaluacion_docente_concentrado_view import evaluacion_docente_concentrado_view

# OJO: esta vista tenía un import duplicado de nombre; la alias-eamos para evitar choques
from api.Administrador.subir_carreras_view import (
    subir_carreras_view,
    generar_plantilla_csv as generar_plantilla_carreras_csv,
    generar_plantilla_nuevos_csv,
    exportar_carreras_pdf
)

# ----- Tasa de Titulación / Titulados (admin) -----
from api.Administrador.tasa_de_titulacion_view import (
    tasa_de_titulacion_view, descargar_plantilla_tasa_titulacion, subir_excel_tasa_titulacion
)
from api.Administrador.titulados_historicos_view import (
    titulados_historicos_view,
    descargar_plantilla_titulados_historicos
)
from api.Administrador import titulados_tsu_inge_view as tti

# ----- NUEVO CRUD Titulados -----
from api.Administrador.tit_his import tit_his_view, tit_his_api

urlpatterns = [
    # ==================== Autenticación ====================
    path('login/',  login_view,  name='login'),
    path('logout/', logout_view, name='logout'),

    # ==================== Home / Público ====================
    path('', home_view, name='index'),
    path('calificaciones/', home_calificaciones, name='calificaciones'),
    path('aprobados/', home_aprobados, name='aprobados'),
    path('reprobados/', home_reprobados, name='reprobados'),
    path('promedios/', home_promedios, name='promedios'),
    path('mapa/', home_mapa, name='mapa'),

    # ----- Vistas usuario normal -----
    path('usuario/examen-admision/', examen_admision_usuario_view, name='examen_admision_usuario'),
    path('usuario/matricula-historica/', matricula_historica_usuario_view, name='matricula_historica_usuario'),
    path('usuario/matricula-genero/', matricula_por_genero_usuario_view, name='matricula_por_genero_usuario'),
    path('usuario/matricula-anual/', matricula_anual_usuario_view, name='matricula_anual_usuario'),
    path('usuario/matricula-cuatrimestre/', matricula_cuatrimestre_usuario_view, name='matricula_cuatrimestre_usuario'),
    path('usuario/matricula-nuevo-ingreso/', matricula_h_nuevo_ingreso_usuario_view, name='matricula_h_nuevo_ingreso_usuario'),
    path('usuario/aprovechamiento/', aprovechamiento_usuario_view, name='aprovechamiento_usuario'),
    path('usuario/indicadores-generales/', indicadores_generales_usuario_view, name='indicadores_generales_usuario'),
    path('usuario/eficiencia-terminal/', eficiencia_terminal_usuario_view, name='eficiencia_terminal_usuario'),
    path('usuario/titulados-historicos-actual/', titulados_historicos_actual_usuario_view, name='titulados_historicos_actual_usuario'),
    path('usuario/evaluacion-docente-cuatrimestre/', evaluacion_docente_cuatrimestre_usuario_view, name='Evaluacion_docente_cuatrimestre_usuario'),
    path('usuario/evaluacion-docente-concentrado/', evaluacion_docente_concentrado_usuario_view, name='evaluacion_docente_concentrado_usuario'),

    # Vista pública Titulados – Histórico (nuevo URL que va en base.html)
    path('titulados/historico/', tit_his_usuario_view, name='tit_his_usuario'),

    # ==================== Administrador ====================
    path('admin/', admin.site.urls),
    path('administrador/', administrador_view, name='administrador'),

    # Gestión general
    path('administrador/subir-calificaciones/', subir_calificaciones, name='subir_calificaciones'),
    path('administrador/gestionar-usuarios/', gestionar_usuarios, name='gestionar_usuarios'),
    path('administrador/generar-plantilla/', generar_plantilla_csv, name='generar_plantilla_csv'),

    # Egresados / Examen admisión
    path('administrador/egresados/', egresados_view, name='egresados'),
    path('administrador/examen-admision/', examen_admision_view, name='examen_admision'),

    # Nuevo ingreso CSV
    path('administrador/descargar-plantilla-nuevo-ingreso/', descargar_plantilla_nuevo_ingreso, name='descargar_plantilla_nuevo_ingreso'),
    path('administrador/subir-csv-nuevo-ingreso/', subir_csv_nuevo_ingreso, name='subir_csv_nuevo_ingreso'),

    # Matrícula
    path('administrador/matricula-genero/', matriculagenero_views.matriculagenero, name='matricula_por_genero'),
    path('administrador/matricula-historica/', matricula_historica, name='matricula_historica'),
    path('administrador/matricula-por-anio/', matricula_por_anio_view, name='matricula_por_anio'),

    path('administrador/matricula-cuatrimestre/', matricula_por_cuatrimestre_view, name='matricula_por_cuatrimestre'),
    path('administrador/matricula-cuatrimestre/descargar-plantilla/', descargar_plantilla_matricula_cuatrimestre, name='descargar_plantilla_matricula_cuatrimestre'),
    path('administrador/matricula-cuatrimestre/subir-csv/', subir_csv_matricula_cuatrimestre, name='subir_csv_matricula_cuatrimestre'),

    # Eficiencia / Aprovechamiento / Indicadores
    path('administrador/eficiencia-3anios/', eficiencia_3anios_view, name='eficiencia_3anios'),
    path('administrador/aprovechamiento/', aprovechamiento_view, name='aprovechamiento'),
    path('administrador/aprovechamiento/descargar-plantilla/', descargar_plantilla_aprovechamiento, name='descargar_plantilla_aprovechamiento'),
    path('administrador/aprovechamiento/cargar/', cargar_aprovechamiento, name='cargar_aprovechamiento'),

    path('administrador/indicadores/reprobacion-desercion/', reprobacion_desercion_view, name='indicadores_generales'),
    path('administrador/indicadores/cargar/', cargar_indicadores_generales, name='cargar_indicadores_generales'),
    path('administrador/indicadores/descargar-plantilla/', descargar_plantilla_indicadores, name='descargar_plantilla_indicadores'),

    path('administrador/eficiencia-terminal/', eficiencia_terminal_view, name='eficiencia_terminal'),
    path('administrador/eficiencia-terminal/descargar-plantilla/', descargar_plantilla_eficiencia_terminal, name='descargar_plantilla_eficiencia_terminal'),
    path('administrador/eficiencia-terminal/cargar/', cargar_eficiencia_terminal, name='cargar_eficiencia_terminal'),

    path('administrador/matricula-h-nuevo-ingreso/', matricula_h_nuevo_ingreso_view, name='matricula_h_nuevo_ingreso'),
    path('administrador/matricula-h-nuevo-ingreso/descargar-plantilla/', descargar_plantilla_matricula_h_nuevo_ingreso, name='descargar_plantilla_matricula_h_nuevo_ingreso'),

    # Titulados histórico actual
    path('administrador/titulados-historico-actual/', titulados_historico_actual_view, name='titulados_historico_actual'),
    path('administrador/titulados-historico-actual/descargar-plantilla/', descargar_plantilla_titulados_historico_actual, name='descargar_plantilla_titulados_historico_actual'),

    # Evaluación docente
    path('administrador/evaluacion-docente-cuatrimestre/', evaluacion_docente_cuatrimestre_view, name='evaluacion_docente_cuatrimestre'),
    path('administrador/evaluacion-docente-concentrado/', evaluacion_docente_concentrado_view, name='evaluacion_docente_concentrado'),

    # Carreras
    path('administrador/subir-carreras/', subir_carreras_view, name='subir_carreras'),
    path('administrador/carreras/generar-plantilla/', generar_plantilla_carreras_csv, name='generar_plantilla_carreras'),
    path('administrador/carreras/generar-plantilla-nuevos/', generar_plantilla_nuevos_csv, name='generar_plantilla_nuevos'),
    path('administrador/carreras/exportar-pdf/', exportar_carreras_pdf, name='exportar_carreras_pdf'),

    # NUEVO CRUD Titulados (sin plantillas)
    path('administrador/titulados-crud/', tit_his_view, name='tit_his'),
    path('administrador/titulados-crud/api/', tit_his_api, name='tit_his_api'),

    # Tasa de Titulación
    path('administrador/tasa-de-titulacion/', tasa_de_titulacion_view, name='tasa_de_titulacion'),
    path('administrador/tasa-de-titulacion/descargar-plantilla/', descargar_plantilla_tasa_titulacion, name='descargar_plantilla_tasa_titulacion'),
    path('administrador/tasa-de-titulacion/subir-excel/', subir_excel_tasa_titulacion, name='subir_excel_tasa_titulacion'),

    # Titulados históricos (separado)
    path('administrador/titulados-historicos/', titulados_historicos_view, name='titulados_historicos'),
    path('administrador/titulados-historicos/descargar-plantilla/', descargar_plantilla_titulados_historicos, name='descargar_plantilla_titulados_historicos'),

    # TSU / Ingeniería
    path('administrador/titulados-tsu-ingenieria/', tti.titulados_tsu_inge_view, name='titulados_tsu_inge'),
    path('administrador/titulados-tsu/descargar-plantilla/', tti.descargar_plantilla_titulados_tsu, name='descargar_plantilla_titulados_tsu'),
    path('administrador/titulados-ing/descargar-plantilla/', tti.descargar_plantilla_titulados_ing, name='descargar_plantilla_titulados_ing'),
    path('administrador/titulados-tsu/subir-excel/', tti.subir_titulados_tsu_excel, name='subir_titulados_tsu_excel'),
    path('administrador/titulados-ing/subir-excel/', tti.subir_titulados_ing_excel, name='subir_titulados_ing_excel'),
]

# Archivos estáticos en modo desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
