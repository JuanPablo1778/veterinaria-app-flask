# src/models/entities/Veterinarios.py
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin
from bson.objectid import ObjectId

class Veterinarios(UserMixin):
    def __init__(self, _id, username, password, matricula_profesional, nombre="", apellido_paterno="", apellido_materno="", telefono=None, email=None) -> None:
        # Asegura que _id sea un ObjectId si es válido, o genera uno nuevo si es None/inválido
        self._id = _id if isinstance(_id, ObjectId) else (ObjectId(_id) if _id and ObjectId.is_valid(_id) else ObjectId())
        self.username = username
        self.password = password
        self.matricula_profesional = matricula_profesional
        self.nombre = nombre
        self.apellido_paterno = apellido_paterno
        self.apellido_materno = apellido_materno
        self.telefono = telefono
        self.email = email

    @classmethod
    def check_password(cls, hashed_password, password):
        return check_password_hash(hashed_password, password)

    @classmethod
    def generate_password(cls, password):
        return generate_password_hash(password)

    # PARA FLASK-LOGIN: EL CAMBIO CRÍTICO ESTÁ AQUÍ
    def get_id(self):
        """
        Devuelve el ID del veterinario en un formato que Flask-Login puede guardar
        y el user_loader puede interpretar para distinguir entre tipos de usuarios.
        """
        return f"V_{str(self._id)}" # Convertimos el ObjectId a string para el prefijo

    # ¡Añade este método para obtener el ObjectId puro!
    def get_mongo_id(self):
        """Retorna el ObjectId puro del veterinario."""
        return self._id

    # Nuevo método para convertir el objeto a un diccionario compatible con MongoDB
    def to_mongo_dict(self):
        """
        Convierte el objeto Veterinarios a un diccionario para su almacenamiento en MongoDB.
        """
        data = {
            "_id": self._id, # MongoDB usará este _id si se proporciona, de lo contrario lo generará
            "username": self.username,
            "password": self.password,
            "matricula_profesional": self.matricula_profesional,
            "nombre": self.nombre,
            "apellido_paterno": self.apellido_paterno,
            "apellido_materno": self.apellido_materno,
            "telefono": self.telefono,
            "email": self.email
        }
        return {k: v for k, v in data.items() if v is not None} # Filtra los None