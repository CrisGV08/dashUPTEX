from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

# Vistas públicas (home)
from api.home.home_views import (
    home_view, home_calificaciones, home_aprobados, home_reprobados,
    home_promedios, home_mapa
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
# Login
from api.login.login_views import login_view, logout_view

# Administrador
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
    importar_matricula_cuatrimestres,
    matricula_por_cuatrimestre_view,
    descargar_plantilla_matricula_cuatrimestre,
    subir_csv_matricula_cuatrimestre
)
from api.Administrador.eficiencia3anios_views import eficiencia_3anios_view
from api.Administrador.aprovechamiento_views import aprovechamiento_view
from api.Administrador.aprovechamiento_tools import descargar_plantilla_aprovechamiento
from api.Administrador.indicadores_generales_view import (
    indicadores_generales_view,
    descargar_plantilla_indicadores,
    subir_csv_indicadores
)
from api.Administrador.eficiencia_terminal_view import eficiencia_terminal_view
from api.Administrador.eficiencia_terminal_tools import descargar_plantilla_eficiencia
from api.Administrador.Matricula_H_Nuevo_Ingreso_view import (
    matricula_h_nuevo_ingreso_view,
    descargar_plantilla_matricula_h_nuevo_ingreso
)
from api.Administrador.titulados_historico_actual_view import (
    titulados_historico_actual_view,
    descargar_plantilla_titulados_historico_actual
)


from api.Administrador.evaluacion_docente_cuatrimestre_view import evaluacion_docente_cuatrimestre_view




urlpatterns = [
    # Home públicas
    path('', home_view, name='index'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('calificaciones/', home_calificaciones, name='calificaciones'),
    path('aprobados/', home_aprobados, name='aprobados'),
    path('reprobados/', home_reprobados, name='reprobados'),
    path('promedios/', home_promedios, name='promedios'),
    path('mapa/', home_mapa, name='mapa'),

    # Vistas usuario normal (indicadores)
    path('usuario/examen-admision/', examen_admision_usuario_view, name='examen_admision_usuario'),
    path('usuario/matricula-historica/', matricula_historica_usuario_view, name='matricula_historica_usuario'),
    path('usuario/matricula-genero/', matricula_por_genero_usuario_view, name='matricula_por_genero_usuario'),
    path('usuario/matricula-anual/', matricula_anual_usuario_view, name='matricula_anual_usuario'),
    path('usuario/matricula-cuatrimestre/', matricula_cuatrimestre_usuario_view, name='matricula_cuatrimestre_usuario'),
    path('usuario/matricula-nuevo-ingreso/', matricula_h_nuevo_ingreso_usuario_view, name='matricula_h_nuevo_ingreso_usuario'),
    path('usuario/aprovechamiento/', aprovechamiento_usuario_view, name='aprovechamiento_usuario'),
    path('administrador/gestionar-usuarios/', gestionar_usuarios, name='gestionar_usuarios'),
    path('usuario/indicadores-generales/', indicadores_generales_usuario_view, name='indicadores_generales_usuario'),
    path('usuario/eficiencia-terminal/', eficiencia_terminal_usuario_view, name='eficiencia_terminal_usuario'),
    path('usuario/titulados-historicos-actual/', titulados_historicos_actual_usuario_view, name='titulados_historicos_actual_usuario'),
   
    # Administrador
    path('administrador/', administrador_view, name='administrador'),
    path('administrador/subir-calificaciones/', subir_calificaciones, name='subir_calificaciones'),
    path('administrador/gestionar-usuarios/', gestionar_usuarios, name='gestionar_usuarios'),
    path('administrador/generar-plantilla/', generar_plantilla_csv, name='generar_plantilla_csv'),
    path('administrador/egresados/', egresados_view, name='egresados'),
    path('administrador/examen-admision/', examen_admision_view, name='examen_admision'),
    path('administrador/descargar-plantilla-nuevo-ingreso/', descargar_plantilla_nuevo_ingreso, name='descargar_plantilla_nuevo_ingreso'),
    path('administrador/subir-csv-nuevo-ingreso/', subir_csv_nuevo_ingreso, name='subir_csv_nuevo_ingreso'),
    path('administrador/matricula-genero/', matriculagenero_views.matriculagenero, name='matricula_por_genero'),
    path('administrador/matricula-historica/', matricula_historica, name='matricula_historica'),
    path('administrador/matricula-por-anio/', matricula_por_anio_view, name='matricula_por_anio'),
    path('administrador/matricula-cuatrimestre/', matricula_por_cuatrimestre_view, name='matricula_por_cuatrimestre'),
    path('administrador/importar-matricula-cuatrimestres/', importar_matricula_cuatrimestres, name='importar_matricula_cuatrimestres'),
    path('administrador/descargar-plantilla-cuatrimestre/', descargar_plantilla_matricula_cuatrimestre, name='descargar_plantilla_cuatrimestre'),
    path('administrador/subir-csv-cuatrimestre/', subir_csv_matricula_cuatrimestre, name='subir_csv_cuatrimestre'),
    path('administrador/eficiencia-3anios/', eficiencia_3anios_view, name='eficiencia_3anios'),
    path('administrador/aprovechamiento/', aprovechamiento_view, name='aprovechamiento'),
    path('administrador/descargar-plantilla-aprovechamiento/', descargar_plantilla_aprovechamiento, name='descargar_plantilla_aprovechamiento'),
    path('administrador/indicadores-generales/', indicadores_generales_view, name='indicadores_generales'),
    path('administrador/descargar-plantilla-indicadores/', descargar_plantilla_indicadores, name='descargar_plantilla_indicadores'),
    path('administrador/subir-csv-indicadores/', subir_csv_indicadores, name='subir_csv_indicadores'),
    path('eficiencia-terminal/', eficiencia_terminal_view, name='eficiencia_terminal'),
    path('descargar-plantilla-eficiencia/', descargar_plantilla_eficiencia, name='descargar_plantilla_eficiencia'),
    path('administrador/matricula-h-nuevo-ingreso/', matricula_h_nuevo_ingreso_view, name='matricula_h_nuevo_ingreso'),
    path('administrador/descargar-plantilla-matricula-h-nuevo-ingreso/', descargar_plantilla_matricula_h_nuevo_ingreso, name='descargar_plantilla_matricula_h_nuevo_ingreso'),
    path('administrador/titulados-historico-actual/', titulados_historico_actual_view, name='titulados_historico_actual'),
    path('administrador/descargar-plantilla-titulados-historico-actual/', descargar_plantilla_titulados_historico_actual, name='descargar_plantilla_titulados_historico_actual'),


    path(
        'evaluacion-docente-cuatrimestre/',
        evaluacion_docente_cuatrimestre_view,
        name='evaluacion_docente_cuatrimestre'
    ),


]

# Archivos estáticos en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)    