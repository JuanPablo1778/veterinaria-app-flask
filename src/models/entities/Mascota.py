from bson import ObjectId
import datetime # <-- Añade esta importación

class Mascota:
    def __init__(self, _id, user_id, nombre, especie, raza=None, sexo=None, edad=None, color=None, fecha_nacimiento=None, notas=None):
        self._id = str(_id) if isinstance(_id, ObjectId) else _id
        # user_id también debe ser un string si es un ObjectId, para consistencia con _id de Mascota
        self.user_id = str(user_id) if isinstance(user_id, ObjectId) else user_id
        self.nombre = nombre
        self.especie = especie
        self.raza = raza
        self.sexo = sexo
        self.edad = edad
        self.color = color

        # Manejo de fecha_nacimiento
        if isinstance(fecha_nacimiento, datetime.datetime):
            self.fecha_nacimiento = fecha_nacimiento
        elif isinstance(fecha_nacimiento, datetime.date):
            # Convierte datetime.date a datetime.datetime al inicio del día
            self.fecha_nacimiento = datetime.datetime(fecha_nacimiento.year, fecha_nacimiento.month, fecha_nacimiento.day)
        elif isinstance(fecha_nacimiento, str) and fecha_nacimiento:
            try:
                # Intenta parsear el string a datetime.datetime
                self.fecha_nacimiento = datetime.datetime.strptime(fecha_nacimiento, '%Y-%m-%d')
            except ValueError:
                print(f"Advertencia: Formato de fecha '{fecha_nacimiento}' no reconocido para Mascota '{nombre}'. Se asigna como None.")
                self.fecha_nacimiento = None
        elif fecha_nacimiento is None:
            self.fecha_nacimiento = None
        else:
            print(f"Advertencia: fecha_nacimiento tiene un tipo inesperado: {type(fecha_nacimiento)} para la mascota '{nombre}'. Se asigna como None.")
            self.fecha_nacimiento = None

        self.notas = notas

    # Añade este método para convertir el objeto Mascota a un diccionario para MongoDB
    def to_dict(self):
        doc = {
            "user_id": ObjectId(self.user_id), # Asegúrate de que user_id se convierta a ObjectId
            "nombre": self.nombre,
            "especie": self.especie,
            "raza": self.raza,
            "sexo": self.sexo,
            "edad": self.edad,
            "color": self.color,
            "notas": self.notas
        }
        if self._id:
            doc["_id"] = ObjectId(self._id)
        if self.fecha_nacimiento:
            # Asegúrate de que fecha_nacimiento es un datetime.datetime
            if isinstance(self.fecha_nacimiento, datetime.date) and not isinstance(self.fecha_nacimiento, datetime.datetime):
                doc["fecha_nacimiento"] = datetime.datetime(self.fecha_nacimiento.year, self.fecha_nacimiento.month, self.fecha_nacimiento.day)
            else:
                doc["fecha_nacimiento"] = self.fecha_nacimiento
        return doc