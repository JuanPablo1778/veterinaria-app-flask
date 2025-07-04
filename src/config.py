import os

class Config:
    # Es bueno mantener la SECRET_KEY aquí para que sea cargada por todas las configuraciones
    SECRET_KEY = 'BliweNAt1T^%kvhUI*S^' # Mantén esta clave SECRETA y difícil de adivinar

class DevelopmentConfig(Config):
    DEBUG = True
    
    # Tu URI de MongoDB es correcta
    MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://juanpa:hola@cluster0.tzkw9lo.mongodb.net/veterinaria?retryWrites=true&w=majority")
    
    # AÑADIR: El nombre de la base de datos que especificaste en la URI y que se usará.
    # En tu URI "mongodb+srv://juanpa:hola@cluster0.tzkw9lo.mongodb.net/veterinaria?retryWrites=true&w=majority"
    # la base de datos es 'veterinaria'.
    MONGO_DB_NAME = "Veterinaria" 


config={
    'development':DevelopmentConfig
}