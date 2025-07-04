# src/models/ModelVeterinarios.py

from src.models.entities.Veterinarios import Veterinarios # Ajustar la ruta de importación
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId # Necesario para trabajar con _id de MongoDB

class ModelVeterinarios():

    @classmethod
    def login(self, db, veterinario):
        try:
            row = db.veterinarios.find_one({"username": veterinario.username})

            if row is not None:
                # Verificar la contraseña hasheada y la matrícula profesional
                # Usar .get() para evitar KeyError si el campo no existe en la DB (aunque debería).
                db_hashed_password = row.get('password')
                db_matricula = row.get('matricula_profesional')

                if db_hashed_password and check_password_hash(db_hashed_password, veterinario.password) and \
                   db_matricula == veterinario.matricula_profesional:
                    
                    return Veterinarios(
                        _id=row.get('_id'), 
                        username=row.get('username'),
                        password=row.get('password'), 
                        matricula_profesional=row.get('matricula_profesional'),
                        nombre=row.get('nombre'),
                        apellido_paterno=row.get('apellido_paterno'),
                        apellido_materno=row.get('apellido_materno'),
                        telefono=row.get('telefono'),
                        email=row.get('email')
                    )
                else:
                    print(f"DEBUG (ModelVeterinarios.login): Contraseña o matrícula profesional incorrecta para el veterinario: {veterinario.username}")
                    return None 
            else:
                print(f"DEBUG (ModelVeterinarios.login): Veterinario no encontrado: {veterinario.username}")
                return None 
        except Exception as ex:
            print(f"ERROR (ModelVeterinarios.login): Ocurrió un error al intentar iniciar sesión de veterinario: {ex}")
            # Es mejor retornar None en caso de error para que Flask-Login lo maneje gracefully
            return None

    @classmethod
    def get_by_id(self, db, id):
        try:
            if not ObjectId.is_valid(id):
                print(f"DEBUG (ModelVeterinarios.get_by_id): ID proporcionado no es un ObjectId válido: {id}")
                return None

            obj_id = ObjectId(id) 
            row = db.veterinarios.find_one({"_id": obj_id})

            if row is not None:
                return Veterinarios(
                    _id=row.get('_id'),
                    username=row.get('username'),
                    password=None, # No necesitamos la contraseña para este método
                    matricula_profesional=row.get('matricula_profesional'),
                    nombre=row.get('nombre'),
                    apellido_paterno=row.get('apellido_paterno'),
                    apellido_materno=row.get('apellido_materno'),
                    telefono=row.get('telefono'),
                    email=row.get('email')
                )
            else:
                print(f"DEBUG (ModelVeterinarios.get_by_id): Veterinario con ID {id} no encontrado.")
                return None
        except Exception as ex:
            print(f"ERROR (ModelVeterinarios.get_by_id): Ocurrió un error al obtener veterinario por ID: {ex}")
            return None

    @classmethod
    def register(self, db, veterinario):
        try:
            # 1. Verificar si el nombre de usuario ya existe
            if db.veterinarios.find_one({"username": veterinario.username}):
                print(f"DEBUG (ModelVeterinarios.register): Registro fallido: El nombre de usuario '{veterinario.username}' ya existe.")
                return False

            # 2. Verificar si la matrícula profesional ya existe
            if db.veterinarios.find_one({"matricula_profesional": veterinario.matricula_profesional}):
                print(f"DEBUG (ModelVeterinarios.register): Registro fallido: La matrícula profesional '{veterinario.matricula_profesional}' ya está registrada.")
                return False

            # 3. Insertar el nuevo veterinario
            veterinario_data = veterinario.to_mongo_dict()
            
            # Asegúrate de que el '_id' no se incluya en la inserción si quieres que MongoDB lo genere
            veterinario_data.pop('_id', None) 

            result = db.veterinarios.insert_one(veterinario_data)
            
            if result.inserted_id:
                veterinario._id = str(result.inserted_id)
                print(f"DEBUG (ModelVeterinarios.register): Veterinario '{veterinario.username}' registrado con _id: {veterinario._id}")
                return True
            print(f"DEBUG (ModelVeterinarios.register): La inserción del veterinario '{veterinario.username}' no generó un inserted_id.")
            return False

        except Exception as ex:
            print(f"ERROR (ModelVeterinarios.register): Ocurrió un error al registrar veterinario: {ex}") 
            return False

    @classmethod
    def update_veterinario_profile(self, db, veterinario):
        """
        Actualiza el perfil de un veterinario existente.
        """
        try:
            if not ObjectId.is_valid(veterinario._id):
                print(f"DEBUG (ModelVeterinarios.update_veterinario_profile): ID de veterinario no válido: {veterinario._id}")
                return False

            obj_id = ObjectId(veterinario._id)
            
            update_data = {
                "$set": {
                    "matricula_profesional": veterinario.matricula_profesional,
                    "nombre": veterinario.nombre,
                    "apellido_paterno": veterinario.apellido_paterno,
                    "apellido_materno": veterinario.apellido_materno,
                    "telefono": veterinario.telefono,
                    "email": veterinario.email
                }
            }
            
            result = db.veterinarios.update_one(
                {"_id": obj_id},
                update_data
            )
            if result.modified_count > 0:
                print(f"DEBUG (ModelVeterinarios.update_veterinario_profile): Perfil del veterinario {veterinario._id} actualizado.")
                return True
            else:
                print(f"DEBUG (ModelVeterinarios.update_veterinario_profile): No se encontró el veterinario {veterinario._id} o no se modificaron datos.")
                return False
        except Exception as ex:
            print(f"ERROR (ModelVeterinarios.update_veterinario_profile): Error al actualizar perfil de veterinario: {ex}")
            return False # Retorna False en caso de error


    @classmethod
    def update_veterinario_password(self, db, veterinario_id, new_hashed_password):
        """
        Actualiza la contraseña de un veterinario.
        """
        try:
            if not ObjectId.is_valid(veterinario_id):
                print(f"DEBUG (ModelVeterinarios.update_veterinario_password): ID de veterinario no válido: {veterinario_id}")
                return False

            obj_id = ObjectId(veterinario_id)
            result = db.veterinarios.update_one(
                {"_id": obj_id},
                {"$set": {"password": new_hashed_password}}
            )
            if result.modified_count > 0:
                print(f"DEBUG (ModelVeterinarios.update_veterinario_password): Contraseña del veterinario {veterinario_id} actualizada.")
                return True
            else:
                print(f"DEBUG (ModelVeterinarios.update_veterinario_password): No se encontró el veterinario {veterinario_id} o la contraseña no cambió.")
                return False
        except Exception as ex:
            print(f"ERROR (ModelVeterinarios.update_veterinario_password): Error al actualizar contraseña de veterinario: {ex}")
            return False # Retorna False en caso de error

    @classmethod
    def delete_veterinario(self, db, veterinario_id):
        """
        Elimina un veterinario de la base de datos.
        """
        try:
            if not ObjectId.is_valid(veterinario_id):
                print(f"DEBUG (ModelVeterinarios.delete_veterinario): ID de veterinario no válido: {veterinario_id}")
                return False

            obj_id = ObjectId(veterinario_id)
            result = db.veterinarios.delete_one({"_id": obj_id})
            if result.deleted_count > 0:
                print(f"DEBUG (ModelVeterinarios.delete_veterinario): Veterinario {veterinario_id} eliminado exitosamente.")
                return True
            else:
                print(f"DEBUG (ModelVeterinarios.delete_veterinario): No se encontró el veterinario {veterinario_id} para eliminar.")
                return False
        except Exception as ex:
            print(f"ERROR (ModelVeterinarios.delete_veterinario): Error al eliminar veterinario: {ex}")
            return False # Retorna False en caso de error
        
        #es de chat
    @classmethod
    def get_all_veterinarios(self, db):
        """
        Obtiene todos los veterinarios de la base de datos.
        """
        try:
            veterinarios_cursor = db.veterinarios.find({})
            veterinarios = []
            for vet_doc in veterinarios_cursor:
                # Mapear el documento de MongoDB a los parámetros del constructor de Veterinarios
                # Utiliza .get() con valores por defecto para campos que podrían no existir.
                veterinarios.append(Veterinarios(
                    _id=vet_doc.get('_id'), 
                    username=vet_doc.get('username'),
                    password=vet_doc.get('password'), # Se asume que es la hasheada
                    matricula_profesional=vet_doc.get('matricula_profesional'),
                    nombre=vet_doc.get('nombre', ""), 
                    apellido_paterno=vet_doc.get('apellido_paterno', ""),
                    apellido_materno=vet_doc.get('apellido_materno', ""),
                    telefono=vet_doc.get('telefono'),
                    email=vet_doc.get('email')
                ))
            return veterinarios
        except Exception as ex:
            print(f"ERROR (ModelVeterinarios.get_all_veterinarios): Error al obtener todos los veterinarios: {ex}")
            return [] # Retorna una lista vacía en caso de error