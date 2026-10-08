import os
import uuid
import sqlite3
import pytz
import random
import resend  # <-- Nueva librería
from datetime import datetime, timedelta
from flask import Flask, render_template, request, send_from_directory, redirect, url_for, session, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)
# Clave secreta requerida para manejar sesiones y mensajes flash en Flask
app.secret_key = 'clave_secreta_super_segura_para_desarrollo'

# ==========================================
# CONFIGURACIONES
# ==========================================
CARPETA_UPLOADS = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['UPLOAD_FOLDER'] = CARPETA_UPLOADS

if not os.path.exists(CARPETA_UPLOADS):
    os.makedirs(CARPETA_UPLOADS)

EXTENSIONES_PERMITIDAS = {'png', 'jpg', 'jpeg', 'pdf'}

# ==========================================
# FUNCIONES AUXILIARES
# ==========================================
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

# ==========================================
# BASE DE DATOS
# ==========================================
def init_db():
    conexion = sqlite3.connect('creditos.db', timeout=10)
    cursor = conexion.cursor()
    
    # Tabla principal de solicitudes
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
    
    # Tabla para verificaciones OTP de correo
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS verificaciones_email (
            email TEXT PRIMARY KEY,
            codigo TEXT NOT NULL,
            expiracion TEXT NOT NULL,
            verificado INTEGER DEFAULT 0
        )
    ''')
    conexion.commit()
    conexion.close()

init_db()

# ==========================================
# FLUJO PASO A PASO: CORREO OTP Y FORMULARIO
# ==========================================

# 1. Página Inicial: Pide el correo
@app.route('/')
def inicio():
    if session.get('email_verificado'):
        return redirect(url_for('mostrar_formulario'))
    return render_template('solicitar_email.html')

# 2. Procesa el correo, genera el OTP y redirige a la pantalla de verificación
@app.route('/enviar-otp', methods=['POST'])
def enviar_otp():
    email = request.form.get('email', '').strip().lower()
    
    if not email:
        flash('Por favor ingresa un correo electrónico válido.', 'error')
        return redirect(url_for('inicio'))
    
    # Genera el código y calcula expiración
    codigo, expiracion = generar_y_enviar_otp(email)
    
    # Guarda o actualiza el código OTP en la base de datos
    conexion = sqlite3.connect('creditos.db', timeout=10)
    cursor = conexion.cursor()
    cursor.execute('''
        INSERT INTO verificaciones_email (email, codigo, expiracion, verificado)
        VALUES (?, ?, ?, 0)
        ON CONFLICT(email) DO UPDATE SET
            codigo = excluded.codigo,
            expiracion = excluded.expiracion,
            verificado = 0
    ''', (email, codigo, expiracion))
    
    conexion.commit()
    conexion.close()
    
    # Guarda el correo en la sesión temporal para el siguiente paso
    session['email_pendiente'] = email
    
    return render_template('verificar_otp.html', email=email)

# 3. Vista y validación del OTP
# ==========================================
# CONFIGURACIÓN DE CORREO (RESEND API)
# ==========================================
resend.api_key = os.environ.get('RESEND_API_KEY')

def generar_y_enviar_otp(destinatario):
    codigo = str(random.randint(100000, 999999))
    expiracion = (datetime.now() + timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M:%S')

    print(f'\n==================================================')
    print(f'*** [DEV MODE] CÓDIGO OTP PARA {destinatario}: {codigo} ***')
    print(f'==================================================\n')

    try:
        # Nota: 'onboarding@resend.dev' es el remitente de pruebas gratuito que provee Resend
        respuesta = resend.Emails.send({
            "from": "onboarding@resend.dev",
            "to": destinatario,
            "subject": "Código de Verificación - Formulario de Crédito",
            "html": f"""
                <div style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
                    <h2>Código de Verificación</h2>
                    <p>Hola,</p>
                    <p>Tu código para continuar con tu solicitud de crédito es:</p>
                    <h1 style="color: #2b6cb0; letter-spacing: 2px;">{codigo}</h1>
                    <p>Este código es válido durante 10 minutos.</p>
                </div>
            """
        })
        print(f"Correo enviado exitosamente vía Resend. ID: {respuesta}")
    except Exception as e:
        print(f'Nota: No se pudo enviar el correo vía Resend: {e}')
    
    return codigo, expiracion

# 4. Formulario Principal de Crédito (Protegido)
@app.route('/formulario')
def mostrar_formulario():
    if not session.get('email_verificado'):
        flash('Debes verificar tu correo antes de llenar la solicitud.', 'error')
        return redirect(url_for('inicio'))

    email_usuario = session.get('email_confirmado', '')
    return render_template('index.html', email_prellenado=email_usuario)

# 5. Guardar la solicitud completa
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

    zona_mexico = pytz.timezone('America/Mexico_City')
    fecha_hora_mexico = datetime.now(zona_mexico).strftime('%Y-%m-%d %H:%M:%S')

    try:
        conexion = sqlite3.connect('creditos.db', timeout=10)
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

        session.pop('email_verificado', None)
        session.pop('email_confirmado', None)

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
                <h1 style="color: #e53e3e;">Error al Registrar</h1>
                <p>La CURP <strong>{curp}</strong> ya se encuentra registrada en el sistema.</p>
                <br>
                <a href="/formulario" style="background: #e53e3e; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">Volver a intentar</a>
            </div>
        '''

# ==========================================
# RUTAS DE ADMINISTRACIÓN
# ==========================================

@app.route('/admin')
def panel_admin():
    conexion = sqlite3.connect('creditos.db', timeout=10)
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

@app.route('/cambiar_estatus/<int:id_solicitud>', methods=['POST'])
def cambiar_estatus(id_solicitud):
    nuevo_estatus = request.form.get('nuevo_estatus')
    
    conexion = sqlite3.connect('creditos.db', timeout=10)
    cursor = conexion.cursor()
    cursor.execute('''
        UPDATE solicitudes_credito 
        SET estatus = ? 
        WHERE id = ?
    ''', (nuevo_estatus, id_solicitud))
    
    conexion.commit()
    conexion.close()
    
    return redirect('/admin')

@app.route('/uploads/<path:filename>')
def ver_documento(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/eliminar_solicitud/<int:id_solicitud>', methods=['POST'])
def eliminar_solicitud(id_solicitud):
    conexion = sqlite3.connect('creditos.db', timeout=10)
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

@app.route('/resetear_base_datos', methods=['POST'])
def resetear_base_datos():
    conexion = sqlite3.connect('creditos.db', timeout=10)
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
    print("\n--------------------------------------------------")
    print("Servidor corriendo en: http://127.0.0.1:5000")
    print("Panel de administración en: http://127.0.0.1:5000/admin")
    print("--------------------------------------------------\n")
    app.run(debug=True)