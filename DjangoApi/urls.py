from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

# Vistas públicas (home)
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
from api.home.aprovechamiento_usuario_view import aprovechamiento_usuario_view




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
from api.Administrador.subir_carreras_view import (
    subir_carreras_view, generar_plantilla_csv,
    generar_plantilla_nuevos_csv, exportar_carreras_pdf
)
from api.Administrador.subir_carreras_view import exportar_carreras_pdf
# Tasa de Titulación
from api.Administrador.tasa_de_titulacion_view import (
    tasa_de_titulacion_view, descargar_plantilla_tasa_titulacion, subir_excel_tasa_titulacion
)

from api.Administrador.titulados_historicos_view import (
    titulados_historicos_view,
    descargar_plantilla_titulados_historicos
)



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

    # Vistas usuario normal
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
    path('evaluacion-docente-concentrado/', evaluacion_docente_concentrado_usuario_view, name='evaluacion_docente_concentrado_usuario'),

   
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
    path('matricula-cuatrimestre/', matricula_por_cuatrimestre_view, name='matricula_por_cuatrimestre'),
    path('matricula-cuatrimestre/descargar-plantilla/', descargar_plantilla_matricula_cuatrimestre, name='descargar_plantilla_matricula_cuatrimestre'),
    path('matricula-cuatrimestre/subir-csv/', subir_csv_matricula_cuatrimestre, name='subir_csv_matricula_cuatrimestre'),    path('administrador/descargar-plantilla-cuatrimestre/', descargar_plantilla_matricula_cuatrimestre, name='descargar_plantilla_cuatrimestre'),
    path('administrador/subir-csv-cuatrimestre/', subir_csv_matricula_cuatrimestre, name='subir_csv_cuatrimestre'),
    path('administrador/eficiencia-3anios/', eficiencia_3anios_view, name='eficiencia_3anios'),
    path('administrador/aprovechamiento/', aprovechamiento_view, name='aprovechamiento'),
    path('administrador/descargar-plantilla-aprovechamiento/', descargar_plantilla_aprovechamiento, name='descargar_plantilla_aprovechamiento'),
    path('administrador/cargar-aprovechamiento/', cargar_aprovechamiento, name='cargar_aprovechamiento'),
    path('reprobacion-desercion/', reprobacion_desercion_view, name='indicadores_generales'),
    path('cargar-indicadores-generales/', cargar_indicadores_generales, name='cargar_indicadores_generales'),
    path('descargar-plantilla-indicadores/', descargar_plantilla_indicadores, name='descargar_plantilla_indicadores'), 
    path('eficiencia-terminal/', eficiencia_terminal_view, name='eficiencia_terminal'),
    path('eficiencia-terminal/descargar-plantilla/', descargar_plantilla_eficiencia_terminal, name='descargar_plantilla_eficiencia_terminal'),
    path('eficiencia-terminal/cargar/', cargar_eficiencia_terminal, name='cargar_eficiencia_terminal'),
    path('administrador/matricula-h-nuevo-ingreso/', matricula_h_nuevo_ingreso_view, name='matricula_h_nuevo_ingreso'),
    path('administrador/descargar-plantilla-matricula-h-nuevo-ingreso/', descargar_plantilla_matricula_h_nuevo_ingreso, name='descargar_plantilla_matricula_h_nuevo_ingreso'),
    path('administrador/titulados-historico-actual/', titulados_historico_actual_view, name='titulados_historico_actual'),
    path('administrador/descargar-plantilla-titulados-historico-actual/', descargar_plantilla_titulados_historico_actual, name='descargar_plantilla_titulados_historico_actual'),
    path('evaluacion-docente-cuatrimestre/', evaluacion_docente_cuatrimestre_view, name='evaluacion_docente_cuatrimestre'),
    path('subir-carreras/', subir_carreras_view, name='subir_carreras'),
    path('plantilla-carreras/', generar_plantilla_csv, name='generar_plantilla_carreras'),
    path('plantilla-carreras-nuevos/', generar_plantilla_nuevos_csv, name='generar_plantilla_nuevos'),
    path('exportar-carreras-pdf/', exportar_carreras_pdf, name='exportar_carreras_pdf'),

    # Tasa de Titulación
    path('administrador/tasa-de-titulacion/', tasa_de_titulacion_view, name='tasa_de_titulacion'),
    path('administrador/descargar-plantilla-tasa-titulacion/', descargar_plantilla_tasa_titulacion, name='descargar_plantilla_tasa_titulacion'),
    path('administrador/subir-excel-tasa-titulacion/', subir_excel_tasa_titulacion, name='subir_excel_tasa_titulacion'),
    path('usuario/evaluacion-docente-cuatrimestre/', evaluacion_docente_cuatrimestre_usuario_view, name='Evaluacion_docente_cuatrimestre_usuario'),
    
    path('administrador/titulados-historico-actual/', titulados_historico_actual_view, name='titulados_historico_actual'),
   
    path('administrador/titulados-historico-actual/descargar-plantilla/', descargar_plantilla_titulados_historico_actual, name='descargar_plantilla_titulados_historico_actual'),

    path('administrador/evaluacion-docente-concentrado/', evaluacion_docente_concentrado_view, name='evaluacion_docente_concentrado'),
    
    # 👇 
    path('administrador/titulados-historicos/', titulados_historicos_view, name='titulados_historicos'),
    path('administrador/titulados-historicos/descargar-plantilla/', descargar_plantilla_titulados_historicos, name='descargar_plantilla_titulados_historicos'),
    
    
    ]




# Archivos estáticos en modo desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
