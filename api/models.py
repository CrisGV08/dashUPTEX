from django.db import models

class Usuarios(models.Model):
    usuario_id = models.CharField(max_length=20, primary_key=True)
    password = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.usuario_id} - {self.correo}"

    class Meta:
        verbose_name = "Administrador"
        verbose_name_plural = "Administradores"

#hola#
class CicloEscolar(models.Model):
    anio = models.IntegerField(primary_key=True)

    def __str__(self):
        return str(self.anio)


class Periodo(models.Model):
    clave = models.CharField(max_length=10, primary_key=True)  # Ej: 'E-A'
    nombre = models.CharField(max_length=50)  # Ej: 'Enero - Abril'

    def __str__(self):
        return self.nombre


class CicloPeriodo(models.Model):
    id = models.AutoField(primary_key=True)
    ciclo = models.ForeignKey(CicloEscolar, on_delete=models.CASCADE)
    periodo = models.ForeignKey(Periodo, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('ciclo', 'periodo')

    def __str__(self):
        return f"{self.ciclo.anio} - {self.periodo.clave}"


class ProgramaEducativoAntiguo(models.Model):
    id = models.CharField(max_length=10, primary_key=True)
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre


class ProgramaEducativoNuevo(models.Model):
    id = models.CharField(max_length=10, primary_key=True)
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre



class ProgramaEducativo(models.Model):
    TIPO_CHOICES = (
        ('TECNICO', 'Técnico'),
        ('INGENIERO', 'Ingeniero'),
    )

    id = models.CharField(max_length=10, primary_key=True)  # p.ej. 'ISC', 'TSUA'
    tipo = models.CharField(max_length=12, choices=TIPO_CHOICES)

    def __str__(self):
        return f"{self.id} - {self.tipo}"


class NuevoIngreso(models.Model):
    ciclo_periodo = models.ForeignKey(CicloPeriodo, on_delete=models.CASCADE)
    programa_antiguo = models.ForeignKey(ProgramaEducativoAntiguo, on_delete=models.CASCADE, null=True, blank=True)
    programa_nuevo = models.ForeignKey(ProgramaEducativoNuevo, on_delete=models.CASCADE, null=True, blank=True)

    examen = models.IntegerField(default=0)
    renoes = models.IntegerField(default=0)
    uaem_gem = models.IntegerField(default=0)
    pase_directo = models.IntegerField(default=0)

    @property
    def total(self):
        return self.examen + self.renoes + self.uaem_gem + self.pase_directo

    def __str__(self):
        prog = self.programa_antiguo or self.programa_nuevo
        return f"{self.ciclo_periodo} - {prog}"


class MatriculaNuevoIngreso(models.Model):
    ciclo_periodo = models.ForeignKey(CicloPeriodo, on_delete=models.CASCADE)
    programa_antiguo = models.ForeignKey(ProgramaEducativoAntiguo, on_delete=models.CASCADE, null=True, blank=True)
    programa_nuevo = models.ForeignKey(ProgramaEducativoNuevo, on_delete=models.CASCADE, null=True, blank=True)
    cantidad = models.IntegerField()

    def __str__(self):
        prog = self.programa_antiguo or self.programa_nuevo
        return f"{self.ciclo_periodo} - {prog}: {self.cantidad}"


class MatriculaHistorica(models.Model):
    ciclo_periodo = models.ForeignKey(CicloPeriodo, on_delete=models.CASCADE)
    programa_antiguo = models.ForeignKey(ProgramaEducativoAntiguo, on_delete=models.CASCADE, null=True, blank=True)
    programa_nuevo = models.ForeignKey(ProgramaEducativoNuevo, on_delete=models.CASCADE, null=True, blank=True)
    cantidad = models.IntegerField()

    def __str__(self):
        prog = self.programa_antiguo or self.programa_nuevo
        return f"{self.ciclo_periodo} - {prog}: {self.cantidad}"

class MatriculaPorGenero(models.Model):
    ciclo_periodo = models.ForeignKey(CicloPeriodo, on_delete=models.CASCADE)
    hombres = models.IntegerField(default=0)
    mujeres = models.IntegerField(default=0)

    @property
    def total(self):
        return self.hombres + self.mujeres

    def __str__(self):
        return f"{self.ciclo_periodo} - H:{self.hombres} M:{self.mujeres}"

class MatriculaPorCuatrimestre(models.Model):
    ciclo_periodo = models.ForeignKey(CicloPeriodo, on_delete=models.CASCADE)
    programa_antiguo = models.ForeignKey(ProgramaEducativoAntiguo, on_delete=models.CASCADE, null=True, blank=True)
    programa_nuevo = models.ForeignKey(ProgramaEducativoNuevo, on_delete=models.CASCADE, null=True, blank=True)
    cantidad = models.IntegerField()

    def __str__(self):
        prog = self.programa_antiguo or self.programa_nuevo
        return f"{self.ciclo_periodo} - {prog}: {self.cantidad}"

class AprovechamientoAcademico(models.Model):
    ciclo_periodo = models.ForeignKey(CicloPeriodo, on_delete=models.CASCADE)
    programa_antiguo = models.ForeignKey(ProgramaEducativoAntiguo, on_delete=models.CASCADE, null=True, blank=True)
    programa_nuevo = models.ForeignKey(ProgramaEducativoNuevo, on_delete=models.CASCADE, null=True, blank=True)
    promedio = models.DecimalField(max_digits=4, decimal_places=2)

    def __str__(self):
        prog = self.programa_antiguo or self.programa_nuevo
        return f"{self.ciclo_periodo} - {prog}: {self.promedio}"


class IndicadoresGenerales(models.Model):
    ciclo_periodo = models.OneToOneField(CicloPeriodo, on_delete=models.CASCADE)
    desertores = models.IntegerField()
    reprobados = models.IntegerField()
    egresados = models.IntegerField()

    @property
    def matricula_total(self):
        total = MatriculaPorCuatrimestre.objects.filter(ciclo_periodo=self.ciclo_periodo).aggregate(
            total=models.Sum('cantidad'))['total']
        return total or 0

    def porcentaje_desercion(self):
        total = self.matricula_total
        return round((self.desertores / total) * 100, 2) if total else 0.0

    def porcentaje_reprobacion(self):
        total = self.matricula_total
        return round((self.reprobados / total) * 100, 2) if total else 0.0

    def __str__(self):
        return f"{self.ciclo_periodo}: {self.matricula_total} alumnos"
  # Asegúrate de importar esto si no está

class EficienciaTerminal(models.Model):
    ciclo_periodo = models.ForeignKey(CicloPeriodo, on_delete=models.CASCADE)  # 🔁 Relación agregada
    programa_antiguo = models.ForeignKey('api.ProgramaEducativoAntiguo', on_delete=models.CASCADE, null=True, blank=True)
    programa_nuevo = models.ForeignKey('api.ProgramaEducativoNuevo', on_delete=models.CASCADE, null=True, blank=True)
    matricula_ingreso = models.IntegerField()
    egresados = models.IntegerField()

    @property
    def porcentaje_eficiencia(self):
        if self.matricula_ingreso > 0:
            return round((self.egresados / self.matricula_ingreso) * 100, 2)
        return 0.0

    def __str__(self):
        prog = self.programa_antiguo or self.programa_nuevo
        return f"{prog} - {self.ciclo_periodo}: {self.porcentaje_eficiencia}%"



#TÍTULADOS HISTORICO 1 Y 2

class GeneracionCarrera(models.Model):
    programa_antiguo = models.ForeignKey('ProgramaEducativoAntiguo', on_delete=models.CASCADE, null=True, blank=True)
    programa_nuevo = models.ForeignKey('ProgramaEducativoNuevo', on_delete=models.CASCADE, null=True, blank=True)

    fecha_ingreso = models.DateField()  # Ejemplo: 2014-05-01 para "may-14"
    fecha_egreso = models.DateField()  # Ejemplo: 2017-12-01 para "dic-17"

    ingreso_hombres = models.IntegerField(default=0)
    ingreso_mujeres = models.IntegerField(default=0)

    egresados_cohorte_h = models.IntegerField(default=0)
    egresados_cohorte_m = models.IntegerField(default=0)

    egresados_rezagados_h = models.IntegerField(default=0)
    egresados_rezagados_m = models.IntegerField(default=0)

    titulados_h = models.IntegerField(default=0)
    titulados_m = models.IntegerField(default=0)

    registrados_dgp_h = models.IntegerField(default=0)
    registrados_dgp_m = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Generación por Carrera"
        verbose_name_plural = "Generaciones por Carrera"
        ordering = ['fecha_ingreso']

    # ---- MÉTODOS CALCULADOS ----

    @property
    def total_ingreso(self):
        return self.ingreso_hombres + self.ingreso_mujeres

    @property
    def total_egresados(self):
        return (self.egresados_cohorte_h + self.egresados_cohorte_m +
                self.egresados_rezagados_h + self.egresados_rezagados_m)

    @property
    def total_titulados(self):
        return self.titulados_h + self.titulados_m

    @property
    def total_dgp(self):
        return self.registrados_dgp_h + self.registrados_dgp_m

    @property
    def tasa_titulacion(self):
        ingresos = self.total_ingreso
        return round((self.total_titulados / ingresos) * 100, 2) if ingresos else 0.0

    def __str__(self):
        prog = self.programa_antiguo or self.programa_nuevo
        return f"{prog} ({self.fecha_ingreso.strftime('%m-%Y')} - {self.fecha_egreso.strftime('%m-%Y')})"






















class TituladosHistoricos(models.Model):
    SEMESTRE_CHOICES = (
        (5, "TSU"),
        (10, "Ingeniería"),
    )

    anio_ingreso = models.IntegerField()
    anio_egreso = models.IntegerField()

    # ← NUEVO
    semestre = models.IntegerField(choices=SEMESTRE_CHOICES, default=5)

    programa_antiguo = models.ForeignKey('ProgramaEducativoAntiguo', on_delete=models.CASCADE, null=True, blank=True)
    programa_nuevo = models.ForeignKey('ProgramaEducativoNuevo', on_delete=models.CASCADE, null=True, blank=True)

    titulados_hombres = models.IntegerField(default=0)
    titulados_mujeres = models.IntegerField(default=0)

    registrados_dgp_h = models.IntegerField(default=0)
    registrados_dgp_m = models.IntegerField(default=0)

    @property
    def total_titulados(self):
        return self.titulados_hombres + self.titulados_mujeres

    @property
    def total_dgp(self):
        return self.registrados_dgp_h + self.registrados_dgp_m

    def __str__(self):
        prog = self.programa_antiguo or self.programa_nuevo
        return f"{prog} - Ingreso {self.anio_ingreso} / Egreso {self.anio_egreso}"





class TasaTitulacion(models.Model):
    anio_ingreso = models.IntegerField()

    programa_antiguo = models.ForeignKey('ProgramaEducativoAntiguo', on_delete=models.CASCADE, null=True, blank=True)
    programa_nuevo = models.ForeignKey('ProgramaEducativoNuevo', on_delete=models.CASCADE, null=True, blank=True)

    matricula_ingreso = models.IntegerField(default=0)
    egresados = models.IntegerField(default=0)
    eficiencia_terminal_porcentaje = models.FloatField(default=0.0)
    titulados = models.IntegerField(default=0)
    tasa_titulacion = models.FloatField(default=0.0)

    def __str__(self):
        prog = self.programa_antiguo or self.programa_nuevo
        return f"{prog} - {self.anio_ingreso}"






class SeguimientoLaboral(models.Model):
    programa_antiguo = models.ForeignKey('ProgramaEducativoAntiguo', on_delete=models.CASCADE, null=True, blank=True)
    programa_nuevo = models.ForeignKey('ProgramaEducativoNuevo', on_delete=models.CASCADE, null=True, blank=True)

    fecha_ingreso = models.DateField()
    fecha_egreso = models.DateField()

    ingreso_h = models.IntegerField(default=0)
    ingreso_m = models.IntegerField(default=0)

    egresados_total = models.IntegerField(default=0)
    titulados_total = models.IntegerField(default=0)
    registrados_dgp_total = models.IntegerField(default=0)

    egresados_trabajan = models.IntegerField(default=0)
    egresados_trabajan_area = models.IntegerField(default=0)

    indice_egreso = models.FloatField(default=0.0)         # %
    indice_titulacion = models.FloatField(default=0.0)     # %

    def __str__(self):
        prog = self.programa_antiguo or self.programa_nuevo
        return f"{prog} - ${self.fecha_ingreso.strftime('%m-%Y')} / ${self.fecha_egreso.strftime('%m-%Y')}"



class EvaluacionDocenteConcentrado(models.Model):
    ciclo = models.CharField(max_length=20, unique=True)
    promedio = models.FloatField()
    mal = models.IntegerField(default=0)
    regular = models.IntegerField(default=0)
    bien = models.IntegerField(default=0)
    muy_bien = models.IntegerField(default=0)
    excelente = models.IntegerField(default=0)
    total = models.IntegerField(default=0)

    def _str_(self):
        return f"{self.ciclo} - {self.promedio}"



class EvaluacionDocenteCuatrimestre(models.Model):
    ciclo_periodo = models.ForeignKey('CicloPeriodo', on_delete=models.CASCADE, unique=True)
    promedio_general = models.FloatField()

    def __str__(self):
        return f"{self.ciclo_periodo} - {self.promedio_general}"


# --------------------------
# TITULADOS POR TSU / INGENIERÍA (CRUD independiente)
# --------------------------
class TituladosTSUIng(models.Model):
    NIVEL_CHOICES = (
        ("TSU", "TSU"),
        ("ING", "Ingeniería"),
    )

    nivel = models.CharField(max_length=3, choices=NIVEL_CHOICES, db_index=True)

    programa_antiguo = models.ForeignKey(
        'ProgramaEducativoAntiguo',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name="titulados_tsu_ing_antiguo",
        db_index=True,
    )
    programa_nuevo = models.ForeignKey(
        'ProgramaEducativoNuevo',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name="titulados_tsu_ing_nuevo",
        db_index=True,
    )

    fecha_ingreso = models.DateField(db_index=True)
    fecha_egreso  = models.DateField(db_index=True)

    ingreso_hombres = models.IntegerField(default=0)
    ingreso_mujeres = models.IntegerField(default=0)

    egresados_cohorte_h = models.IntegerField(default=0)
    egresados_cohorte_m = models.IntegerField(default=0)

    egresados_rezagados_h = models.IntegerField(default=0)
    egresados_rezagados_m = models.IntegerField(default=0)

    titulados_h = models.IntegerField(default=0)
    titulados_m = models.IntegerField(default=0)

    registrados_dgp_h = models.IntegerField(default=0)
    registrados_dgp_m = models.IntegerField(default=0)

    creado_en   = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Titulados TSU/ING"
        verbose_name_plural = "Titulados TSU/ING"
        ordering = ["fecha_ingreso", "fecha_egreso", "nivel"]
        constraints = [
            models.CheckConstraint(
                name="tsui_programa_xor",
                check=(
                    (models.Q(programa_antiguo__isnull=False, programa_nuevo__isnull=True) |
                     models.Q(programa_antiguo__isnull=True,  programa_nuevo__isnull=False))
                ),
            ),
            models.CheckConstraint(
                name="tsui_no_negativos",
                check=models.Q(ingreso_hombres__gte=0) &
                      models.Q(ingreso_mujeres__gte=0) &
                      models.Q(egresados_cohorte_h__gte=0) &
                      models.Q(egresados_cohorte_m__gte=0) &
                      models.Q(egresados_rezagados_h__gte=0) &
                      models.Q(egresados_rezagados_m__gte=0) &
                      models.Q(titulados_h__gte=0) &
                      models.Q(titulados_m__gte=0) &
                      models.Q(registrados_dgp_h__gte=0) &
                      models.Q(registrados_dgp_m__gte=0),
            ),
            models.UniqueConstraint(
                name="tsui_unico_gen_prog_nivel",
                fields=["nivel", "fecha_ingreso", "fecha_egreso", "programa_antiguo", "programa_nuevo"],
            ),
        ]
        indexes = [
            models.Index(fields=["nivel", "fecha_ingreso"]),
            models.Index(fields=["nivel", "fecha_egreso"]),
        ]

    @property
    def total_ingreso(self) -> int:
        return (self.ingreso_hombres or 0) + (self.ingreso_mujeres or 0)

    @property
    def total_egresados(self) -> int:
        return ((self.egresados_cohorte_h or 0) + (self.egresados_cohorte_m or 0) +
                (self.egresados_rezagados_h or 0) + (self.egresados_rezagados_m or 0))

    @property
    def total_titulados(self) -> int:
        return (self.titulados_h or 0) + (self.titulados_m or 0)

    @property
    def total_dgp(self) -> int:
        return (self.registrados_dgp_h or 0) + (self.registrados_dgp_m or 0)

    @property
    def tasa_titulacion(self) -> float:
        ing = self.total_ingreso
        if ing <= 0:
            return 0.0
        return round((self.total_titulados / ing) * 100.0, 2)

    def programa_nombre(self) -> str:
        p = self.programa_antiguo or self.programa_nuevo
        return getattr(p, "nombre", "SIN PROGRAMA")

    def programa_id(self) -> str:
        p = self.programa_antiguo or self.programa_nuevo
        return getattr(p, "id", "")

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.fecha_egreso < self.fecha_ingreso:
            raise ValidationError("La fecha de egreso no puede ser menor que la fecha de ingreso.")
        if self.nivel not in dict(self.NIVEL_CHOICES):
            raise ValidationError("Nivel inválido. Usa 'TSU' o 'ING'.")

    def __str__(self):
        prog = self.programa_antiguo or self.programa_nuevo
        pnom = getattr(prog, "nombre", "SIN PROGRAMA")
        return f"[{self.nivel}] {pnom} | {self.fecha_ingreso:%m-%Y} → {self.fecha_egreso:%m-%Y} (tasa {self.tasa_titulacion}%)"
