from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId # Importar ObjectId

class User(UserMixin):
    def __init__(self, _id, username, password, nombre=None, apellido_paterno=None, apellido_materno=None, telefono=None, email=None): # CAMBIO AQUÍ
        # Asegurarse de que _id sea un string si viene como ObjectId
        self._id = str(_id) if isinstance(_id, ObjectId) else _id
        self.username = username
        self.password = password # Ya debería ser hasheada cuando se pasa aquí
        self.nombre = nombre # Ahora es opcional
        self.apellido_paterno = apellido_paterno # Ahora es opcional
        self.apellido_materno = apellido_materno
        self.telefono = telefono
        self.email = email

    @property
    def id(self):
        return f'U_{self._id}'

    def get_id(self):
        return self.id

    def is_active(self):
        return True

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    @staticmethod
    def generate_password(password):
        return generate_password_hash(password)

    @staticmethod
    def verify_password(hashed_password, password):
        return check_password_hash(hashed_password, password)

    def to_dict(self):
        return {
            "_id": ObjectId(self._id) if self._id else None,
            "username": self.username,
            "password": self.password,
            "nombre": self.nombre,
            "apellido_paterno": self.apellido_paterno,
            "apellido_materno": self.apellido_materno,
            "telefono": self.telefono,
            "email": self.email
        }