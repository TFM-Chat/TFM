from datetime import datetime
import os
from flask import Flask, request, jsonify, send_file
from dotenv import load_dotenv
from flask_cors import CORS
from model import Usuario,db, QueryLog
from services.query_service import handle_query,query_all_docs,update_file_principal,get_max_row_number_ns,call_index_for_update
from services.model_service import get_llm, get_embeddings ,get_embeddings_option_2
import logging
from logging_module.logging_config import setup_logging
import requests
import hashlib
import json

import pandas as pd
from io import BytesIO
from werkzeug.datastructures import FileStorage

from services.upload_file_utils import chunk_document, extract_text_from_document, get_file_size, upload_to_blob_storage, vectorize_and_save_to_cosmos, rollback_blob, rollback_cosmos, rollback_index_update


class Config:
    # Configuración de la base de datos MySQL
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://admin:xxxxxxx@mysql.mysql.database.azure.com:3306/infraestructura'
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Elimina la coma aquí

# Configurar logging
setup_logging()

app = Flask(__name__)
CORS(app)
app.config.from_object(Config)
db.init_app(app)
load_dotenv()

@app.route("/query", methods=["POST"])
def query():
    logging.info(f'Modelo: {os.getenv("MODELO")}')
    data = request.get_json()
    if not data or 'question' not in data or 'recaptchaToken' not in data:
        logging.error("Invalid input or missing reCAPTCHA token")
        return jsonify({"error": "Invalid input or missing reCAPTCHA token"}), 400

    # Verify reCAPTCHA token
    recaptcha_response = data['recaptchaToken']
    embeddings_selected = get_embeddings
    use_cosmosdb = os.getenv('USE_ALTERNATIVE', 'false').lower() == 'true'
    if use_cosmosdb:
        embeddings_selected = get_embeddings_option_2

    response_data = handle_query(data['question'], get_llm, embeddings_selected)

    return jsonify(response_data)


@app.route("/download-log", methods=["POST"])
def download_log():
    data = request.get_json()
    if not data or 'key' not in data:
        logging.error("Invalid input received for download-log")
        return jsonify({"error": "Invalid input"}), 400
    
    provided_key = data['key']
    correct_key = os.getenv('KEY_LOG')

    if provided_key == correct_key:
        log_file_path = 'application.log'
        if os.path.exists(log_file_path):
            return send_file(log_file_path, as_attachment=True)
        else:
            logging.error("Log file does not exist")
            return jsonify({"error": "Log file does not exist"}), 404
    else:
        logging.error("Unauthorized access attempt to download log file")
        return jsonify({"error": "Unauthorized"}), 401
    
# Nuevo endpoint para consultar los documentos en Cosmos DB a
@app.route("/all-documents", methods=["GET"])
def get_cosmosdb_documents():
    # Llamar al servicio que obtiene todos los documentos de Cosmos DB
    documents, status_code = query_all_docs()
    return jsonify(documents), status_code    

# Endpoint para actualizar un documento (borrado lógico)
@app.route('/updatedocument', methods=['PUT'])
def update_document():
    # Obtener los datos del cuerpo de la solicitud en formato JSON
    data = request.get_json()
    
    # Extraer 'row_number' y 'tipo' del JSON
    row_number = data.get('row_number')
    tipo = data.get('tipo')
    info_usuario=data.get('infoUsuario')
    razon_accion=data.get('razonAccion')

    if row_number is None or tipo is None:
        return jsonify({'error': 'Faltan parámetros'}), 400

    # Llamar a la función que realiza la actualización
    response, status_code = update_file_principal(row_number, tipo,info_usuario,razon_accion)

    return jsonify(response), status_code

# Ruta para el login
@app.route('/login', methods=['POST']) #define la ruta con método POST únicamente
def login():
    # URL del servicio de login
    url_login = 'https://app/login' 
    service2 = service2(url_login)
    print('Paso-.-->')
    credenciales = request.get_json()
    nombre_usuario = credenciales.get('nombreUsuario')
    contrasenia = credenciales.get('contrasenia')
    try:
        out = service2.login(nombre_usuario, contrasenia)
        return jsonify(out), 200
    except Exception as e:
        print(f"Error al iniciar sesión: {e}")
        return '', 500

# Ruta para obtener datos básicos de una persona
@app.route('/obtenerDatosBasicosPersona', methods=['GET'])
def obtener_datos_basicos_persona():
    documento = request.args.get('documento')
    try:
        persona_dto = service.obtener_datos_basicos_persona(documento)
        return jsonify(persona_dto), 200
    except Exception as e:
        print(f"Error al obtener datos básicos de la persona: {e}")
        return '', 500
    
class PersonaService:
    def __init__(self, url_obtener_tipo_vinculacion, url_obtener_tipo_vinculacion_key):
        self.url_obtener_tipo_vinculacion = url_obtener_tipo_vinculacion
        self.url_obtener_tipo_vinculacion_key = url_obtener_tipo_vinculacion_key

    def obtener_datos_basicos_persona(self, documento):
        # Configurar los encabezados personalizados
        headers = {
            'Content-Type': 'application/json',
            'key': self.url_obtener_tipo_vinculacion_key,
            'numeroDocumento': documento
        }

        # Hacer la solicitud GET con los encabezados personalizados
        response = requests.get(self.url_obtener_tipo_vinculacion, headers=headers, verify=False)

        # Verificar si la solicitud fue exitosa
        if response.status_code == 200:
            # Convertir la cadena JSON en un objeto Python
            persona_dto = response.json()
            return persona_dto
        else:
            response.raise_for_status()

# URL del servicio de obtener tipo de vinculación
url_obtener_tipo_vinculacion = 'https://app.serviciocivil.gov.co/obtenerDatosBasicosPersonaTipoVinculacion'
url_obtener_tipo_vinculacion_key = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
service = PersonaService(url_obtener_tipo_vinculacion, url_obtener_tipo_vinculacion_key)
class SideapService2:
    def __init__(self, url_login):
        self.url_login = url_login

    def login(self, nombre_usuario, contrasenia):
        # Convertir la contraseña a SHA-256
        sha256_contrasenia = hashlib.sha256(contrasenia.encode()).hexdigest()

        # Configurar los encabezados personalizados
        headers = {
            'Content-Type': 'application/json'
        }

        # Configurar el cuerpo de la solicitud en formato JSON
        request_body = {
            "nombreUsuario": nombre_usuario,
            "contrasenia": sha256_contrasenia
        }

        # Hacer la solicitud POST con los encabezados y el cuerpo
        response = requests.post(self.url_login, headers=headers, data=json.dumps(request_body), verify=False)

        # Verificar si la solicitud fue exitosa
        if response.status_code == 200:
            # Convertir la cadena JSON en un objeto Python
            out = response.json()
            return out
        else:
            response.raise_for_status()

@app.route('/verificarEditor', methods=['GET'])
def verificar_editor():
    cedula = request.args.get('cedula')
    try:
        usuario = Usuario.query.filter_by(cedula=cedula).first()
        if usuario and usuario.activo:
            return jsonify({'esEditor': True}), 200
        else:
            return jsonify({'esEditor': False}), 200
    except Exception as e:
        print(f"Error al verificar si el usuario es Editor: {e}")
        return '', 500

@app.route('/process-document', methods=['POST'])
def process_document():
    is_cosmos_inserted = False
    index_updated = False
    file_url = None
    is_file_upload= False
    try:
        # Inicializar variables de estado
        
        
        

        # Obtener archivo y metadatos del formulario
        fecha_actual = datetime.now().strftime("%Y-%m-%d")
        file = request.files['file']  # El campo 'file' contiene el archivo PDF o Excel
        file_name = file.filename
        metadata = request.form.to_dict()  # Recibir los demás metadatos como 'titulo', 'descripcion', etc.
        max_row_number = get_max_row_number_ns()
        max_row_number = max_row_number + 1 if max_row_number else 10000
        
        # Añadir campos del formulario a metadata
        metadata.update({
            'titulo': request.form.get('titulo', ''),
            'source': request.form.get('file_name', ''),
            'descripcion': request.form.get('descripcion', ''),
            'tema': request.form.get('tema', ''),
            'subtema': request.form.get('subtema', ''),
            'anio': request.form.get('fecha', ''),
            'usuario_creacion': request.form.get('usuario_creacion', ''),
            'fecha_creacion': fecha_actual,
            'row_number': max_row_number,
            'borrado': False,
            'new_service': True
        })

        # 1. Subir el archivo a Azure Blob Storage
        file_url = upload_to_blob_storage(file, file_name)
        is_file_upload = True
        metadata['url'] = file_url

        # 2. Calcular el tamaño del archivo
        file_size = get_file_size(file_url)
        metadata['file_size'] = file_size

        # 3. Extraer texto con Azure Document Intelligence
        documents = extract_text_from_document(file_url)
        if not documents:
            raise Exception("No se pudo extraer el texto del documento. Verifique si el archivo está protegido.")

        chunk_size = int(os.getenv('CHUNK_SIZE'))
        chunk_overlap = int(os.getenv('CHUNK_OVERLAP'))

        # 4. Hacer chunking del documento
        chunks = chunk_document(documents, chunk_size, chunk_overlap)
        if not chunks:
            raise Exception("Error durante el chunking del documento.")

        # 5. Vectorizar y almacenar en Cosmos DB
        vectorize_and_save_to_cosmos(chunks, metadata)
        is_cosmos_inserted=True

        # 6. Actualizar el índice
        call_index_for_update()
        index_updated = True

        return jsonify({"message": "Proceso completado correctamente."}), 200
    
    except Exception as e:
        logging.error(f"Error procesando el documento: {str(e)}")
        
        # Rollback: si se subió el archivo, eliminarlo
        if is_file_upload:
            rollback_blob(file_name)
        
        # Rollback: si se insertaron entradas en Cosmos DB, eliminarlas
        if is_cosmos_inserted:
            rollback_cosmos(file_url)
        
        # Rollback: si se actualizó el índice, revertir el cambio
        if index_updated:
            rollback_index_update()

        return jsonify({"error": str(e)}), 500

@app.route('/get/')
def get_version():
    # Leer el archivo 'version'
    try:
        with open('version', 'r') as f:
            lines = f.readlines()
            version_info = {
                "version": lines[0].strip(),
                "fecha": lines[1].strip()
            }
            return jsonify(version_info)
    except FileNotFoundError:
        return jsonify({"error": "El archivo 'version' no existe"}), 404


@app.route('/process-documents-bulk', methods=['POST'])
def process_documents_from_local_excel():
    try:
        # Ruta local del archivo Excel en el servidor
        excel_path = "infra_nuevo.xlsx"

        # Verificar si el archivo existe
        if not os.path.exists(excel_path):
            return jsonify({"error": f"El archivo Excel no se encontró en la ruta: {excel_path}"}), 400

        # Leer el archivo Excel
        df = pd.read_excel(excel_path)

        # Validar columnas requeridas en el Excel
        required_columns = ['titulo', 'descripcion', 'tema', 'subtema', 'anio', 'adjunto', 'usuario_creacion']
        if not all(col in df.columns for col in required_columns):
            return jsonify({"error": f"El archivo Excel debe contener las columnas: {', '.join(required_columns)}"}), 400

        # Procesar cada fila como un documento
        results = []
        for index, row in df.iterrows():
            try:
                # Construir los metadatos y obtener la URL o ruta local del archivo
                metadata = row.to_dict()
                file_path_or_url = metadata.pop('adjunto')  # Ruta local o URL del archivo PDF

                # Descargar el archivo si es una URL
                if file_path_or_url.startswith('http://') or file_path_or_url.startswith('https://'):
                    response = requests.get(file_path_or_url, stream=True)
                    if response.status_code != 200:
                        raise Exception(f"No se pudo descargar el archivo desde la URL: {file_path_or_url}. Status: {response.status_code}")

                    # Leer el archivo descargado en memoria
                    file_content = BytesIO(response.content)
                    file_name = os.path.basename(file_path_or_url)
                else:
                    # Verificar si el archivo local existe
                    if not os.path.exists(file_path_or_url):
                        raise Exception(f"El archivo PDF no se encontró en la ruta: {file_path_or_url}")
                    
                    # Leer el archivo local
                    with open(file_path_or_url, 'rb') as f:
                        file_content = BytesIO(f.read())
                    file_name = os.path.basename(file_path_or_url)

                # Crear un objeto FileStorage simulando un archivo cargado
                file = FileStorage(
                    stream=file_content,
                    filename=file_name,
                    content_type='application/pdf'
                )

                # Simular una solicitud POST al endpoint existente
                with app.test_client() as client:
                    response = client.post(
                        '/process-document',
                        data={**metadata, 'file': file},
                        content_type='multipart/form-data'
                    )
                    results.append({
                        "index": index,
                        "titulo": metadata.get('titulo'),
                        "status": response.status_code,
                        "message": response.get_json() if response.status_code != 200 else "Documento procesado correctamente"
                    })
            except Exception as e:
                results.append({
                    "index": index,
                    "titulo": row.get('titulo', 'Desconocido'),
                    "status": 500,
                    "message": f"Error al procesar el documento: {str(e)}"
                })

        return jsonify(results), 200

    except Exception as e:
        logging.error(f"Error en la carga masiva de documentos: {str(e)}")
        return jsonify({"error": f"Error procesando documentos: {str(e)}"}), 500



if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5002)