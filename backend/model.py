from datetime import datetime #Importa el módulo datetime para manejo de fechas y horas
from flask_sqlalchemy import SQLAlchemy #Importa SQLAlchemy desde Flask para el manejo de la base de datos

db = SQLAlchemy() #Crea una instancia de SQLAlchemy para la aplicación

class Usuario(db.Model): #Define la clase Usuario que hereda de db.Model
    __tablename__ = 'usuarios_chat' #Establece el nombre de la tabla como 'usuarios_chat'

    id = db.Column(db.Integer, primary_key=True) #Define el campo id como clave primaria de tipo entero
    cedula = db.Column(db.String(20), unique=True, nullable=False) #Define el campo cedula como string único de 20 caracteres, no nulo
    nombre_completo = db.Column(db.String(100), nullable=False) #Define el campo nombre_completo como string de 100 caracteres, no nulo
    activo = db.Column(db.Boolean, default=True) #Define el campo activo como booleano con valor por defecto True

    def __init__(self, cedula, nombre_completo, activo=True): #Define el método constructor con parámetros opcionales
        self.cedula = cedula #Asigna el valor de cédula al atributo correspondiente
        self.nombre_completo = nombre_completo #Asigna el nombre completo al atributo correspondiente
        self.activo = activo

    def __repr__(self): #Define el método __repr__ para representación string del objeto
        return f"<Usuario {self.nombre_completo}>" #Retorna una cadena formateada con el nombre completo del usuario


class QueryLog(db.Model): #Define la clase QueryLog que hereda de db.Model
    __tablename__ = 'query_logs' #Establece el nombre de la tabla como 'query_logs'

    #Define los campos del modelo:
    id = db.Column(db.Integer, primary_key=True) #Clave primaria
    pregunta = db.Column(db.Text, nullable=False) #Texto de la consulta realizada
    respuesta = db.Column(db.Text, nullable=False) #Texto de la respuesta generada
    modelo_usado = db.Column(db.String(255)) #Identificador del modelo utilizado
    tiempo_embeddings = db.Column(db.Float) #Tiempo de procesamiento de embeddings
    tiempo_consulta_modelo = db.Column(db.Float) #Tiempo de consulta al modelo
    tokens_pregunta = db.Column(db.Integer) #Cantidad de tokens en la pregunta
    tokens_documentos = db.Column(db.Integer) #Tokens de documentos consultados
    tokens_respuesta = db.Column(db.Integer) #Tokens en la respuesta generada
    fecha_consulta = db.Column(db.DateTime, default=datetime.utcnow) #Timestamp de la consulta con valor por defecto actual