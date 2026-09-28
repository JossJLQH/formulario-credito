import sqlite3

conexion = sqlite3.connect('creditos.db')
cursor = conexion.cursor()

# Agregamos las nuevas columnas para los documentos
try:
    cursor.execute("ALTER TABLE solicitudes_credito ADD COLUMN foto_ine_frente TEXT;")
    cursor.execute("ALTER TABLE solicitudes_credito ADD COLUMN foto_ine_reverso TEXT;")
    cursor.execute("ALTER TABLE solicitudes_credito ADD COLUMN foto_comprobante_domicilio TEXT;")
    conexion.commit()
    print("¡Base de datos actualizada con las columnas para documentos!")
except sqlite3.OperationalError:
    print("Las columnas ya existían en la base de datos.")

conexion.close()