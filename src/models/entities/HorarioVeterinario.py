# src/models/entities/HorarioVeterinario.py
from bson.objectid import ObjectId
import datetime # Necesario para el parsing de tiempo

class HorarioVeterinario:
    def __init__(self, _id, veterinario_id, dia_semana, mes, anio, hora_inicio, hora_fin, esta_disponible):
        # Manejo de _id: Si _id es None, se genera un nuevo ObjectId. Si es string válido, se convierte. Si ya es ObjectId, se usa.
        self._id = _id if isinstance(_id, ObjectId) else (ObjectId(_id) if _id and ObjectId.is_valid(_id) else None) # Set to None if it's new
        
        # Manejo de veterinario_id: Similar a _id
        self.veterinario_id = veterinario_id if isinstance(veterinario_id, ObjectId) else (ObjectId(veterinario_id) if veterinario_id and ObjectId.is_valid(veterinario_id) else None)
        
        self.dia_semana = dia_semana
        self.mes = mes
        self.anio = anio
        self.hora_inicio = hora_inicio 
        self.hora_fin = hora_fin    
        self.esta_disponible = esta_disponible

    # --- NUEVAS PROPIEDADES PARA DISPLAY ---
    @property
    def hora_inicio_display(self):
        try:
            # Parsear el string 'HH:MM' a un objeto time y luego formatear
            hora_obj = datetime.datetime.strptime(self.hora_inicio, "%H:%M").time()
            return hora_obj.strftime("%I:%M %p") # Formato 12 horas con AM/PM
        except (ValueError, TypeError):
            return self.hora_inicio # Retorna el valor original si hay un error o no es string
    
    @property
    def hora_fin_display(self):
        try:
            # Parsear el string 'HH:MM' a un objeto time y luego formatear
            hora_obj = datetime.datetime.strptime(self.hora_fin, "%H:%M").time()
            return hora_obj.strftime("%I:%M %p") # Formato 12 horas con AM/PM
        except (ValueError, TypeError):
            return self.hora_fin # Retorna el valor original si hay un error o no es string
    # --- FIN NUEVAS PROPIEDADES ---

    def get_id(self):
        return str(self._id)

    def to_dict(self): # <--- THIS IS THE METHOD app.py IS LOOKING FOR!
        """
        Convierte la instancia de HorarioVeterinario en un diccionario.
        Útil para pre-rellenar formularios HTML.
        """
        return {
            '_id': str(self._id) if self._id else '', # Convert ObjectId to string for form/URL
            'veterinario_id': str(self.veterinario_id) if self.veterinario_id else '', # Convert ObjectId to string
            'dia_semana': self.dia_semana,
            'mes': self.mes,
            'anio': self.anio,
            'hora_inicio': self.hora_inicio,
            'hora_fin': self.hora_fin,
            # Para checkboxes, es común usar '1' o '0' como strings
            'esta_disponible': '1' if self.esta_disponible == 1 else '0'
        }

    def to_mongo_dict(self):
        """
        Convierte la instancia a un diccionario adecuado para inserción/actualización en MongoDB.
        Asegura que los ObjectId sean pasados como ObjectId.
        """
        data = {
            # _id solo se incluye si ya existe (para actualizaciones)
            # Para nuevas inserciones, MongoDB lo generará.
            # Aquí se asume que self._id ya es un ObjectId o None.
            "veterinario_id": self.veterinario_id, # Este ya debería ser un ObjectId
            "dia_semana": self.dia_semana,
            "mes": self.mes,
            "anio": self.anio,
            "hora_inicio": self.hora_inicio,
            "hora_fin": self.hora_fin,
            "esta_disponible": self.esta_disponible
        }
        if self._id: # Solo incluir _id si ya está establecido (para operaciones de update/replace)
            data["_id"] = self._id 
        return {k: v for k, v in data.items() if v is not None}

    @staticmethod
    def from_mongo_dict(data):
        """
        Crea una instancia de HorarioVeterinario desde un diccionario de MongoDB.
        """
        if not data:
            return None
        return HorarioVeterinario(
            _id=data.get('_id'), # MongoDB devuelve ObjectId
            veterinario_id=data.get('veterinario_id'), # MongoDB devuelve ObjectId
            dia_semana=data.get('dia_semana'),
            mes=data.get('mes'),
            anio=data.get('anio'),
            hora_inicio=data.get('hora_inicio'),
            hora_fin=data.get('hora_fin'),
            esta_disponible=data.get('esta_disponible', 0)
        )

    def __repr__(self):
        return f"<HorarioVeterinario ID:{self._id} Vet:{self.veterinario_id} {self.dia_semana} {self.mes}/{self.anio} {self.hora_inicio}-{self.hora_fin}>"