# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Administrador(models.Model):
    folio = models.CharField(primary_key=True, max_length=7)
    nombrepila = models.CharField(max_length=30)
    primerapellido = models.CharField(max_length=30)
    segundoapellido = models.CharField(max_length=30, blank=True, null=True)
    correo = models.CharField(unique=True, max_length=40)
    telefono = models.CharField(unique=True, max_length=16)

    class Meta:
        managed = False
        db_table = 'administrador'


class Cita(models.Model):
    folio = models.CharField(primary_key=True, max_length=7)
    fecha = models.DateField()
    hora = models.TimeField()
    motivo = models.CharField(max_length=120)
    propietario = models.ForeignKey('Propietario', models.DO_NOTHING, db_column='propietario')
    mascota = models.ForeignKey('Mascota', models.DO_NOTHING, db_column='mascota')
    veterinario = models.ForeignKey('Veterinario', models.DO_NOTHING, db_column='veterinario')
    estado = models.ForeignKey('EdoCita', models.DO_NOTHING, db_column='estado')

    class Meta:
        managed = False
        db_table = 'cita'


class Consulta(models.Model):
    numero = models.AutoField(primary_key=True)
    sintomas = models.CharField(max_length=150)
    freccardiaca = models.IntegerField()
    frecrespiratoria = models.IntegerField()
    temperatura = models.DecimalField(max_digits=5, decimal_places=2)
    observaciones = models.CharField(max_length=200)
    diagnostico = models.CharField(max_length=150)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    cita = models.OneToOneField(Cita, models.DO_NOTHING, db_column='cita')
    expediente = models.ForeignKey('Expediente', models.DO_NOTHING, db_column='expediente')

    class Meta:
        managed = False
        db_table = 'consulta'


class EdoCita(models.Model):
    clave = models.CharField(primary_key=True, max_length=4)
    nombre = models.CharField(unique=True, max_length=15)

    class Meta:
        managed = False
        db_table = 'edo_cita'

class EdoUsuario(models.Model):
    clave = models.CharField(primary_key=True, max_length=1)
    nombre = models.CharField(max_length=8, unique=True)

    class Meta:
        managed = False
        db_table = 'edo_usuario'

class EdoHosp(models.Model):
    clave = models.CharField(primary_key=True, max_length=3)
    nombre = models.CharField(unique=True, max_length=13)

    class Meta:
        managed = False
        db_table = 'edo_hosp'


class EdoMasc(models.Model):
    clave = models.CharField(primary_key=True, max_length=4)
    nombre = models.CharField(unique=True, max_length=13)

    class Meta:
        managed = False
        db_table = 'edo_masc'


class Especialidad(models.Model):
    clave = models.CharField(primary_key=True, max_length=7)
    nombre = models.CharField(unique=True, max_length=30)
    descripcion = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'especialidad'


class Especie(models.Model):
    clave = models.CharField(primary_key=True, max_length=7)
    nombre = models.CharField(unique=True, max_length=25)

    class Meta:
        managed = False
        db_table = 'especie'


class Expediente(models.Model):
    mascota = models.OneToOneField('Mascota', models.DO_NOTHING, db_column='mascota', primary_key=True)
    fechaapertura = models.DateField()

    class Meta:
        managed = False
        db_table = 'expediente'


class Hospitalizacion(models.Model):
    numero = models.AutoField(primary_key=True)
    diagnoingreso = models.CharField(max_length=150)
    fechaingreso = models.DateField()
    horaingreso = models.TimeField()
    obsergenerales = models.CharField(max_length=200)
    fechaalta = models.DateField(blank=True, null=True)
    horaalta = models.TimeField(blank=True, null=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    consulta = models.ForeignKey(Consulta, models.DO_NOTHING, db_column='consulta')
    estado = models.ForeignKey(EdoHosp, models.DO_NOTHING, db_column='estado')
    veterinario = models.ForeignKey('Veterinario', models.DO_NOTHING, db_column='veterinario')
    expediente = models.ForeignKey(Expediente, models.DO_NOTHING, db_column='expediente')

    class Meta:
        managed = False
        db_table = 'hospitalizacion'


class Mascota(models.Model):
    folio = models.CharField(primary_key=True, max_length=7)
    nombre = models.CharField(max_length=50)
    sexo = models.CharField(max_length=1)
    fechanacimiento = models.DateField()
    peso = models.DecimalField(max_digits=5, decimal_places=2)
    color = models.CharField(max_length=30)
    alergias = models.CharField(max_length=100, blank=True, null=True)
    caracunica = models.CharField(max_length=50)
    propietario = models.ForeignKey('Propietario', models.DO_NOTHING, db_column='propietario')
    especie = models.ForeignKey(Especie, models.DO_NOTHING, db_column='especie')
    raza = models.ForeignKey('Raza', models.DO_NOTHING, db_column='raza')
    estado = models.ForeignKey(EdoMasc, models.DO_NOTHING, db_column='estado')
    imagen = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'mascota'


class Medicamento(models.Model):
    clave = models.CharField(primary_key=True, max_length=7)
    nombre = models.CharField(unique=True, max_length=50)
    descripcion = models.CharField(max_length=90)
    precio = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'medicamento'


class Pago(models.Model):
    codigo = models.AutoField(primary_key=True)
    fecha = models.DateField()
    hora = models.TimeField()
    pagofinal = models.DecimalField(max_digits=10, decimal_places=2)
    consulta = models.ForeignKey(Consulta, models.DO_NOTHING, db_column='consulta')
    hospitalizacion = models.ForeignKey(Hospitalizacion, models.DO_NOTHING, db_column='hospitalizacion', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pago'


class Propietario(models.Model):
    folio = models.CharField(primary_key=True, max_length=7)
    nombrepila = models.CharField(max_length=30)
    primerapellido = models.CharField(max_length=30)
    segundoapellido = models.CharField(max_length=30, blank=True, null=True)
    dircalle = models.CharField(max_length=30)
    dirnum = models.CharField(max_length=10)
    dircolonia = models.CharField(max_length=30)
    correo = models.CharField(unique=True, max_length=40)

    class Meta:
        managed = False
        db_table = 'propietario'


class Raza(models.Model):
    clave = models.CharField(primary_key=True, max_length=8)
    nombre = models.CharField(max_length=35)
    especie = models.ForeignKey(Especie, models.DO_NOTHING, db_column='especie')

    class Meta:
        managed = False
        db_table = 'raza'


class Recepcionista(models.Model):
    folio = models.CharField(primary_key=True, max_length=7)
    nombrepila = models.CharField(max_length=30)
    primerapellido = models.CharField(max_length=30)
    segundoapellido = models.CharField(max_length=30, blank=True, null=True)
    correo = models.CharField(unique=True, max_length=40)
    telefono = models.CharField(unique=True, max_length=16)

    class Meta:
        managed = False
        db_table = 'recepcionista'


class Receta(models.Model):
    numero = models.AutoField(primary_key=True)
    fecha = models.DateField()
    instrugenerales = models.CharField(max_length=150)
    hospitalizacion = models.OneToOneField(Hospitalizacion, models.DO_NOTHING, db_column='hospitalizacion', blank=True, null=True)
    consulta = models.OneToOneField(Consulta, models.DO_NOTHING, db_column='consulta', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'receta'


class ServCons(models.Model):
    id = models.AutoField(primary_key=True)
    servicio = models.ForeignKey('Servicio', models.DO_NOTHING, db_column='servicio')
    consulta = models.ForeignKey(Consulta, models.DO_NOTHING, db_column='consulta')
    cantidad = models.IntegerField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'serv_cons'
        constraints = [
            models.UniqueConstraint(
                fields=['servicio', 'consulta'],
                name='unique_serv_cons'
            )
        ]


class ServHosp(models.Model):
    id = models.AutoField(primary_key=True)
    servicio = models.ForeignKey('Servicio', models.DO_NOTHING, db_column='servicio')
    hospitalizacion = models.ForeignKey(Hospitalizacion, models.DO_NOTHING, db_column='hospitalizacion')
    cantidad = models.IntegerField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'serv_hosp'
        constraints = [
            models.UniqueConstraint(
                fields=['servicio', 'hospitalizacion'],
                name='unique_serv_hosp'
            )
        ]


class Servicio(models.Model):
    clave = models.CharField(primary_key=True, max_length=7)
    nombre = models.CharField(unique=True, max_length=35)
    descripcion = models.CharField(max_length=150)
    costo = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'servicio'


class SignosVitales(models.Model):
    numero = models.AutoField(primary_key=True)
    fecha = models.DateField()
    freccardiaca = models.IntegerField()
    frecrespiratoria = models.IntegerField()
    temperatura = models.DecimalField(max_digits=5, decimal_places=2)
    hospitalizacion = models.ForeignKey(Hospitalizacion, models.DO_NOTHING, db_column='hospitalizacion')

    class Meta:
        managed = False
        db_table = 'signos_vitales'


class Telefono(models.Model):
    clave = models.AutoField(primary_key=True)
    numprincipal = models.CharField(unique=True, max_length=16)
    numsecundario = models.CharField(unique=True, max_length=16, blank=True, null=True)
    propietario = models.ForeignKey(Propietario, models.DO_NOTHING, db_column='propietario')

    class Meta:
        managed = False
        db_table = 'telefono'


class TipoUsuario(models.Model):
    codigo = models.CharField(primary_key=True, max_length=3)
    nombre = models.CharField(unique=True, max_length=13)

    class Meta:
        managed = False
        db_table = 'tipo_usuario'


class Tratamiento(models.Model):
    id = models.AutoField(primary_key=True)
    receta = models.ForeignKey(Receta, models.DO_NOTHING, db_column='receta')
    cantidad = models.IntegerField(blank=True, null=True)
    medicamento = models.ForeignKey(Medicamento, models.DO_NOTHING, db_column='medicamento')
    notas = models.CharField(max_length=50)
    dosis = models.CharField(max_length=30)
    frecuencia = models.CharField(max_length=30)
    duracion = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'tratamiento'
        constraints = [
            models.UniqueConstraint(
                fields=['receta', 'medicamento'],
                name='unique_tratamiento'
            )
        ]


class Usuario(models.Model):
    numero = models.AutoField(primary_key=True)
    usuario = models.CharField(unique=True, max_length=20)
    contrasena = models.CharField(max_length=255)
    tipo = models.ForeignKey(TipoUsuario, models.DO_NOTHING, db_column='tipo')
    propietario = models.OneToOneField(Propietario, models.DO_NOTHING, db_column='propietario', blank=True, null=True)
    recepcionista = models.OneToOneField(Recepcionista, models.DO_NOTHING, db_column='recepcionista', blank=True, null=True)
    veterinario = models.OneToOneField('Veterinario', models.DO_NOTHING, db_column='veterinario', blank=True, null=True)
    administrador = models.OneToOneField(Administrador, models.DO_NOTHING, db_column='administrador', blank=True, null=True)
    imagen = models.CharField(max_length=255, blank=True, null=True)
    
    estado = models.ForeignKey('EdoUsuario', on_delete=models.DO_NOTHING, db_column='estado')


    class Meta:
        managed = False
        db_table = 'usuario'

    
    @property
    def nombre_real(self):
        if self.tipo.codigo == 'VET' and self.veterinario:
            v = self.veterinario
            return f"{v.nombrepila} {v.primerapellido}"

        if self.tipo.codigo == 'PRO' and self.propietario:
            p = self.propietario
            return f"{p.nombrepila} {p.primerapellido}"

        if self.tipo.codigo == 'REC' and self.recepcionista:
            r = self.recepcionista
            return f"{r.nombrepila} {r.primerapellido} "

        if self.tipo.codigo == 'ADM' and self.administrador:
            a = self.administrador
            return f"{a.nombrepila} {a.primerapellido}"

        return ""

class Veterinario(models.Model):
    folio = models.CharField(primary_key=True, max_length=7)
    nombrepila = models.CharField(max_length=30)
    primerapellido = models.CharField(max_length=30)
    segundoapellido = models.CharField(max_length=30, blank=True, null=True)
    correo = models.CharField(unique=True, max_length=40)
    telefono = models.CharField(unique=True, max_length=16)
    cedula = models.CharField(unique=True, max_length=8)
    especialidad = models.ForeignKey(Especialidad, models.DO_NOTHING, db_column='especialidad')

    class Meta:
        managed = False
        db_table = 'veterinario'
