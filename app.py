import os
import uuid
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import sqlite3

app = Flask(__name__)

# Configuración de la carpeta donde se guardarán los documentos subidos
CARPETA_UPLOADS = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['UPLOAD_FOLDER'] = CARPETA_UPLOADS

# Crear la carpeta 'uploads' si aún no existe en el proyecto
if not os.path.exists(CARPETA_UPLOADS):
    os.makedirs(CARPETA_UPLOADS)

# Extensiones de archivo permitidas por seguridad
EXTENSIONES_PERMITIDAS = {'png', 'jpg', 'jpeg', 'pdf'}

def archivo_permitido(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in EXTENSIONES_PERMITIDAS


def guardar_archivo(archivo_form):
    """Función auxilar para validar, nombrar de forma única y guardar el archivo"""
    if archivo_form and archivo_form.filename != '' and archivo_permitido(archivo_form.filename):
        nombre_original = secure_filename(archivo_form.filename)
        extension = nombre_original.rsplit('.', 1)[1].lower()
        
        # Generar un nombre único (ejemplo: ine_frente_a1b2c3d4.jpg)
        nombre_unico = f"{uuid.uuid4().hex[:8]}_{nombre_original}"
        ruta_completa = os.path.join(app.config['UPLOAD_FOLDER'], nombre_unico)
        
        # Guardar el archivo físicamente en la carpeta 'uploads'
        archivo_form.save(ruta_completa)
        return nombre_unico
    return None


@app.route('/')
def formulario():
    return render_template('index.html')


@app.route('/guardar', methods=['POST'])
def guardar_solicitud():
    # 1. Recibir datos de texto del formulario
    nombre = request.form['nombre']
    apellidos = request.form['apellidos']
    fecha_nacimiento = request.form['fecha_nacimiento']
    curp = request.form['curp']
    telefono = request.form['telefono']
    email = request.form['email']
    monto_solicitado = request.form['monto_solicitado']
    ocupacion = request.form['ocupacion']
    ingreso_mensual = request.form['ingreso_mensual']

    # 2. Recibir los archivos de imagen / PDF
    file_ine_frente = request.files.get('ine_frente')
    file_ine_reverso = request.files.get('ine_reverso')
    file_comprobante = request.files.get('comprobante_domicilio')

    # 3. Guardar las fotos en la carpeta 'uploads' y obtener los nombres únicos
    nombre_ine_frente = guardar_archivo(file_ine_frente)
    nombre_ine_reverso = guardar_archivo(file_ine_reverso)
    nombre_comprobante = guardar_archivo(file_comprobante)

    # 4. Guardar todo en la Base de Datos SQLite
    try:
        conexion = sqlite3.connect('creditos.db')
        cursor = conexion.cursor()

        cursor.execute('''
            INSERT INTO solicitudes_credito 
            (nombre, apellidos, fecha_nacimiento, curp, telefono, email, monto_solicitado, ocupacion, ingreso_mensual,
             foto_ine_frente, foto_ine_reverso, foto_comprobante_domicilio)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            nombre, apellidos, fecha_nacimiento, curp, telefono, email, 
            monto_solicitado, ocupacion, ingreso_mensual,
            nombre_ine_frente, nombre_ine_reverso, nombre_comprobante
        ))

        conexion.commit()
        id_registro = cursor.lastrowid
        conexion.close()

        return f'''
            <div style="font-family: Arial, sans-serif; padding: 40px; text-align: center; max-width: 600px; margin: auto;">
                <h1 style="color: #2b6cb0;">¡Solicitud Completa Guardada! 🎉</h1>
                <p>Se ha registrado la solicitud con los documentos adjuntos en la base de datos.</p>
                <p style="background: #edf2f7; padding: 12px; border-radius: 6px;"><strong>ID Solicitud:</strong> #{id_registro}</p>
                <p><strong>Cliente:</strong> {nombre} {apellidos}</p>
                <p><strong>Documentos subidos:</strong></p>
                <ul style="text-align: left; display: inline-block;">
                    <li>INE Frente: {nombre_ine_frente}</li>
                    <li>INE Reverso: {nombre_ine_reverso}</li>
                    <li>Comprobante: {nombre_comprobante}</li>
                </ul>
                <br><br>
                <a href="/" style="background: #2b6cb0; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">Registrar otra solicitud</a>
            </div>
        '''

    except sqlite3.IntegrityError:
        return f'''
            <div style="font-family: Arial, sans-serif; padding: 40px; text-align: center;">
                <h1 style="color: #e53e3e;"> Error al Registrar</h1>
                <p>La CURP <strong>{curp}</strong> ya se encuentra registrada en el sistema.</p>
                <br><br>
                <a href="/" style="background: #e53e3e; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">Volver a intentar</a>
            </div>
        '''


if __name__ == '__main__':
    print("Servidor listo en http://127.0.0.1:5000")
    app.run(debug=True)