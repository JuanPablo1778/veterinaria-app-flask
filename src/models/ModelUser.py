# src/models/ModelUser.py

from src.models.entities.User import User
from bson.objectid import ObjectId

class ModelUser():

    @classmethod
    def login(self, db, user):
        try:
            row = db.users.find_one({"username": user.username})

            if row is not None:
                # === CAMBIO AQUÍ: Usar verify_password en lugar de check_password ===
                if User.verify_password(row.get('password'), user.password):
                    return User(
                        _id=row.get('_id'),
                        username=row.get('username'),
                        password=row.get('password'),
                        nombre=row.get('nombre'),
                        apellido_paterno=row.get('apellido_paterno'),
                        apellido_materno=row.get('apellido_materno'),
                        telefono=row.get('telefono'),
                        email=row.get('email')
                    )
                else:
                    print(f"DEBUG (ModelUser.login): Contraseña incorrecta para el usuario: {user.username}")
                    return None
            else:
                print(f"DEBUG (ModelUser.login): Usuario no encontrado: {user.username}")
                return None
        except Exception as ex:
            print(f"ERROR (ModelUser.login): Ocurrió un error al intentar iniciar sesión: {ex}")
            return None

    @classmethod
    def get_by_id(cls, db, user_id):
        try:
            # Asegúrate de manejar el prefijo 'U_' si tu `get_id` lo añade
            # Basado en tu User.py, user_id que llega a get_by_id DEBE ser el ObjectId puro
            # Si Flask-Login te pasa 'U_...', necesitas splittearlo aquí.
            # Según la traza anterior (image_9096fc.png), en ModelUser.py, línea 52,
            # tienes `actual_id = id_from_session.split('_')[1]`. Si user_id ya es el id puro
            # sin prefijo, esta línea causará un IndexError.
            # Vamos a asumir que load_user en app.py ya lo limpia, o que user_id aquí ya es el puro ObjectId string.
            
            # Si el user_id viene de Flask-Login como 'U_algoid', necesita ser limpiado:
            # if user_id.startswith('U_'):
            #     user_id = user_id.split('_')[1] # Esto lo haría aquí si es necesario

            if not ObjectId.is_valid(user_id):
                print(f"DEBUG (ModelUser.get_by_id): ID de usuario no válido: {user_id}")
                return None

            obj_id = ObjectId(user_id)
            row = db.users.find_one({"_id": obj_id})
            if row:
                return User(
                    _id=row.get('_id'),
                    username=row.get('username'),
                    password=row.get('password'),
                    nombre=row.get('nombre'),
                    apellido_paterno=row.get('apellido_paterno'),
                    apellido_materno=row.get('apellido_materno'),
                    telefono=row.get('telefono'),
                    email=row.get('email')
                )
            else:
                print(f"DEBUG (ModelUser.get_by_id): Usuario con ID {user_id} no encontrado.")
                return None
        except Exception as ex:
            print(f"ERROR (ModelUser.get_by_id): Error al obtener usuario por ID desde MongoDB: {ex}")
            return None

    @classmethod
    def register(self, db, user):
        try:
            if db.users.find_one({"username": user.username}):
                print(f"DEBUG (ModelUser.register): Registro fallido: El usuario '{user.username}' ya existe.")
                return False

            user_data = user.to_dict() # Asumo que tu User.py tiene un to_dict()
            user_data.pop('_id', None) # Asegura que MongoDB genere el _id

            # Asegúrate de hashear la contraseña ANTES de guardar
            user_data['password'] = User.generate_password(user.password) # Hashear aquí

            result = db.users.insert_one(user_data)
            
            if result.inserted_id:
                user._id = str(result.inserted_id)
                print(f"DEBUG (ModelUser.register): Usuario '{user.username}' registrado con _id: {user._id}")
                return True
            print(f"DEBUG (ModelUser.register): La inserción del usuario '{user.username}' no generó un inserted_id.")
            return False

        except Exception as ex:
            print(f"ERROR (ModelUser.register): Ocurrió un error al registrar usuario: {ex}")
            return False

    @classmethod
    def update_user_profile(self, db, user):
        """
        Actualiza el perfil de un usuario existente.
        """
        try:
            if not ObjectId.is_valid(user._id):
                print(f"DEBUG (ModelUser.update_user_profile): ID de usuario no válido: {user._id}")
                return False

            obj_id = ObjectId(user._id)
            
            update_data = {
                "$set": {
                    "nombre": user.nombre,
                    "apellido_paterno": user.apellido_paterno,
                    "apellido_materno": user.apellido_materno,
                    "telefono": user.telefono,
                    "email": user.email
                }
            }
            
            result = db.users.update_one(
                {"_id": obj_id},
                update_data
            )
            if result.modified_count > 0:
                print(f"DEBUG (ModelUser.update_user_profile): Perfil del usuario {user._id} actualizado.")
                return True
            else:
                print(f"DEBUG (ModelUser.update_user_profile): No se encontró el usuario {user._id} o no se modificaron datos.")
                return False
        except Exception as ex:
            print(f"ERROR (ModelUser.update_user_profile): Error al actualizar perfil de usuario: {ex}")
            return False

    @classmethod
    def update_user_password(self, db, user_id, new_hashed_password):
        """
        Actualiza la contraseña de un usuario.
        """
        try:
            if not ObjectId.is_valid(user_id):
                print(f"DEBUG (ModelUser.update_user_password): ID de usuario no válido: {user_id}")
                return False

            obj_id = ObjectId(user_id)
            result = db.users.update_one(
                {"_id": obj_id},
                {"$set": {"password": new_hashed_password}}
            )
            if result.modified_count > 0:
                print(f"DEBUG (ModelUser.update_user_password): Contraseña del usuario {user_id} actualizada.")
                return True
            else:
                print(f"DEBUG (ModelUser.update_user_password): No se encontró el usuario {user_id} o la contraseña no cambió.")
                return False
        except Exception as ex:
            print(f"ERROR (ModelUser.update_user_password): Error al actualizar contraseña: {ex}")
            return False

    @classmethod
    def delete_user(self, db, user_id):
        """
        Elimina un usuario de la base de datos.
        """
        try:
            if not ObjectId.is_valid(user_id):
                print(f"DEBUG (ModelUser.delete_user): ID de usuario no válido: {user_id}")
                return False

            obj_id = ObjectId(user_id)
            result = db.users.delete_one({"_id": obj_id})
            if result.deleted_count > 0:
                print(f"DEBUG (ModelUser.delete_user): Usuario {user_id} eliminado exitosamente.")
                return True
            else:
                print(f"DEBUG (ModelUser.delete_user): No se encontró el usuario {user_id} para eliminar.")
                return False
        except Exception as ex:
            print(f"ERROR (ModelUser.delete_user): Error al eliminar usuario: {ex}")
            return False
        
    @classmethod
    def get_all_users(self, db):
        """
        Obtiene todos los usuarios de la base de datos.
        """
        try:
            users_cursor = db.users.find({})
            users = []
            for user_doc in users_cursor:
                users.append(User(
                    _id=user_doc.get('_id'),
                    username=user_doc.get('username'),
                    password=user_doc.get('password'),
                    nombre=user_doc.get('nombre', ""),
                    apellido_paterno=user_doc.get('apellido_paterno', ""),
                    apellido_materno=user_doc.get('apellido_materno', ""),
                    telefono=user_doc.get('telefono'),
                    email=user_doc.get('email')
                ))
            return users
        except Exception as ex:
            print(f"ERROR (ModelUser.get_all_users): Error al obtener todos los usuarios de MongoDB: {ex}")
            return []