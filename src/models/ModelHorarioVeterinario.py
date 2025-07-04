# src/models/ModelHorarioVeterinario.py

from src.models.entities.HorarioVeterinario import HorarioVeterinario
from bson.objectid import ObjectId
from pymongo.errors import DuplicateKeyError

class ModelHorarioVeterinario:

    @classmethod
    def crear_horario(cls, db, horario_veterinario):
        """
        Inserta un nuevo horario para un veterinario en la base de datos MongoDB.
        """
        try:
            # horario_veterinario.to_mongo_dict() ya maneja que _id y veterinario_id sean ObjectIds
            horario_data = horario_veterinario.to_mongo_dict()
            
            # Aseguramos que el '_id' no se incluya en la inserción si quieres que MongoDB lo genere
            # Esto es redundante si _id en la entidad es None, pero buena práctica para insert_one
            horario_data.pop('_id', None) 
            
            # El veterinario_id ya debería ser un ObjectId aquí gracias a la entidad
            if not isinstance(horario_data.get('veterinario_id'), ObjectId):
                print(f"DEBUG (ModelHorarioVeterinario.crear_horario): ID de veterinario no es un ObjectId válido al intentar guardar: {horario_data.get('veterinario_id')}")
                return False 
            
            result = db.horarios_veterinarios.insert_one(horario_data)
            
            if result.inserted_id:
                horario_veterinario._id = result.inserted_id # Asigna el ObjectId real de MongoDB
                print(f"DEBUG (ModelHorarioVeterinario.crear_horario): Horario creado con _id: {horario_veterinario._id}")
                return True
            print(f"DEBUG (ModelHorarioVeterinario.crear_horario): La inserción del horario no generó un inserted_id.")
            return False
        except DuplicateKeyError as dex: # Captura específica para duplicados
            print(f"ERROR (ModelHorarioVeterinario.crear_horario): Horario duplicado detectado: {dex}")
            raise dex # Re-lanza para que app.py la capture y muestre un flash message específico
        except Exception as ex:
            print(f"ERROR (ModelHorarioVeterinario.crear_horario): Error al crear horario en MongoDB: {ex}")
            return False # Retorna False en caso de error

    @classmethod
    def obtener_horarios_por_veterinario(cls, db, veterinario_id): # Changed param name to reflect it should be ObjectId
        """
        Obtiene todos los horarios registrados para un veterinario específico desde MongoDB.
        Recibe veterinario_id como ObjectId.
        """
        try:
            horarios = []
            
            # Asumiendo que veterinario_id ya es un ObjectId o se valida en app.py
            # No es necesario convertirlo aquí si app.py ya lo hace.
            if not isinstance(veterinario_id, ObjectId):
                print(f"DEBUG (ModelHorarioVeterinario.obtener_horarios_por_veterinario): ID de veterinario no es un ObjectId válido: {veterinario_id}")
                return [] 

            rows = db.horarios_veterinarios.find(
                {"veterinario_id": veterinario_id}
            ).sort([
                ("anio", 1),       # Primero por año ascendente
                ("mes", 1),        # Luego por mes ascendente
                ("hora_inicio", 1) # Finalmente por hora de inicio ascendente (asumiendo formato 'HH:MM')
            ])
            
            for row in rows:
                # Usa from_mongo_dict para crear la instancia de entidad
                horario = HorarioVeterinario.from_mongo_dict(row)
                horarios.append(horario)
            
            # Re-ordenar en Python para asegurar el orden correcto por día de la semana
            dias_orden = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
            horarios.sort(key=lambda h: (
                h.anio, 
                h.mes, 
                dias_orden.index(h.dia_semana) if h.dia_semana in dias_orden else len(dias_orden), # Orden personalizado por día
                h.hora_inicio
            ))

            return horarios
        except Exception as ex:
            print(f"ERROR (ModelHorarioVeterinario.obtener_horarios_por_veterinario): Error al obtener horarios de veterinario: {ex}")
            return [] # Retorna una lista vacía en caso de error
            
    @classmethod
    def obtener_horario_por_id(cls, db, horario_id):
        """
        Obtiene un horario específico por su ID.
        Recibe horario_id como ObjectId.
        """
        try:
            # Asumiendo que horario_id ya es un ObjectId o se valida en app.py
            if not isinstance(horario_id, ObjectId):
                print(f"DEBUG (ModelHorarioVeterinario.obtener_horario_por_id): ID de horario no válido (no ObjectId): {horario_id}")
                return None

            row = db.horarios_veterinarios.find_one({"_id": horario_id}) # Use the ObjectId directly
            if row:
                # Usa from_mongo_dict para crear la instancia de entidad
                return HorarioVeterinario.from_mongo_dict(row)
            else:
                print(f"DEBUG (ModelHorarioVeterinario.obtener_horario_por_id): Horario con ID {horario_id} no encontrado.")
                return None
        except Exception as ex:
            print(f"ERROR (ModelHorarioVeterinario.obtener_horario_por_id): Error al obtener horario por ID: {ex}")
            return None # Retorna None en caso de error

    @classmethod
    def actualizar_horario(cls, db, horario_obj): # <--- Renamed parameter to match app.py's call
        """
        Actualiza un horario existente en la base de datos usando el objeto HorarioVeterinario.
        """
        try:
            if not isinstance(horario_obj, HorarioVeterinario):
                print(f"ERROR (ModelHorarioVeterinario.actualizar_horario): Se esperaba un objeto HorarioVeterinario, se recibió {type(horario_obj)}")
                return False
            
            if not isinstance(horario_obj._id, ObjectId):
                print(f"ERROR (ModelHorarioVeterinario.actualizar_horario): El _id del horario no es un ObjectId válido: {horario_obj._id}")
                return False

            # Usa to_mongo_dict para obtener el diccionario de datos para la actualización
            # Esto asegurará que los IDs sigan siendo ObjectIds en la DB
            update_data = horario_obj.to_mongo_dict()
            
            # Remove _id from the $set data, as we use it in the filter, not to change it.
            # to_mongo_dict() already handles not including _id if it's None.
            # But if it exists, it should not be part of the $set operator's value.
            if '_id' in update_data:
                del update_data['_id']

            # Define el filtro usando el _id del objeto
            filter_query = {"_id": horario_obj._id}

            result = db.horarios_veterinarios.update_one(
                filter_query,
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                print(f"DEBUG (ModelHorarioVeterinario.actualizar_horario): Horario {horario_obj._id} actualizado.")
                return True
            else:
                print(f"DEBUG (ModelHorarioVeterinario.actualizar_horario): No se encontró el horario {horario_obj._id} o no se modificaron datos.")
                return False
        except DuplicateKeyError as dex:
            # Relanzar DuplicateKeyError para que app.py pueda manejarlo específicamente
            print(f"ERROR (ModelHorarioVeterinario.actualizar_horario): Horario duplicado detectado durante la actualización: {dex}")
            raise dex
        except Exception as ex:
            print(f"ERROR (ModelHorarioVeterinario.actualizar_horario): Error al actualizar horario: {ex}")
            return False # Retorna False en caso de error

    @classmethod
    def actualizar_disponibilidad_horario(cls, db, horario_id, esta_disponible):
        """
        Actualiza el estado de disponibilidad de un horario.
        (Este método parece estar bien para su propósito específico)
        """
        try:
            if not ObjectId.is_valid(horario_id):
                print(f"DEBUG (ModelHorarioVeterinario.actualizar_disponibilidad_horario): ID de horario no válido: {horario_id}")
                return False

            obj_id = ObjectId(horario_id)
            result = db.horarios_veterinarios.update_one(
                {"_id": obj_id},
                {"$set": {"esta_disponible": esta_disponible}}
            )
            if result.modified_count > 0:
                print(f"DEBUG (ModelHorarioVeterinario.actualizar_disponibilidad_horario): Disponibilidad del horario {horario_id} actualizada.")
                return True
            else:
                print(f"DEBUG (ModelHorarioVeterinario.actualizar_disponibilidad_horario): No se encontró el horario {horario_id} o la disponibilidad no cambió.")
                return False
        except Exception as ex:
            print(f"ERROR (ModelHorarioVeterinario.actualizar_disponibilidad_horario): Error al actualizar disponibilidad del horario: {ex}")
            return False # Retorna False en caso de error

    @classmethod
    def eliminar_horario(cls, db, horario_id):
        """
        Elimina un horario de la base de datos.
        Recibe horario_id como ObjectId (asumido desde app.py)
        """
        try:
            # Asumiendo que horario_id ya es un ObjectId o se valida en app.py
            if not isinstance(horario_id, ObjectId):
                print(f"DEBUG (ModelHorarioVeterinario.eliminar_horario): ID de horario no válido (no ObjectId): {horario_id}")
                return False

            result = db.horarios_veterinarios.delete_one({"_id": horario_id})
            if result.deleted_count > 0:
                print(f"DEBUG (ModelHorarioVeterinario.eliminar_horario): Horario {horario_id} eliminado exitosamente.")
                return True
            else:
                print(f"DEBUG (ModelHorarioVeterinario.eliminar_horario): No se encontró el horario {horario_id} para eliminar.")
                return False
        except Exception as ex:
            print(f"ERROR (ModelHorarioVeterinario.eliminar_horario): Error al eliminar horario: {ex}")
            return False # Retorna False en caso de error