# src/models/entities/Cita.py
from bson.objectid import ObjectId # Importar ObjectId para validación/conversión
import datetime # Para trabajar con fechas

class Cita:
    def __init__(self, _id, user_id, nombre_mascota, tipo_mascota, raza, edad_mascota, telefono, email, fecha_cita, servicio, estado='pendiente', notas=''):
        # MongoDB usa '_id'. Lo convertimos a string para facilitar el manejo en Python.
        # Si viene un ObjectId, lo convertimos a string. Si ya es string, lo usamos.
        self._id = str(_id) if isinstance(_id, ObjectId) else _id
        self.user_id = user_id
        self.nombre_mascota = nombre_mascota
        self.tipo_mascota = tipo_mascota
        self.raza = raza
        self.edad_mascota = edad_mascota
        self.telefono = telefono
        self.email = email
        self.fecha_cita = fecha_cita # Se espera un objeto datetime
        self.servicio = servicio
        self.estado = estado
        self.notas = notas

    def get_formatted_date(self):
        # Asegúrate de que fecha_cita sea un objeto datetime
        if isinstance(self.fecha_cita, datetime.datetime):
            return self.fecha_cita.strftime('%Y-%m-%d %H:%M')
        return str(self.fecha_cita) # Si no es datetime, devolverlo como string

    # Nuevo método para convertir el objeto a un diccionario compatible con MongoDB
    def to_mongo_dict(self):
        data = {
            "user_id": self.user_id,
            "nombre_mascota": self.nombre_mascota,
            "tipo_mascota": self.tipo_mascota,
            "raza": self.raza,
            "edad_mascota": self.edad_mascota,
            "telefono": self.telefono,
            "email": self.email,
            "fecha_cita": self.fecha_cita, # MongoDB puede almacenar objetos datetime directamente
            "servicio": self.servicio,
            "estado": self.estado,
            "notas": self.notas
        }
        # Si _id existe y es un string que se puede convertir a ObjectId, lo incluimos.
        # Esto es útil si estás actualizando un documento existente.
        if self._id and ObjectId.is_valid(self._id):
            data["_id"] = ObjectId(self._id)
        return data

    def __repr__(self):
        return f"<Cita ID:{self._id} Mascota:{self.nombre_mascota} Fecha:{self.fecha_cita}>"