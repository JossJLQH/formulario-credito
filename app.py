import os
import uuid
from flask import Flask, render_template, request, send_from_directory, redirect
from werkzeug.utils import secure_filename
import sqlite3
from datetime import datetime
import pytz

app = Flask(__name__)

# Configuración de la carpeta de uploads
CARPETA_UPLOADS = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['UPLOAD_FOLDER'] = CARPETA_UPLOADS

if not os.path.exists(CARPETA_UPLOADS):
    os.makedirs(CARPETA_UPLOADS)

EXTENSIONES_PERMITIDAS = {'png', 'jpg', 'jpeg', 'pdf'}

def archivo_permitido(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in EXTENSIONES_PERMITIDAS

def guardar_archivo(archivo_form):
    if archivo_form and archivo_form.filename != '' and archivo_permitido(archivo_form.filename):
        nombre_original = secure_filename(archivo_form.filename)
        nombre_unico = f"{uuid.uuid4().hex[:8]}_{nombre_original}"
        ruta_completa = os.path.join(app.config['UPLOAD_FOLDER'], nombre_unico)
        archivo_form.save(ruta_completa)
        return nombre_unico
    return None

# Función para inicializar la base de datos con los nuevos campos
def init_db():
    conexion = sqlite3.connect('creditos.db')
    cursor = conexion.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS solicitudes_credito (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            primer_nombre TEXT NOT NULL,
            segundo_nombre TEXT,
            apellido_paterno TEXT NOT NULL,
            apellido_materno TEXT,
            fecha_nacimiento TEXT NOT NULL,
            curp TEXT UNIQUE NOT NULL,
            telefono TEXT NOT NULL,
            email TEXT NOT NULL,
            monto_solicitado REAL NOT NULL,
            ocupacion TEXT NOT NULL,
            ingreso_mensual REAL NOT NULL,
            foto_ine_frente TEXT,
            foto_ine_reverso TEXT,
            foto_comprobante_domicilio TEXT,
            fecha_registro TEXT NOT NULL,
            estatus TEXT DEFAULT 'Pendiente'
        )
    ''')
    conexion.commit()
    conexion.close()

# Ejecutamos la inicialización al arrancar
init_db()

# ==========================================
# RUTAS DEL CLIENTE (FORMULARIO)
# ==========================================

@app.route('/')
def formulario():
    return render_template('index.html')

@app.route('/guardar', methods=['POST'])
def guardar_solicitud():
    primer_nombre = request.form['primer_nombre']
    segundo_nombre = request.form.get('segundo_nombre', '')
    apellido_paterno = request.form['apellido_paterno']
    apellido_materno = request.form.get('apellido_materno', '')
    
    fecha_nacimiento = request.form['fecha_nacimiento']
    curp = request.form['curp'].upper().strip()
    telefono = request.form['telefono']
    email = request.form['email']
    monto_solicitado = request.form['monto_solicitado']
    ocupacion = request.form['ocupacion']
    ingreso_mensual = request.form['ingreso_mensual']

    file_ine_frente = request.files.get('ine_frente')
    file_ine_reverso = request.files.get('ine_reverso')
    file_comprobante = request.files.get('comprobante_domicilio')

    nombre_ine_frente = guardar_archivo(file_ine_frente)
    nombre_ine_reverso = guardar_archivo(file_ine_reverso)
    nombre_comprobante = guardar_archivo(file_comprobante)

    # Obtenemos fecha y hora exacta del Centro de México
    zona_mexico = pytz.timezone('America/Mexico_City')
    fecha_hora_mexico = datetime.now(zona_mexico).strftime('%Y-%m-%d %H:%M:%S')

    try:
        conexion = sqlite3.connect('creditos.db')
        cursor = conexion.cursor()

        cursor.execute('''
            INSERT INTO solicitudes_credito 
            (primer_nombre, segundo_nombre, apellido_paterno, apellido_materno, 
             fecha_nacimiento, curp, telefono, email, monto_solicitado, ocupacion, ingreso_mensual,
             foto_ine_frente, foto_ine_reverso, foto_comprobante_domicilio, fecha_registro)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            primer_nombre, segundo_nombre, apellido_paterno, apellido_materno,
            fecha_nacimiento, curp, telefono, email, 
            monto_solicitado, ocupacion, ingreso_mensual,
            nombre_ine_frente, nombre_ine_reverso, nombre_comprobante, fecha_hora_mexico
        ))

        conexion.commit()
        id_registro = cursor.lastrowid
        conexion.close()

        return f'''
            <div style="font-family: Arial, sans-serif; padding: 40px; text-align: center; max-width: 600px; margin: auto;">
                <h1 style="color: #2b6cb0;">¡Solicitud Registrada con Éxito! 🎉</h1>
                <p>Se ha guardado tu solicitud con el <strong>ID No. {id_registro}</strong>.</p>
                <br>
                <a href="/" style="background: #2b6cb0; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">Registrar otra solicitud</a>
            </div>
        '''

    except sqlite3.IntegrityError:
        return f'''
            <div style="font-family: Arial, sans-serif; padding: 40px; text-align: center;">
                <h1 style="color: #e53e3e;"> Error al Registrar</h1>
                <p>La CURP <strong>{curp}</strong> ya se encuentra registrada en el sistema.</p>
                <br>
                <a href="/" style="background: #e53e3e; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">Volver a intentar</a>
            </div>
        '''

# ==========================================
# RUTAS DE ADMINISTRACIÓN
# ==========================================

# 1. Ruta para ver el panel administrativo con la tabla y estatus
@app.route('/admin')
def panel_admin():
    conexion = sqlite3.connect('creditos.db')
    cursor = conexion.cursor()
    cursor.execute('''
        SELECT id, primer_nombre, segundo_nombre, apellido_paterno, apellido_materno, 
               curp, telefono, email, monto_solicitado, 
               foto_ine_frente, foto_ine_reverso, foto_comprobante_domicilio, 
               fecha_registro, COALESCE(estatus, 'Pendiente') AS estatus
        FROM solicitudes_credito
        ORDER BY id DESC
    ''')
    solicitudes = cursor.fetchall()
    conexion.close()
    
    return render_template('admin.html', solicitudes=solicitudes)

# 2. Ruta para cambiar el estatus de la solicitud (Aprobada / Rechazada / Pendiente)
@app.route('/cambiar_estatus/<int:id_solicitud>', methods=['POST'])
def cambiar_estatus(id_solicitud):
    nuevo_estatus = request.form.get('nuevo_estatus')
    
    conexion = sqlite3.connect('creditos.db')
    cursor = conexion.cursor()
    cursor.execute('''
        UPDATE solicitudes_credito 
        SET estatus = ? 
        WHERE id = ?
    ''', (nuevo_estatus, id_solicitud))
    
    conexion.commit()
    conexion.close()
    
    return redirect('/admin')

# 3. Ruta para abrir y ver los archivos guardados en la carpeta 'uploads'
@app.route('/uploads/<path:filename>')
def ver_documento(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# 4. Ruta para eliminar una solicitud específica por su ID
@app.route('/eliminar_solicitud/<int:id_solicitud>', methods=['POST'])
def eliminar_solicitud(id_solicitud):
    conexion = sqlite3.connect('creditos.db')
    cursor = conexion.cursor()
    
    cursor.execute('''
        SELECT foto_ine_frente, foto_ine_reverso, foto_comprobante_domicilio 
        FROM solicitudes_credito WHERE id = ?
    ''', (id_solicitud,))
    archivos = cursor.fetchone()
    
    if archivos:
        for nombre_archivo in archivos:
            if nombre_archivo:
                ruta_archivo = os.path.join(app.config['UPLOAD_FOLDER'], nombre_archivo)
                if os.path.exists(ruta_archivo):
                    os.remove(ruta_archivo)
    
    cursor.execute('DELETE FROM solicitudes_credito WHERE id = ?', (id_solicitud,))
    conexion.commit()
    conexion.close()
    
    return redirect('/admin')

# 5. Ruta para REINICIAR por completo la BD
@app.route('/resetear_base_datos', methods=['POST'])
def resetear_base_datos():
    conexion = sqlite3.connect('creditos.db')
    cursor = conexion.cursor()
    
    cursor.execute('DELETE FROM solicitudes_credito;')
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='solicitudes_credito';")
    
    conexion.commit()
    conexion.close()
    
    for archivo in os.listdir(app.config['UPLOAD_FOLDER']):
        ruta_completa = os.path.join(app.config['UPLOAD_FOLDER'], archivo)
        if os.path.isfile(ruta_completa):
            os.remove(ruta_completa)
            
    return redirect('/admin')


if __name__ == '__main__':
    print("Servidor corriendo en http://127.0.0.1:5000")
    print("Panel de administración en http://127.0.0.1:5000/admin")
    app.run(debug=True)