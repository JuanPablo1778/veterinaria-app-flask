# src/models/ModelCita.py

from .entities.Cita import Cita
from datetime import datetime
from bson.objectid import ObjectId # Necesario para trabajar con _id de MongoDB

class ModelCita:
    # La instancia 'db' que se pasa a los métodos será tu objeto de base de datos de PyMongo
    # Por ejemplo: db = client.veterinaria
    @classmethod
    def create_cita(cls, db, cita):
        """
        Inserta una nueva cita en la base de datos MongoDB.
        """
        try:
            cita_data = cita.to_mongo_dict()
            
            # Asegurar que los IDs de referencia son ObjectId si es necesario
            # Si 'user_id' se almacena como ObjectId en MongoDB
            if cita_data.get('user_id') and ObjectId.is_valid(cita_data['user_id']):
                cita_data['user_id'] = ObjectId(cita_data['user_id'])
            # Si 'veterinario_id' se almacena como ObjectId en MongoDB (asumiendo que las citas se asocian a un veterinario)
            # Agrega esto si tu entidad Cita tiene un campo 'veterinario_id'
            # if cita_data.get('veterinario_id') and ObjectId.is_valid(cita_data['veterinario_id']):
            #     cita_data['veterinario_id'] = ObjectId(cita_data['veterinario_id'])
            
            # El _id se generará automáticamente por MongoDB al insertar, no lo incluimos si ya viene.
            cita_data.pop('_id', None)

            result = db.citas.insert_one(cita_data)
            
            if result.inserted_id:
                cita._id = str(result.inserted_id) # Asigna el ID generado al objeto
                print(f"DEBUG (ModelCita.create_cita): Cita creada con _id: {cita._id}")
                return True
            print(f"DEBUG (ModelCita.create_cita): La inserción de la cita no generó un inserted_id.")
            return False
        except Exception as ex:
            print(f"ERROR (ModelCita.create_cita): Error al guardar la cita en MongoDB: {ex}")
            return False

    @classmethod
    def get_citas_by_user(cls, db, user_id):
        try:
            citas = []
            
            # Convertir user_id a ObjectId si es válido y si así se almacena en la DB
            query_user_id = user_id
            if ObjectId.is_valid(user_id):
                query_user_id = ObjectId(user_id)
            else:
                print(f"DEBUG (ModelCita.get_citas_by_user): ID de usuario no válido para la búsqueda: {user_id}")
                return [] # Retorna una lista vacía si el ID de usuario no es válido

            rows = db.citas.find({"user_id": query_user_id}).sort("fecha_cita", -1) 

            for row in rows:
                citas.append(Cita(
                    _id=row.get('_id'),
                    user_id=row.get('user_id'), # Esto puede ser ObjectId o string, dependiendo de cómo se recuperó
                    nombre_mascota=row.get('nombre_mascota'),
                    tipo_mascota=row.get('tipo_mascota'),
                    raza=row.get('raza'),
                    edad_mascota=row.get('edad_mascota'),
                    telefono=row.get('telefono'),
                    email=row.get('email'),
                    fecha_cita=row.get('fecha_cita'), # Ya debería ser datetime
                    servicio=row.get('servicio'),
                    estado=row.get('estado', 'pendiente'), 
                    notas=row.get('notas', '')
                ))
            return citas
        except Exception as ex:
            print(f"ERROR (ModelCita.get_citas_by_user): Error al obtener las citas del usuario desde MongoDB: {ex}")
            return []

    @classmethod
    def get_cita_by_id(cls, db, cita_id):
        try:
            if not ObjectId.is_valid(cita_id):
                print(f"DEBUG (ModelCita.get_cita_by_id): ID de cita no válido: {cita_id}")
                return None

            obj_id = ObjectId(cita_id)
            row = db.citas.find_one({"_id": obj_id})
            
            if row:
                return Cita(
                    _id=row.get('_id'),
                    user_id=row.get('user_id'),
                    nombre_mascota=row.get('nombre_mascota'),
                    tipo_mascota=row.get('tipo_mascota'),
                    raza=row.get('raza'),
                    edad_mascota=row.get('edad_mascota'),
                    telefono=row.get('telefono'),
                    email=row.get('email'),
                    fecha_cita=row.get('fecha_cita'),
                    servicio=row.get('servicio'),
                    estado=row.get('estado', 'pendiente'),
                    notas=row.get('notas', '')
                )
            else:
                print(f"DEBUG (ModelCita.get_cita_by_id): Cita con ID {cita_id} no encontrada.")
                return None
        except Exception as ex:
            print(f"ERROR (ModelCita.get_cita_by_id): Error al obtener la cita por ID desde MongoDB: {ex}")
            return None

    @classmethod
    def update_cita(cls, db, cita):
        try:
            if not ObjectId.is_valid(cita._id):
                print(f"DEBUG (ModelCita.update_cita): ID de cita no válido en el objeto cita: {cita._id}")
                return False

            obj_id = ObjectId(cita._id)

            update_data = {
                "$set": {
                    "nombre_mascota": cita.nombre_mascota,
                    "tipo_mascota": cita.tipo_mascota,
                    "raza": cita.raza,
                    "edad_mascota": cita.edad_mascota,
                    "telefono": cita.telefono,
                    "email": cita.email,
                    "fecha_cita": cita.fecha_cita,
                    "servicio": cita.servicio,
                    "notas": cita.notas,
                    "estado": cita.estado
                }
            }
            
            # Convertir user_id a ObjectId si es válido y si así se almacena en la DB
            query_user_id = cita.user_id
            if ObjectId.is_valid(cita.user_id):
                query_user_id = ObjectId(cita.user_id)
            else:
                print(f"DEBUG (ModelCita.update_cita): ID de usuario no válido en el objeto cita para la condición de actualización: {cita.user_id}")
                return False # No continuar si el user_id no es válido para la condición de seguridad

            result = db.citas.update_one(
                {"_id": obj_id, "user_id": query_user_id}, # Condición combinada por seguridad
                update_data
            )
            if result.modified_count > 0:
                print(f"DEBUG (ModelCita.update_cita): Cita {cita._id} actualizada exitosamente.")
                return True
            else:
                print(f"DEBUG (ModelCita.update_cita): Cita {cita._id} no encontrada para actualizar o no se realizaron cambios.")
                return False
        except Exception as ex:
            print(f"ERROR (ModelCita.update_cita): Error al actualizar la cita en MongoDB: {ex}")
            return False

    @classmethod
    def cancel_cita(cls, db, cita_id, user_id):
        try:
            if not ObjectId.is_valid(cita_id):
                print(f"DEBUG (ModelCita.cancel_cita): ID de cita no válido: {cita_id}")
                return False

            obj_id = ObjectId(cita_id)
            
            query_user_id = user_id
            if ObjectId.is_valid(user_id):
                query_user_id = ObjectId(user_id)
            else:
                print(f"DEBUG (ModelCita.cancel_cita): ID de usuario no válido para la condición de cancelación: {user_id}")
                return False

            result = db.citas.update_one(
                {"_id": obj_id, "user_id": query_user_id},
                {"$set": {"estado": "cancelada"}}
            )
            if result.modified_count > 0:
                print(f"DEBUG (ModelCita.cancel_cita): Cita {cita_id} cancelada exitosamente.")
                return True
            else:
                print(f"DEBUG (ModelCita.cancel_cita): Cita {cita_id} no encontrada para cancelar o ya estaba cancelada.")
                return False
        except Exception as ex:
            print(f"ERROR (ModelCita.cancel_cita): Error al cancelar la cita en MongoDB: {ex}")
            return False
            
    @classmethod
    def restore_cita(cls, db, cita_id, user_id):
        try:
            if not ObjectId.is_valid(cita_id):
                print(f"DEBUG (ModelCita.restore_cita): ID de cita no válido: {cita_id}")
                return False

            obj_id = ObjectId(cita_id)
            
            query_user_id = user_id
            if ObjectId.is_valid(user_id):
                query_user_id = ObjectId(user_id)
            else:
                print(f"DEBUG (ModelCita.restore_cita): ID de usuario no válido para la condición de restauración: {user_id}")
                return False

            result = db.citas.update_one(
                {"_id": obj_id, "user_id": query_user_id, "estado": "cancelada"}, # Asegura que solo se restauren las canceladas
                {"$set": {"estado": "pendiente"}}
            )
            if result.modified_count > 0:
                print(f"DEBUG (ModelCita.restore_cita): Cita {cita_id} restaurada exitosamente.")
                return True
            else:
                print(f"DEBUG (ModelCita.restore_cita): Cita {cita_id} no encontrada para restaurar o no estaba en estado 'cancelada'.")
                return False
        except Exception as ex:
            print(f"ERROR (ModelCita.restore_cita): Error al restaurar la cita en MongoDB: {ex}")
            return False

    @classmethod
    def get_dashboard_data(cls, db, user_id):
        try:
            query_user_id = user_id
            if ObjectId.is_valid(user_id):
                query_user_id = ObjectId(user_id)
            else:
                print(f"DEBUG (ModelCita.get_dashboard_data): ID de usuario no válido para el dashboard: {user_id}")
                return [], []

            rows = db.citas.find(
                {"user_id": query_user_id},
                {"_id": 1, "nombre_mascota": 1, "tipo_mascota": 1, "raza": 1, "edad_mascota": 1, 
                 "fecha_cita": 1, "servicio": 1, "estado": 1, "telefono": 1, "email": 1, "notas": 1} # Incluí más campos que podrían ser útiles en el dashboard
            ).sort("fecha_cita", -1)

            data = []
            columns = ["_id", "nombre_mascota", "tipo_mascota", "raza", "edad_mascota", "fecha_cita", "servicio", "estado", "telefono", "email", "notas"]
            
            for row in rows:
                row_data = []
                for col in columns:
                    value = row.get(col, None)
                    # Convertir ObjectId a string para serialización
                    if isinstance(value, ObjectId):
                        value = str(value)
                    row_data.append(value)
                data.append(row_data)
            
            return columns, data
        except Exception as ex:
            print(f"ERROR (ModelCita.get_dashboard_data): Error al obtener datos para el dashboard desde MongoDB: {ex}")
            return [], []