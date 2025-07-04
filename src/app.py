import os
import sys

# Obtén la ruta del directorio padre de 'src' (que es 'Flask_proyecto')
# y añádela al sys.path para que Python pueda encontrar 'src' como un paquete.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Ahora tus importaciones deberían funcionar correctamente
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
from pymongo import MongoClient
from bson.objectid import ObjectId
from pymongo.errors import DuplicateKeyError
import json
import pandas as pd

# Importar el diccionario 'config' que contiene tus clases de configuración
from .config import config 

# Models (Ahora deberían resolverse correctamente debido al sys.path modificado)
from src.models.ModelUser import ModelUser
from src.models.ModelCita import ModelCita
from src.models.ModelMascota import ModelMascota
from src.models.ModelVeterinarios import ModelVeterinarios
from src.models.ModelHorarioVeterinario import ModelHorarioVeterinario

# Entities (Ahora deberían resolverse correctamente)
from src.models.entities.User import User
from src.models.entities.Cita import Cita
from src.models.entities.Mascota import Mascota
from src.models.entities.Veterinarios import Veterinarios
from src.models.entities.HorarioVeterinario import HorarioVeterinario

app = Flask(__name__)

# Cargar la configuración de Flask desde el objeto DevelopmentConfig
app.config.from_object(config['development'])

# Inicializa el cliente de MongoDB
mongo_client = MongoClient(app.config['MONGO_URI'])
# Obtén la base de datos específica utilizando el nombre de DB de la configuración
db = mongo_client[app.config['MONGO_DB_NAME']]

login_manager_app = LoginManager(app)
login_manager_app.login_view = 'login_route'
login_manager_app.init_app(app)


@login_manager_app.user_loader
def load_user(id_with_type):
    try:
        id_parts = id_with_type.split('_')
        user_type_prefix = id_parts[0]
        actual_id = id_parts[1] # <--- ¡Aquí ocurre el IndexError si id_parts solo tiene un elemento!

        if user_type_prefix == 'U':
            return ModelUser.get_by_id(db, actual_id)
        elif user_type_prefix == 'V':
            return ModelVeterinarios.get_by_id(db, actual_id)
        return None
    except IndexError:
        print(f"DEBUG: id_with_type '{id_with_type}' no tiene el formato esperado (prefijo_id).")
        # Aquí puedes agregar lógica para intentar cargar el usuario si sabes que es un ID antiguo sin prefijo
        if ObjectId.is_valid(id_with_type):
            # Intentar como usuario (asumiendo que los usuarios son el tipo principal sin prefijo si los hay)
            user = ModelUser.get_by_id(db, id_with_type)
            if user:
                print(f"DEBUG: Usuario antiguo con ID '{id_with_type}' cargado.")
                return user
            # Si no es usuario, intentar como veterinario (si también pueden existir sin prefijo)
            veterinario = ModelVeterinarios.get_by_id(db, id_with_type)
            if veterinario:
                print(f"DEBUG: Veterinario antiguo con ID '{id_with_type}' cargado.")
                return veterinario
        return None
    except Exception as e:
        print(f"Error inesperado en load_user para ID '{id_with_type}': {e}")
        return None

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_type = request.form.get('login_type')
        username = request.form['username']
        password = request.form['password']

        if login_type == 'user':
            user_obj = User(_id=None, username=username, password=password) # _id=None es temporal aquí
            logged_entity = ModelUser.login(db, user_obj) # Este método debe devolver un objeto User con _id

            if logged_entity:
                # No necesitas logged_entity.id = f'U_{logged_entity._id}' aquí.
                # Flask-Login llamará automáticamente a logged_entity.get_id()
                # que ya devuelve "U_ObjectIdString".
                login_user(logged_entity) 
                flash('Login de usuario exitoso!', 'success')
                return redirect(url_for('home'))
            else:
                flash("Credenciales de usuario inválidas.", 'danger')
                return render_template('auth/login.html', selected_type='user', username=username)

        elif login_type == 'veterinarian':
            matricula_profesional = request.form['matricula_profesional']
            vet_obj = Veterinarios(_id=None, username=username, password=password, matricula_profesional=matricula_profesional)
            logged_entity = ModelVeterinarios.login(db, vet_obj)
            
            if logged_entity:
                # No necesitas logged_entity.id = f'V_{logged_entity._id}' aquí.
                login_user(logged_entity)
                flash('Login de veterinario exitoso!', 'success')
                return redirect(url_for('home_veterinarios'))
            else:
                flash("Credenciales de veterinario inválidas o matrícula profesional incorrecta.", 'danger')
                return render_template('auth/login.html', selected_type='veterinarian', username=username, matricula_profesional=matricula_profesional)
        else:
            flash("Tipo de inicio de sesión no especificado.", 'danger')
            return render_template('auth/login.html')
    else:
        return render_template('auth/login.html', selected_type='user')
    
@app.route('/veterinarios_register', methods=['GET', 'POST'])
def veterinarios_register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        matricula_profesional = request.form['matricula_profesional']
        nombre = request.form['nombre']
        apellido_paterno = request.form['apellido_paterno']
        apellido_materno = request.form.get('apellido_materno', None)
        telefono = request.form.get('telefono', None)
        email = request.form.get('email', None)

        hashed_password = Veterinarios.generate_password(password)

        # _id=None para que MongoDB genere uno nuevo
        new_veterinario = Veterinarios(_id=None, username=username, password=hashed_password, 
                                       matricula_profesional=matricula_profesional, nombre=nombre, 
                                       apellido_paterno=apellido_paterno, apellido_materno=apellido_materno, 
                                       telefono=telefono, email=email)

        if ModelVeterinarios.register(db, new_veterinario):
            flash('Veterinario registrado con éxito. ¡Ya puedes iniciar sesión!', 'success')
            return redirect(url_for('login'))
        else:
            flash('Error al registrar veterinario. Posiblemente el nombre de usuario o la matrícula profesional ya existen.', 'danger')
            return render_template('auth/veterinarios_register.html',
                                   username=username,
                                   matricula_profesional=matricula_profesional,
                                   nombre=nombre,
                                   apellido_paterno=apellido_paterno,
                                   apellido_materno=apellido_materno,
                                   telefono=telefono,
                                   email=email)
    else:
        return render_template('auth/veterinarios_register.html')
    
@app.route('/home_veterinarios')
@login_required
def home_veterinarios():
    if current_user.__class__.__name__ == 'User':
        flash('Acceso denegado. Esta página es para veterinarios.', 'warning')
        return redirect(url_for('home'))
    return render_template('home_veterinarios.html')

@app.route('/crear_horarios_veterinario', methods=['GET', 'POST'])
@login_required
def crear_horarios_veterinario():
    # 1. Validación de tipo de usuario al inicio de la función
    if not isinstance(current_user, Veterinarios):
        flash('Acceso denegado: Solo los veterinarios pueden crear horarios.', 'warning') #
        return redirect(url_for('home')) #

    # Aseguramos que veterinario_id se obtenga correctamente
    # current_user.get_mongo_id() debería devolver un ObjectId
    # y lo necesitamos como string para el constructor de HorarioVeterinario si tu __init__ lo espera así,
    # o como ObjectId si tu __init__ lo convierte internamente.
    # Por la estructura de tu entidad HorarioVeterinario (que espera _id y veterinario_id directamente),
    # es mejor pasar el ObjectId si el constructor lo maneja, o el string si lo convierte.
    # Dado que HorarioVeterinario.__init__ maneja tanto ObjectId como string para _id y veterinario_id,
    # pasar el ObjectId directamente es lo más robusto.
    veterinario_id_obj = current_user.get_mongo_id() # Esto debe devolver un ObjectId
    print(f"DEBUG: Extracted veterinario_id as ObjectId: {veterinario_id_obj} (Type: {type(veterinario_id_obj)})") #

    if request.method == 'POST':
        dia_semana = request.form['dia_semana']
        mes = request.form['mes']
        anio = request.form['anio']
        hora_inicio = request.form['hora_inicio']
        hora_fin = request.form['hora_fin']
        # Si el checkbox no está marcado, request.form.get('esta_disponible') será None.
        # Por eso, '1' if ... else 0 es correcto.
        esta_disponible = 1 if request.form.get('esta_disponible') == '1' else 0 

        try:
            mes = int(mes)
            anio = int(anio)
            if not (1 <= mes <= 12):
                raise ValueError("Mes inválido. Debe ser un número entre 1 y 12.") #
            if not (datetime.now().year <= anio <= datetime.now().year + 10):
                raise ValueError(f"Año inválido. Debe ser entre {datetime.now().year} y {datetime.now().year + 10}.") #
        except ValueError as ve:
            flash(f'Error de validación: {str(ve)}', 'danger') #
            # Asegúrate de pasar 'datetime' y 'request_form' al re-renderizar
            return render_template('crear_horarios_veterinario.html', request_form=request.form, datetime=datetime) #

        if not all([dia_semana, mes, anio, hora_inicio, hora_fin]):
            flash('Por favor, completa todos los campos requeridos.', 'danger') #
            # Asegúrate de pasar 'datetime' y 'request_form' al re-renderizar
            return render_template('crear_horarios_veterinario.html', request_form=request.form, datetime=datetime) #

        if hora_inicio >= hora_fin:
            flash('La hora de inicio debe ser anterior a la hora de fin.', 'danger') #
            # Asegúrate de pasar 'datetime' y 'request_form' al re-renderizar
            return render_template('crear_horarios_veterinario.html', request_form=request.form, datetime=datetime) #

        try:
            # Crear instancia del horario
            # Pasa el ObjectId directamente si tu entidad HorarioVeterinario lo maneja
            nuevo_horario = HorarioVeterinario(
                _id=None,
                veterinario_id=veterinario_id_obj, # Pasa el ObjectId
                dia_semana=dia_semana,
                mes=mes,
                anio=anio,
                hora_inicio=hora_inicio,
                hora_fin=hora_fin,
                esta_disponible=esta_disponible
            )

            ModelHorarioVeterinario.crear_horario(db, nuevo_horario) #
            flash('Horario creado exitosamente.', 'success') #
            # Redirige para evitar el reenvío del formulario
            return redirect(url_for('consultar_horarios_veterinario')) # Redirige a la página de consulta

        except DuplicateKeyError:
            flash('Ya existe un horario para este veterinario en esta fecha y hora de inicio.', 'warning') #
            # Asegúrate de pasar 'datetime' y 'request_form' al re-renderizar
            return render_template('crear_horarios_veterinario.html', request_form=request.form, datetime=datetime) #
        except Exception as e:
            flash(f'Ocurrió un error al guardar el horario: {str(e)}', 'danger') #
            # Asegúrate de pasar 'datetime' y 'request_form' al re-renderizar
            return render_template('crear_horarios_veterinario.html', request_form=request.form, datetime=datetime) #

    # Para solicitudes GET, simplemente renderiza el formulario
    # Asegúrate de pasar 'datetime' al template para que pueda usar datetime.now().year
    return render_template('crear_horarios_veterinario.html', datetime=datetime, request_form={})


@app.route('/consultar_horarios_veterinario')
@login_required
def consultar_horarios_veterinario():
    # 1. Validación de tipo de usuario
    if not isinstance(current_user, Veterinarios):
        flash('Acceso denegado: Esta página es para veterinarios.', 'warning') #
        return redirect(url_for('home')) #

    veterinario_id_obj = None 
    try:
        # current_user.get_mongo_id() devuelve un ObjectId
        veterinario_id_obj = current_user.get_mongo_id()
        print(f"DEBUG: En consultar_horarios_veterinario, veterinario_id extraído (ObjectId): {veterinario_id_obj}") #

    except AttributeError as e:
        print(f"ERROR: Falló al identificar el ID del veterinario logueado para consultar horarios. Detalle: {e}") #
        flash('Error: No se pudo identificar el ID del veterinario logueado. Por favor, asegúrese de que su cuenta de veterinario esté configurada correctamente.', 'danger') #
        return redirect(url_for('home_veterinarios')) #

    horarios = []
    try:
        # Pasa el ObjectId al modelo de consulta
        horarios = ModelHorarioVeterinario.obtener_horarios_por_veterinario(db, veterinario_id_obj) #
        
        # Ordenar los horarios para una mejor visualización (por año, mes, día de la semana, hora de inicio)
        dias_orden = {"Lunes": 1, "Martes": 2, "Miércoles": 3, "Jueves": 4, "Viernes": 5, "Sábado": 6, "Domingo": 7} #
        if horarios:
            # Asegúrate de que hora_inicio y hora_fin sean strings comparables o conviértelos a objetos time si es necesario
            horarios.sort(key=lambda h: (h.anio, h.mes, dias_orden.get(h.dia_semana, 99), h.hora_inicio)) #

        if not horarios:
            flash('No tienes horarios registrados todavía.', 'info') #

    except Exception as e:
        flash(f'Ocurrió un error al cargar los horarios: {str(e)}', 'danger') #
    
    # No necesitas las propiedades _display aquí si ya las estás manejando en la entidad.
    # Si tu entidad HorarioVeterinario tiene propiedades @property para hora_inicio_display
    # y hora_fin_display, el template las usará automáticamente.
    return render_template('consultar_horarios_veterinario.html', horarios=horarios) #

@app.route('/editar_horario_veterinario/<horario_id>', methods=['GET', 'POST'])
@login_required
def editar_horario_veterinario(horario_id):
    # Validación de que solo los veterinarios pueden acceder
    if not isinstance(current_user, Veterinarios):
        flash("Acceso denegado. Esta área es solo para veterinarios.", "danger")
        return redirect(url_for('home'))

    # Manejo de ObjectId: Convertir el ID de la URL a ObjectId
    try:
        horario_obj_id = ObjectId(horario_id)
    except Exception:
        flash("ID de horario inválido.", "danger")
        return redirect(url_for('consultar_horarios_veterinario'))

    # Obtener el horario de la base de datos
    horario = ModelHorarioVeterinario.obtener_horario_por_id(db, horario_obj_id)
    
    # Validación: Verificar si el horario existe y si pertenece al veterinario logueado
    if not horario or horario.veterinario_id != current_user.get_mongo_id():
        flash("Horario no encontrado o no autorizado.", "danger")
        return redirect(url_for('consultar_horarios_veterinario'))

    if request.method == 'POST':
        # Extracción de datos del formulario (POST request para actualizar)
        dia_semana = request.form['dia_semana']
        mes = request.form['mes']
        anio = request.form['anio']
        hora_inicio = request.form['hora_inicio']
        hora_fin = request.form['hora_fin']
        esta_disponible = 1 if request.form.get('esta_disponible') == '1' else 0

        # Validaciones de entrada (similares a 'crear_horarios_veterinario')
        try:
            mes = int(mes)
            anio = int(anio)
            if not (1 <= mes <= 12):
                raise ValueError("Mes inválido. Debe ser un número entre 1 y 12.")
            # Ensure proper year range check for the current year
            if not (datetime.now().year <= anio <= datetime.now().year + 10):
                raise ValueError(f"Año inválido. Debe ser entre {datetime.now().year} y {datetime.now().year + 10}.")
        except ValueError as ve:
            flash(f'Error de validación: {str(ve)}', 'danger')
            # Pasa el horario existente (para mantener el ID) y request.form para pre-rellenar los campos en caso de error
            # También se añade is_editing=True para que puedas adaptar el título del formulario en el template si lo deseas.
            return render_template('crear_horarios_veterinario.html', horario=horario, request_form=request.form, datetime=datetime, is_editing=True)

        if hora_inicio >= hora_fin:
            flash("La hora de inicio debe ser anterior a la hora de fin.", "danger")
            return render_template('crear_horarios_veterinario.html', horario=horario, request_form=request.form, datetime=datetime, is_editing=True)

        try:
            # Actualiza la instancia existente del horario con los nuevos datos
            horario.dia_semana = dia_semana
            horario.mes = mes
            horario.anio = anio
            horario.hora_inicio = hora_inicio
            horario.hora_fin = hora_fin
            horario.esta_disponible = esta_disponible

            # Llama al método del modelo para actualizar en la base de datos
            ModelHorarioVeterinario.actualizar_horario(db, horario) 
            flash("Horario actualizado exitosamente!", "success")
            return redirect(url_for('consultar_horarios_veterinario'))
        except DuplicateKeyError:
            flash('Ya existe un horario para este veterinario en esta fecha y hora de inicio.', 'warning')
            return render_template('crear_horarios_veterinario.html', horario=horario, request_form=request.form, datetime=datetime, is_editing=True)
        except Exception as e:
            flash(f"Error al actualizar el horario: {e}", "danger")
            return render_template('crear_horarios_veterinario.html', horario=horario, request_form=request.form, datetime=datetime, is_editing=True)
    
    # GET request: Cargar el formulario con los datos del horario existente
    # Este es el punto donde horario.to_dict() se llama.
    # Con la adición de `to_dict()` en HorarioVeterinario.py, esto ya no debería dar error.
    return render_template('crear_horarios_veterinario.html', horario=horario, request_form=horario.to_dict(), datetime=datetime, is_editing=True)


# 2. Ruta para ELIMINAR horarios
# Se ha añadido la ruta con el parámetro <horario_id> y se limita a POST (por seguridad)
@app.route('/eliminar_horario_veterinario/<horario_id>', methods=['POST'])
@login_required
def eliminar_horario_veterinario(horario_id):
    # Validación de que solo los veterinarios pueden acceder
    if not isinstance(current_user, Veterinarios):
        flash("Acceso denegado. Esta área es solo para veterinarios.", "danger")
        return redirect(url_for('home'))

    # Manejo de ObjectId: Convertir el ID de la URL a ObjectId
    # Se asegura que los ObjectId se manejen correctamente al buscar y pasar IDs a los modelos.
    try:
        horario_obj_id = ObjectId(horario_id)
    except Exception:
        flash("ID de horario inválido.", "danger")
        return redirect(url_for('consultar_horarios_veterinario'))

    # Obtener el horario para verificar la propiedad antes de eliminar
    horario = ModelHorarioVeterinario.obtener_horario_por_id(db, horario_obj_id)

    # Validación: Verificar si el horario existe y si pertenece al veterinario logueado
    if not horario or horario.veterinario_id != current_user.get_mongo_id():
        flash("Horario no encontrado o no autorizado para eliminar.", "danger")
        return redirect(url_for('consultar_horarios_veterinario'))

    try:
        # Llama al método del modelo para eliminar de la base de datos
        ModelHorarioVeterinario.eliminar_horario(db, horario_obj_id)
        flash("Horario eliminado exitosamente!", "success")
    except Exception as e:
        flash(f"Error al eliminar el horario: {e}", "danger")

    # Siempre redirige de vuelta a la página de consulta después de la operación
    return redirect(url_for('consultar_horarios_veterinario'))
    
@app.route('/registrar_mascota', methods=['GET', 'POST'])
@login_required
def registrar_mascota():
    if request.method == 'POST':
        try:
            # current_user.id ahora devuelve "U_ObjectIdString" o "V_ObjectIdString"
            # Extraemos solo el ObjectIdString. Este es el ID del usuario en MongoDB.
            # user_id del form es el ID del usuario logueado
            # user_id = current_user.id # Esto sería 'U_668636c72b53f6701e924705'
            # Necesitamos extraer el 'ObjectIdString'
            user_id_from_session = current_user.id.split('_')[1] 
            
            nombre = request.form['nombre']
            especie = request.form['especie']
            raza = request.form.get('raza', None)
            sexo = request.form.get('sexo', 'desconocido')
            edad = request.form.get('edad', type=int) # Usar type=int es muy útil aquí
            color = request.form.get('color', None)
            
            fecha_nacimiento_str = request.form.get('fecha_nacimiento', None)
            # No necesitas convertir a .date() aquí, Mascota.__init__ lo hará a datetime.datetime
            # Si fecha_nacimiento_str es un string vacío, pasamos None
            fecha_nacimiento = fecha_nacimiento_str if fecha_nacimiento_str else None 
            # ¡Importante! No hagas datetime.strptime aquí, pásale el string o None a Mascota
            # Mascota.__init__ se encarga de la conversión robusta.

            notas = request.form.get('notas', None)

            new_mascota = Mascota(
                _id=None, # Para que MongoDB genere el _id
                user_id=user_id_from_session, # Pasa el string del ObjectId del usuario
                nombre=nombre,
                especie=especie,
                raza=raza,
                sexo=sexo,
                edad=edad,
                color=color,
                fecha_nacimiento=fecha_nacimiento, # Pasamos el string o None
                notas=notas
            )

            # Si tu db object se pasa globalmente o se inicializa de otra forma, úsalo aquí.
            # Asumo que 'db' es tu cliente de MongoDB (mongo.db) o similar
            if ModelMascota.register_mascota(db, new_mascota):
                flash(f'¡Mascota "{nombre}" registrada con éxito!', 'success')
                return redirect(url_for('mis_mascotas'))
            else:
                flash('Error al registrar la mascota. Por favor, verifica los datos.', 'danger')
                return render_template('registrar_mascota.html', request_form=request.form)

        except ValueError as ve:
            flash(f'Datos de edad o fecha de nacimiento inválidos: {ve}', 'danger')
            return render_template('registrar_mascota.html', request_form=request.form)
        except Exception as e:
            flash(f'Ocurrió un error inesperado al registrar la mascota: {e}', 'danger')
            print(f"Error al registrar mascota: {e}") # Para depuración
            return render_template('registrar_mascota.html', request_form=request.form)
    else:
        return render_template('registrar_mascota.html')

@app.route('/mis_mascotas')
@login_required
def mis_mascotas():
    # current_user.id es 'U_ObjectIdString', necesitamos solo el ObjectIdString
    user_id = current_user.id.split('_')[1]
    
    print(f"DEBUG: user_id actual (para mis_mascotas): {user_id}")
    mascotas = ModelMascota.get_mascotas_by_user(db, user_id)
    print(f"DEBUG: Mascotas obtenidas de la BD para user_id {user_id}: {mascotas}")
    return render_template('mis_mascotas.html', mascotas=mascotas)
    
@app.route('/home') 
def home():
    return render_template('home.html')

@app.route('/protected')
@login_required
def protected():
    return "<h1> Esta es una vista protegida, solo para usuarios auntenticados </h1>"

def status_401(error):
    return redirect(url_for('login'))

def status_404(error):
    return "<h1> Pagina no encontrada </h1>", 404

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        nombre = request.form['nombre']
        apellido_paterno = request.form['apellido_paterno']
        apellido_materno = request.form.get('apellido_materno', None)
        telefono = request.form.get('telefono', None)
        email = request.form.get('email', None)

        hashed_password = User.generate_password(password)

        # _id=None para que MongoDB genere uno nuevo
        new_user = User(_id=None, username=username, password=hashed_password, 
                        nombre=nombre, apellido_paterno=apellido_paterno, 
                        apellido_materno=apellido_materno, telefono=telefono, email=email)

        if ModelUser.register(db, new_user):
            flash('Usuario registrado con éxito. ¡Ya puedes iniciar sesión!', 'success')
            return redirect(url_for('login'))
        else:
            flash('Error al registrar usuario. Posiblemente el nombre de usuario ya existe.', 'danger')
            return render_template('auth/register.html',
                                   username=username,
                                   nombre=nombre,
                                   apellido_paterno=apellido_paterno,
                                   apellido_materno=apellido_materno,
                                   telefono=telefono,
                                   email=email)
    else:
        return render_template('auth/register.html')
    
@app.route('/agendar', methods=['GET', 'POST'])
@login_required
def agendar_cita():
    if request.method == 'POST':
        try:
            # current_user.id es 'U_ObjectIdString', necesitamos solo el ObjectIdString
            user_id = current_user.id.split('_')[1]
            
            nombre_mascota = request.form['nombre_mascota']
            tipo_mascota = request.form['tipo_mascota']
            raza = request.form.get('raza', None)
            edad_mascota = request.form.get('edad_mascota', type=int)
            telefono = request.form.get('telefono', None)
            email = request.form.get('email', None)
            fecha_cita_str = request.form['fecha_cita']
            servicio = request.form['servicio']
            notas = request.form.get('notas', None)

            # Convertir la cadena de fecha a un objeto datetime
            fecha_cita = datetime.strptime(fecha_cita_str, '%Y-%m-%dT%H:%M') 

            # _id=None para que MongoDB genere uno nuevo
            new_cita = Cita(
                _id=None,
                user_id=user_id,
                nombre_mascota=nombre_mascota,
                tipo_mascota=tipo_mascota,
                raza=raza,
                edad_mascota=edad_mascota,
                telefono=telefono,
                email=email,
                fecha_cita=fecha_cita,
                servicio=servicio,
                estado='pendiente',
                notas=notas
            )

            if ModelCita.create_cita(db, new_cita):
                flash('Cita agendada con éxito!', 'success')
                return redirect(url_for('historial_citas'))
            else:
                flash('Error al agendar la cita. Inténtalo de nuevo.', 'danger')
                return render_template('agendar_cita.html', request_form=request.form)

        except ValueError as ve:
            flash(f'Formato de fecha u edad incorrecto: {ve}', 'danger')
            return render_template('agendar_cita.html', request_form=request.form)
        except Exception as e:
            flash(f'Ocurrió un error inesperado: {e}', 'danger')
            return render_template('agendar_cita.html', request_form=request.form)

    else:
        return render_template('agendar_cita.html')
    
@app.route('/historial_citas')
@login_required 
def historial_citas():
    # current_user.id es 'U_ObjectIdString', necesitamos solo el ObjectIdString
    user_id = current_user.id.split('_')[1]
    citas = ModelCita.get_citas_by_user(db, user_id)
    now = datetime.now()
    return render_template('historial_citas.html', citas=citas, now=now)

@app.route('/modificar_cita/<cita_id>', methods=['GET', 'POST']) # El ID de MongoDB es string, no int
@login_required
def modificar_cita(cita_id):
    # ModelCita.get_cita_by_id ahora espera un string de _id
    cita = ModelCita.get_cita_by_id(db, cita_id) 

    # Verifica si la cita existe y si pertenece al usuario actual por seguridad
    # Asegúrate de que cita.user_id es el _id de usuario como string
    if not cita or str(cita.user_id) != current_user.id.split('_')[1]:
        flash("Cita no encontrada o no tienes permisos para modificarla.", "danger")
        return redirect(url_for('historial_citas'))

    if request.method == 'POST':
        cita.nombre_mascota = request.form['nombre_mascota']
        cita.tipo_mascota = request.form['tipo_mascota']
        cita.raza = request.form.get('raza', None)
        cita.edad_mascota = request.form.get('edad_mascota', type=int)
        cita.telefono = request.form.get('telefono', None)
        cita.email = request.form.get('email', None)
        fecha_cita_str = request.form['fecha_cita']
        cita.servicio = request.form['servicio']
        cita.notas = request.form.get('notas', None)
        cita.estado = request.form.get('estado', 'pendiente') # Puedes añadir un campo para estado si es necesario

        if not all([cita.nombre_mascota, cita.tipo_mascota, fecha_cita_str, cita.servicio]):
            flash("Por favor, completa todos los campos obligatorios.", "danger")
            return render_template('modificar_cita.html', cita=cita, request_form=request.form)
        try:
            cita.fecha_cita = datetime.strptime(fecha_cita_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash("Formato de fecha y hora inválido.", "danger")
            return render_template('modificar_cita.html', cita=cita, request_form=request.form)

        if ModelCita.update_cita(db, cita):
            flash("Cita actualizada exitosamente.", "success")
            return redirect(url_for('historial_citas'))
        else:
            flash("Error al actualizar la cita. Por favor, inténtalo de nuevo.", "danger")
            return render_template('modificar_cita.html', cita=cita, request_form=request.form)

    cita.fecha_cita_str = cita.fecha_cita.strftime('%Y-%m-%dT%H:%M')
    return render_template('modificar_cita.html', cita=cita)

@app.route('/cancelar_cita/<cita_id>', methods=['POST']) # El ID de MongoDB es string, no int
@login_required
def cancelar_cita(cita_id):
    cita = ModelCita.get_cita_by_id(db, cita_id)
    # Verifica que la cita pertenezca al usuario actual
    if not cita or str(cita.user_id) != current_user.id.split('_')[1]:
        flash("Cita no encontrada o no tienes permisos para cancelarla.", "danger")
    else:
        if cita.estado == 'cancelada' or cita.estado == 'completada':
            flash("La cita ya está en un estado que no permite la cancelación.", "info")
        # Pasa el ID de la cita (string) y el user_id (string)
        elif ModelCita.cancel_cita(db, cita_id, current_user.id.split('_')[1]):
            flash("Cita cancelada exitosamente.", "success")
        else:
            flash("Error al cancelar la cita.", "danger")
    return redirect(url_for('historial_citas'))

@app.route('/restaurar_cita/<cita_id>', methods=['POST']) # El ID de MongoDB es string, no int
@login_required
def restaurar_cita(cita_id):
    cita = ModelCita.get_cita_by_id(db, cita_id)
    # Verifica que la cita pertenezca al usuario actual
    if not cita or str(cita.user_id) != current_user.id.split('_')[1]:
        flash("Cita no encontrada o no tienes permisos para restaurarla.", "danger")
    else:
        if cita.estado == 'cancelada':
            # Pasa el ID de la cita (string) y el user_id (string)
            if ModelCita.restore_cita(db, cita_id, current_user.id.split('_')[1]):
                flash("Cita restaurada exitosamente a 'pendiente'.", "success")
            else:
                flash("Error al restaurar la cita.", "danger")
        else:
            flash("La cita no está en estado 'cancelada' para ser restaurada.", "info")
    return redirect(url_for('historial_citas'))

@app.route('/dashboard')
@login_required
def dashboard():
    # current_user.id es 'U_ObjectIdString', necesitamos solo el ObjectIdString
    # Este dashboard es solo para usuarios regulares, no para veterinarios
    if current_user.__class__.__name__ == 'Veterinarios':
        flash('Acceso denegado. Este dashboard es solo para usuarios.', 'warning')
        return redirect(url_for('home_veterinarios'))
        
    user_id = current_user.id.split('_')[1]

    columns, all_citas_data = ModelCita.get_dashboard_data(db, user_id) 

    if not all_citas_data:
        df = pd.DataFrame(columns=columns)
    else:
        df = pd.DataFrame(all_citas_data, columns=columns)

    if 'fecha_cita' in df.columns:
        # Asegurarse de que 'fecha_cita' sea un tipo de dato datetime antes de operar
        # Si MongoDB ya lo almacena como ISODate, pd.to_datetime debería manejarlo.
        df['fecha_cita'] = pd.to_datetime(df['fecha_cita'], errors='coerce')
        df.dropna(subset=['fecha_cita'], inplace=True)
    else:
        df['fecha_cita'] = pd.Series(dtype='datetime64[ns]')

    total_citas = len(df)
    
    df_activas = df[df['estado'] != 'cancelada']

    citas_pendientes = len(df_activas[(df_activas['estado'] == 'pendiente') & (df_activas['fecha_cita'] > datetime.now())])
    citas_completadas = len(df_activas[df_activas['estado'] == 'completada'])
    citas_canceladas = len(df[df['estado'] == 'cancelada'])

    hoy = datetime.now()
    citas_hoy = len(df_activas[(df_activas['fecha_cita'].dt.date == hoy.date())])
    
    proximos_7_dias = hoy + timedelta(days=7)
    citas_proximos_7_dias = len(df_activas[(df_activas['fecha_cita'] > hoy) & (df_activas['fecha_cita'] <= proximos_7_dias)])

    proximas_citas_raw = df_activas[df_activas['fecha_cita'] > datetime.now()].sort_values(by='fecha_cita').head(5).to_dict('records')
    
    proximas_citas_obj = []
    for row_dict in proximas_citas_raw:
        try:
            # Asegurarse de que el '_id' se pase correctamente al constructor de Cita
            # Si el documento de MongoDB tiene '_id', row_dict.get('_id') lo obtendrá
            # y el constructor de Cita lo convertirá a string.
            cita_id_from_db = row_dict.get('_id') 
            proximas_citas_obj.append(Cita(
                _id=cita_id_from_db, # Pasa el _id original de MongoDB
                user_id=user_id,
                nombre_mascota=row_dict.get('nombre_mascota'),
                tipo_mascota=row_dict.get('tipo_mascota'),
                raza=row_dict.get('raza'),
                edad_mascota=row_dict.get('edad_mascota'),
                telefono=row_dict.get('telefono'), # Asegúrate de que estos campos existan en el dict de MongoDB
                email=row_dict.get('email'),
                fecha_cita=row_dict.get('fecha_cita'),
                servicio=row_dict.get('servicio'),
                notas=row_dict.get('notas'),
                estado=row_dict.get('estado')
            ))
        except Exception as e:
            print(f"Error creating Cita object for dashboard table: {e} - Data: {row_dict}")
            continue

    # Data for charts (using df_activas for pet types and services)
    tipos_mascota_counts = df_activas['tipo_mascota'].value_counts().sort_index()
    tipos_mascota_labels = tipos_mascota_counts.index.tolist()
    tipos_mascota_data = tipos_mascota_counts.values.tolist()

    servicios_counts = df_activas['servicio'].value_counts().sort_values(ascending=False)
    servicios_labels = [s.replace('_', ' ').capitalize() for s in servicios_counts.index.tolist()]
    servicios_data = servicios_counts.values.tolist()

    # Citas por Estado chart data (using the full df)
    estado_counts = df['estado'].value_counts()
    estado_labels = estado_counts.index.tolist()
    estado_data = estado_counts.values.tolist()

    # Average pet age by type
    edad_promedio_por_tipo = df_activas.groupby('tipo_mascota')['edad_mascota'].mean().round(1).fillna(0).to_dict()

    # --- START NEW LINEAR CHART DATA GENERATION (y = mx + b) ---
    linear_chart_prep_df = df_activas.groupby('tipo_mascota').agg(
        num_unique_services=('servicio', 'nunique'), # This will be 'm'
        total_appointments=('fecha_cita', 'count')   # This will be 'b' (using count of appointments)
    ).reset_index()

    lineal_chart_labels = linear_chart_prep_df['tipo_mascota'].tolist()
    lineal_chart_data = []

    for index, row in linear_chart_prep_df.iterrows():
        m_val = row['num_unique_services']
        b_val = row['total_appointments']
        x_val = index + 1   # Assign a 1-based numerical index for 'x'
        y_calculated = (m_val * x_val) + b_val
        lineal_chart_data.append(y_calculated)
    # --- END NEW LINEAR CHART DATA GENERATION ---

    return render_template('dashboard.html',
                            total_citas=total_citas,
                            citas_pendientes=citas_pendientes,
                            citas_completadas=citas_completadas,
                            citas_canceladas=citas_canceladas,
                            citas_hoy=citas_hoy,
                            citas_proximos_7_dias=citas_proximos_7_dias,
                            proximas_citas=proximas_citas_obj,
                            tipos_mascota_labels=json.dumps(tipos_mascota_labels),
                            tipos_mascota_data=json.dumps(tipos_mascota_data),
                            servicios_labels=json.dumps(servicios_labels),
                            servicios_data=json.dumps(servicios_data),
                            estado_labels=json.dumps(estado_labels),
                            estado_data=json.dumps(estado_data),
                            edad_promedio_por_tipo=edad_promedio_por_tipo,
                            lineal_chart_labels=json.dumps(lineal_chart_labels),
                            lineal_chart_data=json.dumps(lineal_chart_data)
                            )


if __name__=='__main__':
    # Configura la llave secreta para Flask-Login y flashes
    app.secret_key = config['development'].SECRET_KEY
    # Cargar otras configuraciones (como DEBUG)
    app.config.from_object(config['development'])
    app.register_error_handler(401,status_401)
    app.register_error_handler(404,status_404)
    # CAMBIO AQUÍ: set use_reloader=False
    app.run(debug=True, port=5001)