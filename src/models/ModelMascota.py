# src/models/ModelMascota.py

from src.models.entities.Mascota import Mascota
from bson.objectid import ObjectId

class ModelMascota():

    @classmethod
    def register_mascota(self, db, mascota):
        try:
            # === CAMBIO CLAVE AQUÍ: Usar .to_dict() en lugar de .to_mongo_dict() ===
            mascota_data = mascota.to_dict()
            
            if "_id" in mascota_data and mascota_data["_id"] is None:
                del mascota_data["_id"]

            result = db.perfiles_mascotas.insert_one(mascota_data)
            
            if result.inserted_id:
                mascota._id = str(result.inserted_id)
                print(f"DEBUG (ModelMascota.register_mascota): Mascota '{mascota.nombre}' registrada con _id: {mascota._id}")
                return True
            print(f"DEBUG (ModelMascota.register_mascota): La inserción de la mascota '{mascota.nombre}' no generó un inserted_id.")
            return False
        except Exception as ex:
            # Aquí también cambia a .to_dict() para la depuración si es necesario
            # Aunque en un error de atributo, esto podría fallar también, es útil para otros errores.
            print(f"ERROR (ModelMascota.register_mascota): Error al registrar mascota en MongoDB: {ex}") # Eliminé mascota.to_mongo_dict() para evitar recursión de error
            return False

    @classmethod
    def get_mascotas_by_user(self, db, user_id):
        try:
            mascotas = []
            
            if not ObjectId.is_valid(user_id):
                print(f"DEBUG (ModelMascota.get_mascotas_by_user): user_id no válido para la búsqueda: {user_id}")
                return [] 

            query_user_id = ObjectId(user_id)
            rows = db.perfiles_mascotas.find({"user_id": query_user_id})

            for row in rows:
                mascotas.append(Mascota(
                    _id=row.get('_id'),
                    user_id=row.get('user_id'),
                    nombre=row.get('nombre'),
                    especie=row.get('especie'),
                    raza=row.get('raza'),
                    sexo=row.get('sexo'),
                    edad=row.get('edad'),
                    color=row.get('color'),
                    fecha_nacimiento=row.get('fecha_nacimiento'),
                    notas=row.get('notas')
                ))
            return mascotas
        except Exception as ex:
            print(f"ERROR (ModelMascota.get_mascotas_by_user): Error al obtener mascotas por usuario: {ex}")
            return []

    @classmethod
    def get_mascota_by_id(self, db, mascota_id):
        try:
            if not ObjectId.is_valid(mascota_id):
                print(f"DEBUG (ModelMascota.get_mascota_by_id): ID de mascota no válido: {mascota_id}")
                return None

            obj_id = ObjectId(mascota_id)
            row = db.perfiles_mascotas.find_one({"_id": obj_id})
            
            if row:
                return Mascota(
                    _id=row.get('_id'),
                    user_id=row.get('user_id'),
                    nombre=row.get('nombre'),
                    especie=row.get('especie'),
                    raza=row.get('raza'),
                    sexo=row.get('sexo'),
                    edad=row.get('edad'),
                    color=row.get('color'),
                    fecha_nacimiento=row.get('fecha_nacimiento'),
                    notas=row.get('notas')
                )
            else:
                print(f"DEBUG (ModelMascota.get_mascota_by_id): Mascota con ID {mascota_id} no encontrada.")
                return None
        except Exception as ex:
            print(f"ERROR (ModelMascota.get_mascota_by_id): Error al obtener mascota por ID: {ex}")
            return None

    @classmethod
    def update_mascota(self, db, mascota):
        """
        Actualiza los datos de una mascota existente.
        """
        try:
            if not ObjectId.is_valid(mascota._id):
                print(f"DEBUG (ModelMascota.update_mascota): ID de mascota no válido: {mascota._id}")
                return False
            
            # === CAMBIO CLAVE AQUÍ: Usar .to_dict() en lugar de .to_mongo_dict() ===
            update_data_raw = mascota.to_dict()
            
            update_data = {"$set": {k: v for k, v in update_data_raw.items() if k not in ["_id", "user_id"]}}

            obj_id = ObjectId(mascota._id)
            query_user_id = ObjectId(mascota.user_id)

            result = db.perfiles_mascotas.update_one(
                {"_id": obj_id, "user_id": query_user_id},
                update_data
            )
            
            if result.modified_count > 0:
                print(f"DEBUG (ModelMascota.update_mascota): Mascota {mascota._id} actualizada.")
                return True
            else:
                print(f"DEBUG (ModelMascota.update_mascota): No se encontró la mascota {mascota._id} o no se modificaron datos.")
                return False
        except Exception as ex:
            print(f"ERROR (ModelMascota.update_mascota): Error al actualizar mascota: {ex}")
            return False

    @classmethod
    def delete_mascota(self, db, mascota_id, user_id):
        """
        Elimina una mascota de la base de datos.
        """
        try:
            if not ObjectId.is_valid(mascota_id):
                print(f"DEBUG (ModelMascota.delete_mascota): ID de mascota no válido: {mascota_id}")
                return False

            obj_id = ObjectId(mascota_id)
            
            if not ObjectId.is_valid(user_id):
                print(f"DEBUG (ModelMascota.delete_mascota): user_id de la mascota no válido para eliminación: {user_id}")
                return False
            
            query_user_id = ObjectId(user_id)

            result = db.perfiles_mascotas.delete_one({"_id": obj_id, "user_id": query_user_id})
            
            if result.deleted_count > 0:
                print(f"DEBUG (ModelMascota.delete_mascota): Mascota {mascota_id} del usuario {user_id} eliminada exitosamente.")
                return True
            else:
                print(f"DEBUG (ModelMascota.delete_mascota): No se encontró la mascota {mascota_id} del usuario {user_id} para eliminar.")
                return False
        except Exception as ex:
            print(f"ERROR (ModelMascota.delete_mascota): Error al eliminar mascota: {ex}")
            return False